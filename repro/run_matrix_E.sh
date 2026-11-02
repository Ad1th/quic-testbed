#!/bin/bash
# E: fully controlled - offloads off, 4 MB UDP rcvbuf, quic-go UDP GSO disabled (every sender's packets reach netem singly)
set -e
IMG=quic-testbed:pinned
run() { docker run --rm --privileged --network host -v "$PWD":/work $IMG python3 /work/repro/run_rigor.py "$@"; }
run --out /work/data/rigor/E_controlled.csv --offloads off --rcvbuf 4194304 --quicgo-gso off --rtts 50,100 --losses 0,1,2,5 --iterations 20
