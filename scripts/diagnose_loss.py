#!/usr/bin/env python3
"""Phase 5 diagnostic: is h3's weakness under uniform loss caused by WHERE loss is applied?
Variants at one (rtt, loss): both directions (as in the sweep), data direction only (server->client egress),
ack direction only (client->server egress). Run under testbed.sh."""
import argparse, csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_tests import fetch, netem

ap = argparse.ArgumentParser()
ap.add_argument("--rtt", type=float, default=50); ap.add_argument("--loss", type=float, default=2)
ap.add_argument("--iterations", type=int, default=15)
ap.add_argument("--out", default=os.path.join(HERE, "..", "data", "raw", "diagnose_loss.csv"))
a = ap.parse_args()

def tc(ns, dev, *args):
    subprocess.run(["ip", "netns", "exec", ns, "tc", "qdisc", "add", "dev", dev, "root", "netem", *args], check=True)

def setup(variant):
    netem("netem_clear")
    d = f"{a.rtt/2:g}ms"
    lossy = ["delay", d, "rate", "1gbit", "loss", f"{a.loss:g}%"]
    clean = ["delay", d, "rate", "1gbit"]
    tc("client", "veth-c", *(lossy if variant in ("both", "ack_only") else clean))
    tc("server", "veth-s", *(lossy if variant in ("both", "data_only") else clean))

with open(a.out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["rtt_ms", "loss_pct", "variant", "protocol", "iteration", "total_s"])
    for v in ("both", "data_only", "ack_only"):
        setup(v)
        for it in range(1, a.iterations + 1):
            for proto in (("h2", "h3") if it % 2 else ("h3", "h2")):
                f = fetch(proto, "1MB.bin", 40)
                w.writerow([f"{a.rtt:g}", f"{a.loss:g}", v, proto, it, float(f[3]) if f else ""]); fh.flush()
        print("done", v, flush=True)
netem("netem_clear")
