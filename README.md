# quic-testbed: HTTP/2 (TCP) vs HTTP/3 (QUIC) under emulated networks

Rootless, single-machine testbed (WSL2/Linux). A client and a server network namespace are joined by a veth link shaped with
`tc netem`; nginx serves the same file over HTTP/2 (TCP 443) and HTTP/3 (UDP 443); curl (and aioquic for cross-checks) download it
repeatedly; the analysis finds where one protocol beats the other. Course: BCSE308P Computer Networks, VIT. Docs: [`docs/`](docs/README.md).

## Quick start
```bash
sudo modprobe sch_netem                      # once per WSL boot
pip install -r requirements.txt
scripts/run_all.sh demo                      # ~30 s live h2-vs-h3 run (50 ms RTT, 0 % and 2 % loss)
scripts/run_all.sh analyze                   # re-derive tables, statistics, figures from data/raw (no experiments)
```
Prerequisites (curl/nginx with HTTP/3 in `~/.local`, certificate and test files in `~/srv`): `scripts/build_toolchain.sh`
(reconstructed from the build trees, not tested as a whole; the OpenSSL step is an assumption). Run `scripts/testbed.sh <cmd>` to
execute any command with the namespaces and nginx up (no sudo needed).

## Layout
| Path | What |
|---|---|
| `scripts/testbed.sh`, `setup_netns.sh`, `netem.sh` | namespaces, nginx lifecycle, netem profiles (static, burst, India 4G/5G/congested) |
| `scripts/run_tests.py` | sweep runner (curl h2/h3 -> CSV), `--shard k/n` for parallel runs |
| `scripts/analyze_crossover.py`, `stats_significance.py` | medians, winner table, figures; bootstrap CI + Wilcoxon (Bonferroni) |
| `scripts/diagnose_loss.py`, `sender_test.py`, `cc_test.py`, `aioquic_crosscheck.py` | why-is-h3-slow diagnostics |
| `scripts/blackout_test.py`, `migration_test.py` | loss-burst recovery and client-IP-change tests |
| `scripts/capture_handshake.sh`, `pcap_capture.py` | handshake pcap + TLS key log (tcpdump cannot run rootless) |
| `scripts/merge_results.py`, `run_all.sh`, `build_toolchain.sh` | merge shards (never overwrites), pipeline entry point, toolchain build |
| `conf/nginx.conf` | template; `testbed.sh` renders it to `logs/nginx.rendered.conf` |
| `data/raw/` | measurements (`results.csv` 1 MB sweep, `results_10MB.csv`, test CSVs); `results_sweep1_backup.csv` = first sweep |
| `data/processed/`, `data/results/` | derived tables and figures; `data/captures/` pcaps + key log |

## Key results (details: `docs/TODO.md`, `docs/Project_Report_Real_Results.docx`)
- 0 % loss: HTTP/3 ~11 % faster at all 6 RTTs (significant; handshake ~1 RTT vs 2).
- 0.5-1 % uniform loss: no consistent winner. >= 2 %: HTTP/2 faster in all 18 cells.
- 10 MB: HTTP/2 faster in all 9 cells tested. Mobile profiles (Airtel-calibrated RTT/jitter/rate, modeled loss): HTTP/3 faster, not significant after correction.
- Blackout: HTTP/3 not faster to recover. Client IP change: HTTP/2 0/8, aioquic HTTP/3 6/8, curl HTTP/3 0/8.

## Notes
- `data/raw/results.csv` is sweep 1 (minus the old India rows) plus later shards; do not regenerate over it.
- Never run two experiments at once if you want clean timings (several sweeps here ran as parallel shards on 12 threads).
