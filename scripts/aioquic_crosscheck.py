#!/usr/bin/env python3
"""Compare h3 via curl(ngtcp2) vs h3 via aioquic vs h2 via curl on a few lossy conditions.
Run under testbed:  scripts/testbed.sh python3 scripts/aioquic_crosscheck.py"""
import argparse, csv, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_tests import netem, fetch

ap = argparse.ArgumentParser()
ap.add_argument("--conds", default="50:0,50:1,50:2,100:2")  # rtt:loss
ap.add_argument("--iterations", type=int, default=10)
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "aioquic_check.csv"))
a = ap.parse_args()

def aio(max_time=40):
    r = subprocess.run(["ip", "netns", "exec", "client", sys.executable, f"{HERE}/aioquic_client.py",
                        "https://10.0.0.2/1MB.bin", str(max_time)], capture_output=True, text=True)
    f = r.stdout.split()
    return float(f[2]) if r.returncode == 0 and len(f) == 4 and int(f[3]) == 1048576 else None

with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["rtt_ms", "loss_pct", "client", "iteration", "total_s"])
    for c in a.conds.split(","):
        rtt, loss = map(float, c.split(":"))
        netem("netem_static", f"{rtt:g}", f"{loss:g}")
        for it in range(1, a.iterations + 1):
            for name in ("curl_h2", "curl_h3", "aioquic_h3"):
                if name == "aioquic_h3": t = aio()
                else:
                    f = fetch(name[-2:], "1MB.bin", 40); t = float(f[3]) if f else None
                w.writerow([f"{rtt:g}", f"{loss:g}", name, it, "" if t is None else t]); fh.flush()
        print("done", c, flush=True)
netem("netem_clear")
