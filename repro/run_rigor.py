#!/usr/bin/env python3
"""Controlled re-run of the h2-vs-h3 comparison (run inside the repro/ Docker image, --privileged, repo mounted at /work).

Differences from scripts/run_tests.py, each addressing a confound raised in review:
  * strictly serial: one transfer at a time, no shards
  * --offloads on|off: TSO/GSO/GRO on both veth ends. With offloads on, netem drops whole TCP GSO super-segments
    (one "loss" can remove several MSS) while QUIC datagrams are dropped one at a time, so the same netem loss %
    is not the same loss process for the two protocols
  * CPU pinning (client, nginx, quic-go on separate vCPUs) and per-transfer CPU time of client and server
  * per-transfer kernel counters: netem qdisc sent/dropped on the data (server egress) and ACK (client egress) sides,
    server TCP RetransSegs, client UDP RcvbufErrors
  * a third HTTP/3 sender: quic-go (h3qg), in addition to nginx h2 / nginx h3
"""
import argparse, csv, os, re, resource, subprocess, sys, time, uuid
from datetime import datetime, timezone

W = os.environ.get("WORK", "/work")
CURL, CERT = "/opt/h3/bin/curl", "/srv/certs/server.crt"
NGINX = "/opt/h3/nginx/sbin/nginx"
QG = f"{W}/repro/quicgo-server/quicgo-server"
QC = "/opt/h3/bin/quiche-server"  # only in the quic-testbed:quiche image (repro/Dockerfile.quiche)
CPU = {"runner": "0", "client": "5", "nginx": "2", "quicgo": "3", "quiche": "4"}
URL = {"h2": "https://10.0.0.2/{f}", "h3": "https://10.0.0.2/{f}", "h3qg": "https://10.0.0.2:8443/{f}",
       "h3qc": "https://10.0.0.2:9443/{f}"}
FLAG = {"h2": "--http2", "h3": "--http3-only", "h3qg": "--http3-only", "h3qc": "--http3-only"}
FMT = "%{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total} %{speed_download} %{http_version} %{http_code}"
COLS = ["run_id", "timestamp", "topology", "offloads", "rcvbuf", "quicgo_gso", "protocol", "rtt_ms", "loss_pct", "rate", "iteration", "ok", "connect_s",
        "handshake_s", "ttfb_s", "total_s", "throughput_Bps", "http_version", "cpu_client_s", "cpu_server_s",
        "data_sent_pkts", "data_dropped", "ack_sent_pkts", "ack_dropped", "tcp_retrans_segs", "udp_rcvbuf_errors", "exit_hang"]


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, **kw).stdout


def ns(n, cmd):
    return sh(f"ip netns exec {n} {cmd}")


TOPO = "direct"
# where netem lives: direct = on the endpoints' own veths (original testbed); bridge = on a separate router netns that
# L2-bridges client and server. Linux TCP always builds GSO skbs (segmented only after the qdisc), and quic-go uses UDP
# GSO, so netem on a sender's own device drops multi-packet skbs whatever ethtool says. In bridge mode packets are
# segmented when they leave the sender (endpoint offloads off), GRO is off on the router ports, and netem drops wire packets.
NETEM_DEV = {"direct": (("server", "veth-s"), ("client", "veth-c")), "bridge": (("router", "veth-rc"), ("router", "veth-rs"))}


def setup_bridge():
    for n in ("client", "server", "router"):
        subprocess.run(f"ip netns del {n}", shell=True, capture_output=True)
        sh(f"ip netns add {n}")
    sh("ip link add veth-c type veth peer name veth-rc && ip link add veth-s type veth peer name veth-rs")
    sh("ip link set veth-c netns client && ip link set veth-s netns server")
    sh("ip link set veth-rc netns router && ip link set veth-rs netns router")
    ns("client", "ip addr add 10.0.0.1/24 dev veth-c")
    ns("server", "ip addr add 10.0.0.2/24 dev veth-s")
    ns("router", "ip link add br0 type bridge")
    for d in ("veth-rc", "veth-rs"):
        ns("router", f"ip link set {d} master br0")
    for n, devs in (("client", ["lo", "veth-c"]), ("server", ["lo", "veth-s"]), ("router", ["lo", "veth-rc", "veth-rs", "br0"])):
        for d in devs:
            ns(n, f"ip link set {d} up")


def setup(offloads):
    if TOPO == "bridge":
        setup_bridge()
        for d in ("veth-rc", "veth-rs"):
            ns("router", f"ethtool -K {d} gro off")
    else:
        sh(f"bash {W}/scripts/setup_netns.sh")
    for n, d in (("client", "veth-c"), ("server", "veth-s")):
        v = "on" if offloads == "on" else "off"
        ns(n, f"ethtool -K {d} tso {v} gso {v} gro {v}")
        subprocess.run(f"ip netns exec {n} ethtool -K {d} tx-udp-segmentation {v}", shell=True, capture_output=True)
    print("topology", TOPO, end=" | ")
    print("offloads", offloads, ns("server", "ethtool -k veth-s").count(": on"), "features on (server veth)",
          "| tcp cc:", ns("server", "sysctl -n net.ipv4.tcp_congestion_control").strip(), flush=True)


def start_servers(qlog, quicgo_gso="on"):
    conf = open(f"{W}/conf/nginx.conf").read().replace("@PROJECT@", W).replace("@HOME@", "")
    os.makedirs(f"{W}/logs", exist_ok=True)
    open(f"{W}/logs/nginx.rigor.conf", "w").write(conf)
    procs = [subprocess.Popen(f"ip netns exec server taskset -c {CPU['nginx']} {NGINX} -p /opt/h3/nginx "
                              f"-c {W}/logs/nginx.rigor.conf -g 'pid {W}/logs/nginx-rigor.pid;'", shell=True)]
    env = dict(os.environ, **({"QLOGDIR": f"{qlog}/server_quicgo"} if qlog else {}))
    if quicgo_gso == "off":  # quic-go batches datagrams with UDP GSO; netem then drops whole batches (like TCP TSO)
        env["QUIC_GO_DISABLE_GSO"] = "true"
    if qlog:
        os.makedirs(f"{qlog}/server_quicgo", exist_ok=True)
    procs.append(subprocess.Popen(f"ip netns exec server taskset -c {CPU['quicgo']} {QG} -addr 10.0.0.2:8443",
                                  shell=True, env=env, stderr=subprocess.DEVNULL))
    if os.path.exists(QC):
        procs.append(subprocess.Popen(f"ip netns exec server taskset -c {CPU['quiche']} {QC} --listen 10.0.0.2:9443 "
                                      f"--root /srv/content --cert /srv/certs/server.crt --key /srv/certs/server.key "
                                      f"--no-retry", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL))
    time.sleep(2)
    return procs


def pid_of(pattern):
    out = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split()
    return int(out[-1]) if out else None


def cpu_of(pid):
    if not pid:
        return 0.0
    f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
    return (int(f[11]) + int(f[12])) / os.sysconf("SC_CLK_TCK")


QD = re.compile(r"Sent \d+ bytes (\d+) pkt \(dropped (\d+)")


def qdisc(n, dev):
    m = QD.search(ns(n, f"tc -s qdisc show dev {dev}"))
    return (int(m[1]), int(m[2])) if m else (0, 0)


def snmp(n, proto, field):
    lines = [l.split() for l in ns(n, "cat /proc/net/snmp").splitlines() if l.startswith(proto + ":")]
    return int(lines[1][lines[0].index(field)])


def counters():
    (dn, dd), (an, ad) = NETEM_DEV[TOPO]
    return (*qdisc(dn, dd), *qdisc(an, ad),
            snmp("server", "Tcp", "RetransSegs"), snmp("client", "Udp", "RcvbufErrors"))


def netem(rtt, loss, rate):
    d = f"{rtt / 2:g}ms"
    for n, dev in NETEM_DEV[TOPO]:
        subprocess.run(f"ip netns exec {n} tc qdisc del dev {dev} root", shell=True, capture_output=True)
        a = f"delay {d} rate {rate}" + (f" loss {loss:g}%" if loss > 0 else "")
        ns(n, f"tc qdisc add dev {dev} root netem {a}")


def fetch(proto, fname, max_time, qlog):
    """Returns (fields or None, exit_hang). guard against a fetch that never exits: such a process is killed after max_time+5 s and its already-printed measurement is kept."""
    env = dict(os.environ)
    if qlog and proto != "h2":
        env["QLOGDIR"] = f"{qlog}/client_{proto}"
        os.makedirs(env["QLOGDIR"], exist_ok=True)
    cmd = (f"exec taskset -c {CPU['client']} ip netns exec client {CURL} -s -o /dev/null --cacert {CERT} "
           f"--max-time {max_time} {FLAG[proto]} -w '{FMT}' {URL[proto].format(f=fname)}")
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                         env=env, start_new_session=True)
    hang = 0
    try:
        out, _ = p.communicate(timeout=max_time + 5)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, 9)
        out, _ = p.communicate()
        rc, hang = 0, 1
    f = (out or "").split()
    return (f if rc == 0 and len(f) == 7 and f[6] == "200" else None), hang


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--offloads", choices=["on", "off"], required=True)
    ap.add_argument("--protocols", default="h2,h3,h3qg")
    ap.add_argument("--file", default="1MB.bin")
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--rtts", default="50,100")
    ap.add_argument("--losses", default="0,1,2,5")
    ap.add_argument("--rate", default="1gbit")
    ap.add_argument("--max-time", type=int, default=40)
    ap.add_argument("--rcvbuf", type=int, default=0, help="if >0, set net.core.rmem_default/max (needs --network host); "
                    "restored to 212992 on exit")
    ap.add_argument("--topology", choices=["direct", "bridge"], default="direct")
    ap.add_argument("--quicgo-gso", choices=["on", "off"], default="on")
    ap.add_argument("--qlog", default="", help="directory for client (and quic-go server) qlogs")
    a = ap.parse_args()
    global TOPO
    TOPO = a.topology
    os.sched_setaffinity(0, {int(CPU["runner"])})
    if a.qlog:
        os.makedirs(a.qlog, exist_ok=True)
    if a.rcvbuf:
        sh(f"sysctl -qw net.core.rmem_default={a.rcvbuf} net.core.rmem_max={2 * a.rcvbuf}")
    setup(a.offloads)
    procs = start_servers(a.qlog, a.quicgo_gso)
    protos = a.protocols.split(",")
    for proto in protos:  # preflight: every sender must serve the object once on a clean link before measuring
        netem(10, 0, a.rate)
        f, _ = fetch(proto, a.file, 15, "")
        if f is None or (proto != "h2" and f[5] != "3"):
            for p_ in procs:
                p_.terminate()
            if a.rcvbuf:
                sh("sysctl -qw net.core.rmem_default=212992 net.core.rmem_max=212992")
            sys.exit(f"preflight failed for {proto}: {f}")
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:6]
    new = not os.path.exists(a.out) or os.path.getsize(a.out) == 0
    try:
        with open(a.out, "a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(COLS)
            conds = [(float(r), float(l)) for r in a.rtts.split(",") for l in a.losses.split(",")]
            for ci, (rtt, loss) in enumerate(conds, 1):
                netem(rtt, loss, a.rate)
                t0, fails = time.time(), 0
                for it in range(1, a.iterations + 1):
                    k = it % len(protos)
                    for proto in protos[k:] + protos[:k]:  # rotate order each iteration to cancel drift
                        spid = pid_of("nginx: worker") if proto in ("h2", "h3") else pid_of(QG if proto == "h3qg" else QC)
                        c0, s0, ru0 = counters(), cpu_of(spid), resource.getrusage(resource.RUSAGE_CHILDREN)
                        f, hang = fetch(proto, a.file, a.max_time, a.qlog)
                        ru1, s1, c1 = resource.getrusage(resource.RUSAGE_CHILDREN), cpu_of(spid), counters()
                        dc = [y - x for x, y in zip(c0, c1)]
                        cc = (ru1.ru_utime + ru1.ru_stime) - (ru0.ru_utime + ru0.ru_stime)
                        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                        base = [run_id, ts, a.topology, a.offloads, a.rcvbuf or 212992, a.quicgo_gso, proto, f"{rtt:g}", f"{loss:g}", a.rate, it]
                        tail = [f"{cc:.3f}", f"{s1 - s0:.3f}", *dc, hang]
                        if f is None:
                            fails += 1
                            w.writerow(base + [0, "", "", "", "", "", ""] + tail)
                        else:
                            w.writerow(base + [1, *f[:4], f"{float(f[4]):.0f}", f[5]] + tail)
                        fh.flush()
                print(f"[{ci}/{len(conds)}] offloads={a.offloads} rtt={rtt:g} loss={loss:g} {time.time() - t0:.0f}s "
                      f"fails={fails}", flush=True)
    finally:
        for p in procs:
            p.terminate()
        subprocess.run("pkill -f 'nginx: ' ; pkill -f quicgo-server; pkill -f quiche-server", shell=True)
        if a.rcvbuf:
            sh("sysctl -qw net.core.rmem_default=212992 net.core.rmem_max=212992")
    print("done", run_id, a.out)


if __name__ == "__main__":
    sys.exit(main())
