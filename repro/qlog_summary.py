#!/usr/bin/env python3
"""Summarise qlog files (JSON-SEQ .sqlog from curl/ngtcp2 and quic-go) per connection.
For each file: vantage (client/server), duration, packets sent/received, packets declared lost, PTO expiries,
congestion-state changes, and stalls (idle gaps between received packets > --stall-ms) with their total length.
Client-side stalls are what an h3 transfer looks like when the *server* is stuck in loss recovery.
usage: qlog_summary.py <dir_or_files>... [--stall-ms 150] [--csv out.csv]"""
import argparse, csv, glob, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("paths", nargs="+")
ap.add_argument("--stall-ms", type=float, default=150)
ap.add_argument("--csv", default=None)
a = ap.parse_args()

files = []
for p in a.paths:
    files += sorted(glob.glob(os.path.join(p, "*qlog*"))) if os.path.isdir(p) else [p]


def records(path):
    raw = open(path, "rb").read().decode("utf-8", "replace")
    parts = raw.split("\x1e") if "\x1e" in raw else raw.splitlines()
    for part in parts:
        part = part.strip()
        if part:
            try:
                yield json.loads(part)
            except json.JSONDecodeError:
                continue


def name_of(ev):
    if "name" in ev:
        return ev["name"]
    return f"{ev.get('category', '')}:{ev.get('event', '')}"


rows = []
for f in files:
    vantage, evs = "?", []
    for r in records(f):
        tr = r.get("trace") or {}
        vp = tr.get("vantage_point") or r.get("vantage_point")
        if isinstance(vp, dict) and vp.get("type"):
            vantage = vp["type"]
        if "time" in r and ("name" in r or "event" in r):
            evs.append(r)
    if not evs:
        continue
    t = [float(e["time"]) for e in evs]
    n = [name_of(e) for e in evs]
    recv_t = sorted(ti for ti, ni in zip(t, n) if ni.endswith("packet_received"))
    gaps = [b - x for x, b in zip(recv_t, recv_t[1:]) if b - x > a.stall_ms]
    pto = sum(1 for e, ni in zip(evs, n) if ni.endswith("loss_timer_updated")
              and (e.get("data") or {}).get("event_type") == "expired")
    rows.append(dict(file=os.path.basename(f), vantage=vantage, duration_ms=round(max(t) - min(t), 1),
                     sent=sum(ni.endswith("packet_sent") for ni in n), received=len(recv_t),
                     lost=sum(ni.endswith("packet_lost") for ni in n), pto_expired=pto,
                     cc_state_changes=sum(ni.endswith("congestion_state_updated") for ni in n),
                     stalls=len(gaps), stall_ms_total=round(sum(gaps), 1),
                     max_stall_ms=round(max(gaps), 1) if gaps else 0.0))

if not rows:
    sys.exit("no qlog events found")
keys = list(rows[0])
print("\t".join(keys))
for r in rows:
    print("\t".join(str(r[k]) for k in keys))
if a.csv:
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows(rows)
