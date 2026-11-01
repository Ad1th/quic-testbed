#!/usr/bin/env python3
"""Run curl --http2 / --http3-only against nginx inside the testbed and append rows to a CSV.
Must be started under scripts/testbed.sh (needs the client/server namespaces).
connect_s = curl time_connect (TCP or QUIC socket connect), handshake_s = time_appconnect (cumulative,
i.e. TLS/QUIC handshake done), ttfb_s = time_starttransfer, total_s = time_total. All cumulative from request start."""
import argparse, csv, os, subprocess, sys, time, uuid
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
CURL = f"{HOME}/.local/bin/curl"
CERT = f"{HOME}/srv/certs/server.crt"
COLS = ["run_id", "timestamp", "protocol", "profile", "rtt_ms", "loss_pct", "iteration",
        "connect_s", "handshake_s", "ttfb_s", "total_s", "throughput_Bps", "http_version"]
# nominal (mean RTT ms, mean loss %) for the mobile profiles so they fit the same columns
MOBILE = {"india_4g": (50, 1.0), "india_5g": (48, 0.3), "india_4g_congested": (120, 3.0)}
PROTO = {"h2": ["--http2"], "h3": ["--http3-only"]}
FMT = "%{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total} %{speed_download} %{http_version} %{http_code}"


def netem(*args):
    subprocess.run(["bash", "-c", f'source "{HERE}/netem.sh"; "$@"', "_", *args], check=True)


def fetch(proto, fname, max_time):
    cmd = ["ip", "netns", "exec", "client", CURL, "-s", "-o", "/dev/null", "--cacert", CERT,
           "--max-time", str(max_time), *PROTO[proto], "-w", FMT, f"https://10.0.0.2/{fname}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    f = r.stdout.split()
    if r.returncode != 0 or len(f) != 7 or f[6] != "200":
        return None
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "results.csv"))
    ap.add_argument("--file", default="1MB.bin")
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--rtts", default="20,50,100,150,200,300")
    ap.add_argument("--losses", default="0,0.5,1,2,3,5")
    ap.add_argument("--profiles", default="static,india_4g,india_5g,india_4g_congested")
    ap.add_argument("--max-time", type=int, default=40)
    ap.add_argument("--shard", default="0/1", help="k/n: run only conditions with index %% n == k")
    ap.add_argument("--run-id", default=None)
    a = ap.parse_args()

    conds = []
    for p in a.profiles.split(","):
        if p == "static":
            conds += [("static", float(r), float(l)) for r in a.rtts.split(",") for l in a.losses.split(",")]
        else:
            conds.append((p, *MOBILE[p]))
    k, n = map(int, a.shard.split("/"))
    conds = [c for i, c in enumerate(conds) if i % n == k]
    run_id = a.run_id or datetime.now().strftime("%Y%m%dT%H%M%S-") + uuid.uuid4().hex[:6]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    new = not os.path.exists(a.out) or os.path.getsize(a.out) == 0
    fails = 0
    with open(a.out, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLS)
        for ci, (prof, rtt, loss) in enumerate(conds, 1):
            if prof == "static":
                netem("netem_static", f"{rtt:g}", f"{loss:g}")
            else:
                netem(f"netem_{prof}")
            t0 = time.time()
            for it in range(1, a.iterations + 1):
                order = ["h2", "h3"] if it % 2 else ["h3", "h2"]  # alternate to cancel drift
                for proto in order:
                    f = fetch(proto, a.file, a.max_time)
                    ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                    if f is None:
                        fails += 1
                        w.writerow([run_id, ts, proto, prof, f"{rtt:g}", f"{loss:g}", it, "", "", "", "", "", ""])
                    else:
                        w.writerow([run_id, ts, proto, prof, f"{rtt:g}", f"{loss:g}", it,
                                    f[0], f[1], f[2], f[3], f"{float(f[4]):.0f}", f[5]])
                    fh.flush()
            print(f"[{ci}/{len(conds)}] {prof} rtt={rtt:g} loss={loss:g}  {time.time()-t0:.0f}s  fails so far={fails}", flush=True)
    netem("netem_clear")
    print(f"done run_id={run_id} out={a.out} failures={fails}")


if __name__ == "__main__":
    sys.exit(main())
