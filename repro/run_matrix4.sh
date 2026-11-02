#!/bin/bash
# P: nginx with the one-line ssthresh patch (repro/Dockerfile.nginxpatch), same conditions as G.
set -e
docker build -q -t quic-testbed:nginxpatch -f repro/Dockerfile.nginxpatch repro
docker run --rm --privileged --network host -v "$PWD":/work quic-testbed:nginxpatch python3 /work/repro/run_rigor.py \
    --out /work/data/rigor/P_nginx_patched.csv --topology bridge --offloads off --rcvbuf 4194304 \
    --protocols h2,h3,h3qg --rtts 50,100 --losses 0,1,2,5 --iterations 20
