#!/bin/bash
# Controlled configurations (netem on a router netns, so every protocol's packets are dropped as wire packets):
#   F: bridge, endpoint offloads off, default 208 KB UDP rcvbuf
#   G: F + 4 MB UDP rcvbuf (removes client receive-buffer overflow)
#   D: G + qlog (curl client per sender, quic-go server) at 50 ms / 2 %, for mechanism analysis
set -e
IMG=quic-testbed:pinned
run() { docker run --rm --privileged --network host -v "$PWD":/work $IMG python3 /work/repro/run_rigor.py "$@"; }
G="--topology bridge --offloads off --rtts 50,100 --losses 0,1,2,5 --iterations 20"
run --out /work/data/rigor/F_bridge.csv $G
run --out /work/data/rigor/G_bridge_rcvbuf4m.csv $G --rcvbuf 4194304
run --out /work/data/rigor/D_qlog.csv --topology bridge --offloads off --rcvbuf 4194304 --rtts 50 --losses 2 --iterations 10 --qlog /work/data/rigor/qlog
