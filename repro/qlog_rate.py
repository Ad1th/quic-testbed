#!/usr/bin/env python3
"""Per-connection delivery rate seen by the client (packets received per RTT window, median over the transfer) and, for
server qlogs that carry recovery:metrics_updated (quic-go), the time-weighted median congestion window in packets.
usage: qlog_rate.py <rtt_ms> <qlog_dir>..."""
import json, os, sys, glob
import numpy as np
rtt = float(sys.argv[1])
for d in sys.argv[2:]:
    per_rtt, cw = [], []
    for f in sorted(glob.glob(os.path.join(d, "*qlog"))):
        ev = []
        for part in open(f, encoding="utf-8", errors="replace").read().split("\x1e"):
            part = part.strip()
            if part:
                try:
                    ev.append(json.loads(part))
                except json.JSONDecodeError:
                    pass
        recv = np.array([e["time"] for e in ev if e.get("name", "").endswith("packet_received")], float)
        if len(recv) > 50:
            b = np.histogram(recv, bins=np.arange(recv.min(), recv.max() + rtt, rtt))[0]
            per_rtt.append(np.median(b[1:-1]) if len(b) > 3 else np.nan)
        m = [(e["time"], e["data"]["congestion_window"]) for e in ev
             if e.get("name", "").endswith("metrics_updated") and "congestion_window" in e.get("data", {})]
        if len(m) > 2:
            t = np.array([x[0] for x in m]); w = np.array([x[1] for x in m]) / 1252
            dt = np.diff(t, append=t[-1]); order = np.argsort(w); cum = np.cumsum(dt[order])
            cw.append(w[order][np.searchsorted(cum, cum[-1] / 2)])
    print(f"{os.path.basename(d):15s} pkts received per {rtt:g} ms (median over conns): "
          f"{np.nanmedian(per_rtt) if per_rtt else float('nan'):.1f}"
          + (f" | server cwnd pkts (time-weighted median): {np.median(cw):.1f}" if cw else ""))
