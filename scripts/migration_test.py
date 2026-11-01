#!/usr/bin/env python3
"""Phase 9 (optional): client IP change mid-transfer. At --at seconds, replace the client's address 10.0.0.1 with
10.0.0.3 on veth-c, then see whether the download completes. h2 (TCP) is bound to the old 4-tuple; h3 can survive only if
the client stack keeps sending (QUIC connection IDs + server path validation). Result is whatever the stacks do.
Run under testbed:  scripts/testbed.sh python3 scripts/migration_test.py"""
import argparse, csv, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from run_tests import CURL, CERT, FMT, PROTO, netem

ap = argparse.ArgumentParser()
ap.add_argument("--at", type=float, default=1.5); ap.add_argument("--iterations", type=int, default=5)
ap.add_argument("--file", default="10MB.bin"); ap.add_argument("--prime", type=int, default=1, help="1 = pre-resolve ARP for the new address"); ap.add_argument("--protocols", default="h2,h3,h3_aioquic"); ap.add_argument("--max-time", type=int, default=30)
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "migration.csv"))
a = ap.parse_args()
ipc = lambda *x: subprocess.run(["ip", "netns", "exec", "client", "ip", *x], check=True)

SIZE = {"1MB.bin": 1 << 20, "10MB.bin": 10 << 20}[a.file]

def run(proto, migrate):
    ipc("addr", "flush", "dev", "veth-c"); ipc("addr", "add", "10.0.0.1/24", "dev", "veth-c")
    netem("apply", "delay", "25ms", "rate", "20mbit")
    if migrate and a.prime:  # make the server resolve 10.0.0.3 (ARP) first, so L2 resolution is not part of the test
        ipc("addr", "add", "10.0.0.3/24", "dev", "veth-c")
        subprocess.run(["ip", "netns", "exec", "client", "ping", "-c1", "-W2", "-I", "10.0.0.3", "10.0.0.2"],
                       capture_output=True)
        ipc("addr", "del", "10.0.0.3/24", "dev", "veth-c")
    url = f"https://10.0.0.2/{a.file}"
    if proto == "h3_aioquic":  # aioquic's UDP socket is not pinned to the old source address
        cmd = ["ip", "netns", "exec", "client", sys.executable, f"{HERE}/aioquic_client.py", url, str(a.max_time)]
    else:
        cmd = ["ip", "netns", "exec", "client", CURL, "-s", "-o", "/dev/null", "--cacert", CERT,
               "--max-time", str(a.max_time), *PROTO[proto], "-w", FMT, url]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    if migrate:
        time.sleep(a.at)
        ipc("addr", "add", "10.0.0.3/24", "dev", "veth-c"); ipc("addr", "del", "10.0.0.1/24", "dev", "veth-c")
    out = p.communicate()[0].split()
    if proto == "h3_aioquic":
        ok = p.returncode == 0 and len(out) == 4 and int(out[3]) == SIZE
        return ok, float(out[2]) if ok else ""
    ok = p.returncode == 0 and len(out) == 7 and out[6] == "200"
    return ok, float(out[3]) if ok else ""

with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["protocol", "migrate", "iteration", "completed", "total_s"])
    for migrate in (False, True):
        for it in range(1, a.iterations + 1):
            for proto in a.protocols.split(","):
                ok, t = run(proto, migrate); w.writerow([proto, int(migrate), it, int(ok), t]); fh.flush()
        print("done migrate =", migrate, flush=True)
ipc("addr", "flush", "dev", "veth-c"); ipc("addr", "add", "10.0.0.1/24", "dev", "veth-c"); netem("netem_clear")
