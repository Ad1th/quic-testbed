#!/usr/bin/env python3
"""Phase 8: loss-burst recovery. Download 10MB; at t=--start s make the link drop 100% of packets for --outage s,
then restore. Compare completion time with a no-outage baseline: stall = total - baseline.
Run under testbed:  scripts/testbed.sh python3 scripts/blackout_test.py"""
import argparse, csv, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_tests import CURL, CERT, FMT, PROTO, netem

ap = argparse.ArgumentParser()
ap.add_argument("--rtt", type=float, default=50); ap.add_argument("--rate", default="20mbit")
ap.add_argument("--start", type=float, default=1.5); ap.add_argument("--outages", default="0,1,2,4")
ap.add_argument("--iterations", type=int, default=8); ap.add_argument("--file", default="10MB.bin")
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "blackout.csv"))
a = ap.parse_args()
half = f"{a.rtt/2:g}ms"

def run(proto, outage):
    netem("apply", "delay", half, "rate", a.rate)
    p = subprocess.Popen(["ip", "netns", "exec", "client", CURL, "-s", "-o", "/dev/null", "--cacert", CERT,
                          "--max-time", "60", *PROTO[proto], "-w", FMT, f"https://10.0.0.2/{a.file}"],
                         stdout=subprocess.PIPE, text=True)
    if outage > 0:
        time.sleep(a.start); netem("apply", "delay", half, "rate", a.rate, "loss", "100%")
        time.sleep(outage); netem("apply", "delay", half, "rate", a.rate)
    out = p.communicate()[0].split()
    return float(out[3]) if p.returncode == 0 and len(out) == 7 and out[6] == "200" else None

with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["rtt_ms", "rate", "outage_s", "protocol", "iteration", "total_s"])
    for o in map(float, a.outages.split(",")):
        for it in range(1, a.iterations + 1):
            for proto in (("h2", "h3") if it % 2 else ("h3", "h2")):
                t = run(proto, o)
                w.writerow([f"{a.rtt:g}", a.rate, f"{o:g}", proto, it, "" if t is None else t]); fh.flush()
        print("done outage", o, flush=True)
netem("netem_clear")
