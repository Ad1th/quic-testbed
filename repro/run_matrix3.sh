#!/bin/bash
# H: G's conditions (bridge, endpoint offloads off, 4 MB UDP rcvbuf) with a fourth sender, Cloudflare quiche (h3qc).
set -e
docker image inspect quic-testbed:quiche >/dev/null 2>&1 || docker build -q -t quic-testbed:quiche -f repro/Dockerfile.quiche repro
run() { docker run --rm --privileged --network host -v "$PWD":/work quic-testbed:quiche python3 /work/repro/run_rigor.py "$@"; }
run --out /work/data/rigor/H_bridge_rcvbuf4m_4senders.csv --topology bridge --offloads off --rcvbuf 4194304 \
    --protocols h2,h3,h3qg,h3qc --rtts 50,100 --losses 0,1,2,5 --iterations 20
