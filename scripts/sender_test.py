#!/usr/bin/env python3
"""Phase 5: same client (curl h3), different QUIC SENDER: nginx (port 443) vs aioquic server (port 4433), plus curl h2.
Run under testbed.sh."""
import argparse, csv, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from run_tests import CURL, CERT, FMT, netem

ap = argparse.ArgumentParser()
ap.add_argument("--conds", default="50:0,50:1,50:2,100:2"); ap.add_argument("--iterations", type=int, default=12)
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "sender_test.csv"))
a = ap.parse_args()
srv = subprocess.Popen(["ip", "netns", "exec", "server", sys.executable, f"{HERE}/aioquic_server.py", "4433"])
time.sleep(2)

def get(flag, port):
    r = subprocess.run(["ip", "netns", "exec", "client", CURL, "-s", "-o", "/dev/null", "--cacert", CERT, "--max-time", "40",
                        flag, "-w", FMT, f"https://10.0.0.2:{port}/1MB.bin"], capture_output=True, text=True)
    f = r.stdout.split()
    return float(f[3]) if r.returncode == 0 and len(f) == 7 and f[6] == "200" else None

try:
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["rtt_ms", "loss_pct", "sender", "iteration", "total_s"])
        for c in a.conds.split(","):
            rtt, loss = map(float, c.split(":")); netem("netem_static", f"{rtt:g}", f"{loss:g}")
            for it in range(1, a.iterations + 1):
                for name, flag, port in (("nginx_h2", "--http2", 443), ("nginx_h3", "--http3-only", 443), ("aioquic_h3", "--http3-only", 4433)):
                    t = get(flag, port); w.writerow([f"{rtt:g}", f"{loss:g}", name, it, "" if t is None else t]); fh.flush()
            print("done", c, flush=True)
finally:
    srv.terminate(); netem("netem_clear")
