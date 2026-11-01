# Architecture

## 1. Goal
Measure, under controlled and repeatable network impairment, **when HTTP/3 (QUIC/UDP) is faster than
HTTP/2 (TLS/TCP)** and where the crossover boundary lies in (RTT, packet-loss) space - with no root access
and no second machine.

## 2. System diagram

```
 WSL2 Ubuntu 22.04 host (one machine, no sudo needed at run time)
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ user namespace (unshare -Urnm)  = "fake root" so we can make network stuff   │
 │                                                                              │
 │  ┌─ netns: client ──────┐   veth pair    ┌─ netns: server ───────────────┐   │
 │  │ 10.0.0.1  (veth-c)   │◄══════════════►│ 10.0.0.2  (veth-s)            │   │
 │  │ curl 8.23 (h2 / h3)  │  tc netem on   │ nginx 1.31                    │   │
 │  │ ← run_tests.py       │  BOTH egress:  │   TCP 443: TLS1.3 + HTTP/2    │   │
 │  └──────────────────────┘  delay, loss,  │   UDP 443: QUIC + HTTP/3      │   │
 │                            rate         │   files: 1MB.bin, 10MB.bin    │   │
 │                                         └───────────────────────────────┘   │
 └──────────────────────────────────────────────────────────────────────────────┘
          │ CSV rows                                   ▲ sets conditions
          ▼                                            │
   data/raw/results.csv ──► analyze_crossover.py ──► data/processed/{medians,crossover_table}.csv + report
```

## 3. Components

| Layer | Component | Role |
|---|---|---|
| Isolation | `unshare -Urnm` + `ip netns` | Two independent network stacks on one host, rootless |
| Link | veth pair | Virtual cable client<->server |
| Impairment | `tc netem` (delay, jitter, loss, gemodel, rate) | The experimental variable |
| Server | nginx (HTTP/3 module) | Serves same file over h2 and h3 on port 443 |
| Client | curl built with ngtcp2 + nghttp3 | `--http2` vs `--http3-only` |
| Crypto | OpenSSL 3.6 with QUIC API | TLS 1.3 for both protocols |
| Orchestration | `testbed.sh`, `run_tests.py` | Lifecycle, sweep, CSV logging |
| Analysis | pandas/numpy | Medians, paired comparison, crossover interpolation |

## 4. Experimental design

- **Independent variables:** protocol (h2/h3); RTT {20, 50, 100, 200, 300} ms; uniform loss {0, 0.5, 1, 2, 5} %;
  plus three realistic mobile profiles (India 4G, 5G, congested 4G with bursty Gilbert-Elliott loss).
- **Dependent variables:** connect, handshake, TTFB, total time, throughput.
- **Workload:** one 1 MB GET per measurement, fresh connection each time (so handshake cost is included).
- **Repetitions:** 20 iterations x 2 protocols x 28 conditions = 1120 requests.
- **Controls:** alternate h2/h3 order each iteration (cancels drift); same server, same file, same cert;
  1 Gbit rate cap so UDP receive-buffer overflow doesn't create phantom loss for QUIC.
- **Failure handling:** 40 s timeout, counted *at* 40 s (right-censored) rather than dropped - dropping would
  flatter the slower protocol.
- **Metric:** median total time (robust to outliers), h3/h2 ratio, paired win-fraction; 5% ratio band = tie.

## 5. Key design decisions

1. **Namespaces instead of two VMs/containers** - reproducible, fast, no Docker, no sudo.
2. **netem on both ends** - delay RTT/2 per direction, so the RTT is exactly as specified.
3. **Source-built curl/nginx** - distro packages lack HTTP/3.
4. **Sharding** - conditions are split by `index % n` so the sweep can run in 5 parallel processes (each in
   its own testbed instance).
5. **Crossover by interpolation** - find where log(h3/h2) changes sign between neighbouring grid points.

## 6. Results at a glance (see data/processed/significance.csv and docs/TODO.md for current numbers)

- 0 % loss: HTTP/3 ~11 % faster at every RTT (significant) - saves a round trip in the handshake.
- 0.5-1 % loss: mostly no significant difference.
- >= 2 % loss: HTTP/2 significantly faster in every tested cell.
- Diagnostics: HTTP/3 penalty only when data packets are lost; reproduced with a second QUIC client (aioquic) and a second
  QUIC server (aioquic); TCP Reno vs CUBIC explains part of it.
- Mobile profiles: see the latest crossover report (profiles recalibrated on Airtel measurements, 28 Oct 2026).

## 7. Limitations

Emulated (not real) network; one host so CPU contention is possible; single 1 MB object; curl is a single-stream
client; self-signed cert; no 0-RTT; one implementation pair (ngtcp2 client / nginx server).
