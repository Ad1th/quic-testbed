# repro/ - controlled re-run of the HTTP/2 vs HTTP/3 comparison

Everything runs in Docker on any host with a Linux kernel that has `sch_netem` (Docker Desktop's VM does). Run from the repo root.
Keep the host awake and on power: a sleeping host freezes the VM (analysis drops affected transfers, but runs get long).

| File | What |
|---|---|
| `Dockerfile` | Ubuntu 22.04 + the exact OpenSSL/nghttp3/ngtcp2/nghttp2/curl/nginx commits of `scripts/build_toolchain.sh` (-> `quic-testbed:pinned`) |
| `Dockerfile.quiche` | + Cloudflare quiche 0.29.3 `quiche-server` (-> `quic-testbed:quiche`) |
| `Dockerfile.nginxpatch` | same nginx commit with the one-line CUBIC ssthresh change (-> `quic-testbed:nginxpatch`) |
| `quicgo-server/` | quic-go v0.64.1 HTTP/3 static file server; build: `cd repro/quicgo-server && GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build` (use `amd64` on x86) |
| `run_rigor.py` | serial runner: `--topology direct|bridge`, `--offloads on|off`, `--rcvbuf`, `--quicgo-gso`, `--protocols h2,h3,h3qg,h3qc`, `--qlog DIR`; logs per-transfer netem sent/dropped, TCP RetransSegs, UDP RcvbufErrors, client/server CPU |
| `run_matrix.sh` | configurations A (original settings) and B (ethtool offloads off) |
| `run_matrix2.sh` | F (bridge), G (bridge + 4 MB rcvbuf), D (qlog) |
| `run_matrix3.sh` | H (G + quiche, four senders) |
| `run_matrix4.sh` | P (G with patched nginx) |
| `analyze_rigor.py` | medians, realised loss, paired ratios with bootstrap CI + Wilcoxon/Bonferroni |
| `plot_rigor.py` | figures (realised loss, ratios, CDFs) |
| `qlog_summary.py`, `qlog_rate.py` | qlog stalls / packets-per-RTT / quic-go cwnd |

Data and reports: `data/rigor/` (`report_<config>.md`, `figs/`).
