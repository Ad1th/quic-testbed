#!/bin/bash
# Serial confound matrix (one transfer at a time, one container at a time). Run from the repo root on a Docker host.
#   A: offloads on,  default 208 KB UDP rcvbuf  (= original testbed settings)
#   B: offloads off, default rcvbuf
# (C and D here were superseded by the bridge topology: see run_matrix2.sh. ethtool cannot stop TCP's always-GSO.)
# A's 50 ms / 0 % and 1 % cells were collected by the first launch (before the exit-hang guard); this resumes A after them.
set -e
IMG=quic-testbed:pinned
run() { docker run --rm --privileged --network host -v "$PWD":/work $IMG python3 /work/repro/run_rigor.py "$@"; }
I="--iterations 20"
run --out /work/data/rigor/A_offon.csv --offloads on --rtts 50 --losses 2,5 $I
run --out /work/data/rigor/A_offon.csv --offloads on --rtts 100 --losses 0,1,2,5 $I
run --out /work/data/rigor/B_offoff.csv --offloads off --rtts 50,100 --losses 0,1,2,5 $I
