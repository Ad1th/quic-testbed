# PRD — QUIC vs TCP Performance Analyzer

**Course:** BCSE308P – Computer Networks, VIT
**Student:** Abhilash Singh (24BCI0054)
**Status:** Build in progress (WSL2 environment, Oct 2026)

---

## 1. Problem Statement

HTTP/3 (QUIC) is being adopted industry-wide on the assumption that it outperforms HTTP/2 (TCP). That evidence mostly comes from measurements on stable, high-quality Western networks. Indian mobile networks (4G/5G) behave differently — latency swings wildly and packet loss arrives in sudden bursts rather than steadily. Whether QUIC's advantages hold up under *those* conditions hasn't been directly tested, and no existing study states a precise condition (RTT/loss threshold) at which TCP is still competitive or better.

**This project answers two concrete questions:**
1. Under emulated network conditions resembling Indian mobile networks, does HTTP/3 measurably outperform HTTP/2?
2. Is there a precise "crossover point" — a condition under which HTTP/2 matches or beats HTTP/3 — and where is it?

---

## 2. Goals

| # | Goal | Done when |
|---|---|---|
| G1 | Serve identical content over HTTP/2 and HTTP/3 from one server | `curl --http2` and `curl --http3-only` both succeed against the same file |
| G2 | Emulate a matrix of network conditions | `tc netem` sweep runs RTT 20–300ms × loss 0–5%, plus 3 mobile profiles |
| G3 | Measure the right metrics per run | handshake time, TTFB, total time, throughput, loss-burst recovery, migration behavior logged per run |
| G4 | Find the crossover point | A stated rule (e.g. "HTTP/2 competitive below X ms RTT, Y% loss") backed by data |
| G5 | Model Indian mobile conditions specifically | `india_4g`/`india_5g` netem profiles, ideally calibrated against real measured ping/loss samples |
| G6 | Produce a defensible report and demo | Report has real (not placeholder) data; live demo reproduces the headline claim |

---

## 3. Scope

**In scope:**
- Single client, single server, same machine (WSL2), connected via Linux network namespaces + `tc netem`
- HTTP/2-over-TCP vs HTTP/3-over-QUIC comparison only
- File-download workload (1MB, 10MB static files)
- Static RTT/loss matrix + 3 named mobile profiles + one loss-burst scenario + one IP-migration scenario

**Out of scope (explicitly, for the report's Limitations section):**
- Multiple concurrent clients / real traffic load
- Real device testing on an actual Jio/Airtel network (unless done as a bonus calibration step)
- Comparing congestion control algorithms (BBR vs CUBIC) — noted as future work
- CPU/battery cost measurement — noted as future work
- Realistic workloads (video streaming, many small objects) — noted as future work

---

## 4. Technical Requirements

| Component | Requirement |
|---|---|
| Server | Nginx built with `--with-http_v3_module`, serving same file over TCP:443 (h2) and UDP:443 (h3) |
| Client | curl built with `--with-ngtcp2 --with-nghttp3` (`--http3-only` working); aioquic as secondary client |
| TLS | OpenSSL 3.5+ (QUIC API) or quictls; self-signed cert; `SSLKEYLOGFILE` set for Wireshark decryption |
| Network emulation | `tc netem` on a veth link between two Linux network namespaces |
| Automation | Python script sweeping RTT × loss × protocol × profile, N≥20 runs per cell, writing to CSV |
| Analysis | Script computing per-cell medians, crossover boundary, and a heatmap |

---

## 5. Data Schema (`data/raw/results.csv`)

```
run_id, timestamp, protocol, profile, rtt_ms, loss_pct, iteration,
connect_s, handshake_s, ttfb_s, total_s, throughput_Bps, http_version
```

---

## 6. Deliverables

1. Working testbed (Nginx + curl + netem namespaces) — runnable end-to-end
2. `data/raw/results.csv` — real measured data, not simulated
3. `data/results/crossover_summary.csv` and `crossover_heatmap.png`
4. `Project_Report.docx` — filled with **real** results (replacing current placeholders)
5. A short live-demo script (commands + talking points)
6. Wireshark capture (decrypted via keylog) showing the handshake comparison

---

## 7. What the Final Output Should Look Like

- **A CSV of real timing data** across ~50+ static conditions × 2 protocols × 20 runs, plus 3 mobile profiles.
- **A heatmap** (RTT on one axis, loss on the other) colored by which protocol wins, with a visible boundary line.
- **One sentence stating the crossover rule**, e.g.: *"HTTP/2 is only competitive below ~X ms RTT and ~Y% loss; above that, HTTP/3 wins by Z% on average."* — X, Y, Z come from your actual data, not assumed.
- **A table or chart** of completion time vs RTT, one line per protocol, showing the gap widening as conditions worsen.
- **A packet capture screenshot** comparing handshake round-trips (QUIC: 1-RTT vs TCP+TLS: 2-RTT).
- **A loss-burst recovery comparison** (HTTP/2 stalls and restarts; HTTP/3 recovers faster).
- Optional: a connection-migration result (HTTP/3 survives a simulated IP switch, HTTP/2 does not).

---

## 8. Conclusions to Present to Your Professor

State these as findings, backed by your actual numbers (replace bracketed placeholders with your real results):

1. **Headline finding:** "HTTP/3 (QUIC) outperformed HTTP/2 (TCP) in [X]% of tested conditions, with the gap widening as RTT and packet loss increased."
2. **The crossover point:** "Below approximately [X] ms RTT and [Y]% loss, with high bandwidth, HTTP/2 matched or slightly outperformed HTTP/3. Above that threshold, HTTP/3 was consistently faster, by up to [Z]% at the highest-RTT, highest-loss conditions tested."
3. **Handshake efficiency:** "QUIC's 1-RTT handshake measurably reduced connection setup time compared to TCP+TLS's 2-RTT handshake, confirmed via decrypted packet capture."
4. **Resilience under loss:** "After a simulated loss burst, HTTP/3 recovered in [X]s versus [Y]s for HTTP/2, consistent with QUIC's lack of head-of-line blocking."
5. **Connection migration:** "HTTP/3 maintained the connection through a simulated IP address change; HTTP/2 could not, requiring a full reconnect."
6. **Relevance to India:** "Under network conditions modeled on Indian 4G/5G characteristics — [calibrated against real measurements / modeled on typical variability and bursty loss] — HTTP/3's advantage was [most/equally] pronounced, supporting wider adoption of HTTP/3 for Indian mobile users."
7. **Honest limitation:** "This testbed uses emulated network conditions on a single machine rather than real carrier networks, and tests a single-client file-download workload rather than concurrent or streaming traffic — both are noted as directions for future work."

---

## 9. Remaining Tasks (as of this PRD)

- [ ] Finish building Nginx with HTTP/3 (in progress)
- [ ] Configure and start Nginx serving test files over h2 + h3
- [ ] Set up netem profiles and namespaces
- [ ] Run smoke test (one condition, both protocols)
- [ ] Run full sweep → `data/raw/results.csv`
- [ ] Run crossover analysis → heatmap + summary
- [ ] (Optional, recommended) Calibrate `india_4g`/`india_5g` profiles against real phone ping/speedtest data
- [ ] Capture Wireshark handshake comparison with TLS keylog
- [ ] Update `Project_Report.docx` with real numbers, screenshots, graphs
- [ ] Rehearse live demo
