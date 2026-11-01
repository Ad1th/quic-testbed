# Project guide: files, folders, and flow

## 1. Folder structure

```
~/quic-testbed/                  <- the project (small, ~400 KB)
├── scripts/                     <- all the logic
│   ├── testbed.sh               <- ENTRY POINT: builds the fake network, starts nginx, runs your command
│   ├── setup_netns.sh           <- creates the two "virtual machines" (namespaces) + cable between them
│   ├── netem.sh                 <- the network-condition knobs (delay, loss, bandwidth, mobile profiles)
│   ├── run_tests.py             <- the experiment runner: loops over conditions, calls curl, writes CSV
│   └── analyze_crossover.py     <- turns raw CSV into medians, winner table, crossover points
├── conf/
│   └── nginx.conf               <- web server config: serves HTTP/2 (TCP 443) and HTTP/3 (UDP 443) on 10.0.0.2
├── data/
│   ├── raw/                     <- measurements straight from curl (one row per request)
│   │   ├── results.csv          <- FINAL merged dataset: 1120 rows (the five shards combined)
│   │   ├── shard_0..4.csv       <- partial results from 5 parallel runs (merged into results.csv)
│   │   └── smoke.csv            <- 8-row early sanity test (can be deleted)
│   └── processed/               <- analysis output
│       ├── medians.csv          <- per condition x protocol: n, fails, median/p25/p75 time, TTFB, handshake
│       ├── crossover_table.csv  <- per condition: h2 vs h3 median, ratio, h3 win fraction, winner
│       └── crossover_report.txt <- the human-readable report (grid + crossover points + mobile profiles)
├── logs/                        <- shard_*.log (progress of each parallel run), nginx-error.log, run_id.txt
└── docs/                        <- this folder

Outside the project (tools it depends on):
~/build/{openssl,nghttp2,nghttp3,ngtcp2,curl,nginx}   source trees you compiled
~/.local/bin/curl                curl 8.23 built with HTTP/3 (ngtcp2 + nghttp3 + OpenSSL 3.6)
~/.local/nginx/sbin/nginx        nginx 1.31 built with HTTP/3 (QUIC) support
~/srv/certs/server.{crt,key}     self-signed TLS cert for 10.0.0.2
~/srv/content/{1MB,10MB}.bin     the test files that get downloaded
```

## 2. What each file does (plain English)

- **testbed.sh** - Wrapper. Uses `unshare -Urnm` so you get fake root + private network *without sudo*,
  mounts a private `/run`, calls `setup_netns.sh`, launches nginx inside the `server` namespace, waits until
  `ping` works, runs whatever command you pass, then kills nginx on exit.
- **setup_netns.sh** - Makes namespaces `client` (10.0.0.1, iface `veth-c`) and `server` (10.0.0.2, iface `veth-s`)
  joined by a virtual Ethernet cable. Safe to re-run.
- **netem.sh** - Uses Linux `tc netem` on *both* ends of the cable. Functions: `netem_static <rtt> <loss>`,
  `netem_loss_burst`, `netem_india_4g`, `netem_india_5g`, `netem_india_4g_congested`, `netem_clear`.
  RTT is split half/half per direction; a 1 Gbit rate cap is set so QUIC bursts don't overflow the UDP
  receive buffer (which would fake extra loss only on h3).
- **run_tests.py** - For each condition: apply netem, then `--iterations` times fetch `1MB.bin` with
  `curl --http2` and `curl --http3-only` (order alternates each iteration to cancel drift). Records connect,
  handshake, TTFB, total time, throughput. Failures/timeouts (40 s) are logged as empty rows.
  Supports `--shard k/n` to split conditions across parallel processes.
- **analyze_crossover.py** - Reads results.csv; failures count as 40 s (right-censored, not dropped);
  computes medians, h3/h2 ratio, paired win-rate, a 5% "tie" band, and linearly interpolates where the
  ratio crosses 1 (the **crossover**).
- **nginx.conf** - One server block listening on `10.0.0.2:443` for both QUIC and TLS/TCP, `Alt-Svc` header
  advertising h3. Note: paths are hard-coded to `/home/abhi/...`.

## 3. The flow, step by step

1. **Build the stack (one time, done).** OpenSSL(QUIC) -> nghttp3 -> ngtcp2 -> nghttp2 -> curl -> nginx, all in `~/.local`.
2. **Create content + cert (one time, done).** `~/srv/content/*.bin`, `~/srv/certs/server.*`.
3. **Run an experiment.**
   ```bash
   cd ~/quic-testbed
   scripts/testbed.sh python3 scripts/run_tests.py --out data/raw/results.csv
   ```
   Behind the scenes: testbed.sh -> setup_netns.sh -> nginx up -> run_tests.py -> (per condition) netem.sh -> curl h2/h3 -> CSV row.
4. **(Optional) Parallelise.** Run 5 copies with `--shard 0/5` ... `--shard 4/5` and different `--out shard_N.csv`,
   then concatenate (keep one header) into `results.csv`. That is how the existing data was produced.
5. **Analyse.** `python3 scripts/analyze_crossover.py` -> writes `data/processed/*`.
6. **Read the result.** `cat data/processed/crossover_report.txt`.

## 4. Mental model

```
  [client ns 10.0.0.1] --veth-c ==== netem (delay/loss/rate) ==== veth-s-- [server ns 10.0.0.2: nginx]
        curl --http2 / --http3-only  ------------- HTTPS GET /1MB.bin ------------->
```
