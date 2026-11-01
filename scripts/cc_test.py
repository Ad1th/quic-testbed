#!/usr/bin/env python3
"""Phase 5: does the server's TCP congestion control explain h2's advantage under loss? Switch server-netns TCP CC
(cubic vs reno) and compare h2 and h3 (h3 unaffected: QUIC CC lives in nginx). Run under testbed.sh."""
import argparse, csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from run_tests import fetch, netem

ap = argparse.ArgumentParser()
ap.add_argument("--conds", default="50:1,50:2,100:2"); ap.add_argument("--iterations", type=int, default=12)
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "cc_test.csv"))
a = ap.parse_args()
with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["rtt_ms", "loss_pct", "tcp_cc", "protocol", "iteration", "total_s"])
    for cc in ("cubic", "reno"):
        subprocess.run(["ip", "netns", "exec", "server", "sysctl", "-qw", f"net.ipv4.tcp_congestion_control={cc}"], check=True)
        for c in a.conds.split(","):
            rtt, loss = map(float, c.split(":")); netem("netem_static", f"{rtt:g}", f"{loss:g}")
            for it in range(1, a.iterations + 1):
                for proto in (("h2", "h3") if it % 2 else ("h3", "h2")):
                    f = fetch(proto, "1MB.bin", 40)
                    w.writerow([f"{rtt:g}", f"{loss:g}", cc, proto, it, float(f[3]) if f else ""]); fh.flush()
        print("done", cc, flush=True)
netem("netem_clear")
