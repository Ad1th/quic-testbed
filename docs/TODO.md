# TODO - tracked against PRD.md

_Last updated: 2026-10-28. Source of truth for requirements: [PRD.md](PRD.md). Detailed items are below the phase table._

## Phase tracker

| Phase | What | Status |
|---|---|---|
| 0 | Toolchain, testbed, netem profiles, runner, smoke test | DONE |
| 1 | Full sweep (25 static + 3 mobile, 1120 rows) + crossover analysis | DONE |
| 2 | Docs folder (guide, architecture, presentation) | DONE |
| 3 | Figures: heatmap + completion-vs-RTT chart (B3, B4, B5) | DONE |
| 4 | aioquic client + cross-check of h3 slowness (A5, B1) | DONE - aioquic is also slower than h2 at 2% loss (4.98s vs 1.42s @50ms; 7.13 vs 3.96 @100ms), so not a curl-only artefact. At 1% loss aioquic beat h2 (0.70 vs 0.93s), so it is implementation-dependent |
| 5 | Explain h3-under-loss result (B1 diagnostics: CC, buffers, one-way loss) | DONE - partially explained: loss on data direction only, not nginx-specific, TCP congestion control accounts for only part (see below) |
| 6 | Extra data: 150 ms / 3 % cells, 10 MB runs (A1, A2) | DONE - 6a: static grid 36 cells, results.csv = 1560 rows, India profiles re-run. 6b: 10 MB, 3 RTT x 3 loss x 10 iters -> data/raw/results_10MB.csv (see 10 MB finding) |
| 7 | Handshake capture with SSLKEYLOGFILE + Wireshark screenshot (A7, C1) | DONE - real Wireshark 3.6.2 screenshots taken headlessly via scripts/wireshark_screenshot.py: docs/evidence/wireshark_h2_crop.png (HTTP/2 decrypted: GET /1MB.bin at 0.203 s) and wireshark_h3_crop.png (QUIC Initial 0.000, server 0.050, client 1-RTT 0.102). LIMITATION: Wireshark 3.6.2 did NOT decrypt the HTTP/3 1-RTT payload (filter `http3` = 0 packets; cause unconfirmed, possibly post-quantum key exchange). Trimmed IPv4-only pcaps h2_ipv4/h3_ipv4 added (originals untouched). |
| 8 | Loss-burst recovery test (A3) | DONE - data/raw/blackout.csv, 64 rows, 0 failures (see finding below) |
| 9 | IP-migration test, optional (A4) | DONE - data/raw/migration.csv, 48 rows (see finding below) |
| 10 | Statistics: bootstrap CI / significance, crossover rule sentence (B2, B6) | DONE for 1 MB data (rerun after 6b for 10 MB) - rule below |
| 11 | India profile calibration (A6) | DONE - Airtel-calibrated RTT/jitter/bandwidth (loss is modeled: ICMP loss measured 0 %) in `netem.sh`; india_4g / india_5g re-run; old rows replaced (backup: data/raw/results_sweep1_backup.csv) |
| 12 | Project_Report.docx with real numbers + limitations (C2, C3) | DONE (draft) - docs/Project_Report_Real_Results.docx, also copied to OneDrive Desktop as a NEW file (original Project_Report.docx untouched). 11 figures, 10 tables, date 28 October 2026, reg. no. 24BCI0054, citations verified and listed in docs/literature_references.md. Still yours: look at it in Word for layout (I cannot render it here) and sign the declaration. |
| 13 | Hygiene: README, run_all.sh, build script, hard-coded paths (D1-D5), demo rehearsal (C4) | DONE except demo rehearsal (yours). README.md, requirements.txt, scripts/run_all.sh (analyze/demo/sweep), merge_results.py, build_toolchain.sh (untested; OpenSSL step assumed), nginx.conf now a template rendered by testbed.sh (no /home/abhi left in conf/ or scripts/; verified with a smoke run). smoke.csv left in place (raw data not deleted). |

## Crossover rule (1 MB, 36 static cells + 3 mobile profiles; data/processed/significance.csv)

> In this testbed HTTP/3 beats HTTP/2 by ~11 % **only on loss-free links** (all 6 RTTs, 20-300 ms, significant).
> At 0.5-1 % uniform random loss neither wins consistently (9 of 12 cells not distinguishable). At >= 2 % uniform loss
> HTTP/2 is faster in all 18 cells, by about 1.3x-4.7x (14 significant after Bonferroni, 4 CI-only; ratio-of-medians 1.31x-7.18x).
> On the bandwidth-limited, bursty-loss mobile profiles calibrated on Airtel, HTTP/3 is faster: India 4G 0.79x,
> India 5G 0.62x, congested 4G 0.77x (95 % bootstrap CIs exclude 1, but not significant after Bonferroni over 39 tests).

Caveats: Phase 6 cells were run as 5 parallel shards on 12 cores (as was sweep 1); 20 paired iterations per cell.
The mobile profiles differ from the static grid in more than loss pattern (they also have a bandwidth cap and jitter),
so "bursty vs uniform loss" is a hypothesis for the difference, not an isolated finding.

## Phase 9 finding: client IP change mid-download (data/raw/migration.csv; 10 MB, 50 ms RTT, 20 Mbit, address 10.0.0.1 -> 10.0.0.3 at ~1.5 s; 8 iterations per cell)

| Client | No switch: completed / median total | With IP switch: completed / median total |
|---|---|---|
| curl HTTP/2 (TCP) | 8/8, 5.13 s | **0/8** |
| curl HTTP/3 | 8/8, 5.05 s | **0/8** |
| aioquic HTTP/3 (vs nginx) | 8/8, 4.74 s | **6/8**, 5.55 s (iterations 3 and 6 timed out at 20 s) |

Reading: HTTP/2 cannot survive the address change (expected for TCP). HTTP/3 **can** migrate (aioquic completed 6 of 8, about 0.8 s
slower than no switch), but **curl's HTTP/3 cannot**: its UDP socket is bound to the old source address, so this is a client
limitation, not a protocol one. The 2 aioquic failures are unexplained: an earlier 3-run check (without ARP priming,
data/raw/migration_unprimed_aioquic_3runs.csv) also failed on its first migrate run, and I added ARP priming for the full run
expecting that to fix it; it did not (failures were iterations 3 and 6, not the first), so **the ARP explanation is not supported**.
Report wording: "HTTP/3 survived the IP change in 6 of 8 runs with an HTTP/3 client that supports it; HTTP/2 survived in 0 of 8."
Do not write "only HTTP/3 survived" without the 6/8 qualifier and the curl caveat.

## Phase 8 finding: blackout (100 % loss) mid-download (data/raw/blackout.csv; 10 MB, 50 ms RTT, 20 Mbit, outage starts at 1.5 s, 8 iterations)

| Outage | h2 median total (s) | h3 median total (s) | h2 added vs no-outage | h3 added vs no-outage |
|---|---|---|---|---|
| none | 4.96 | 5.00 | - | - |
| 1 s | 6.67 | 7.57 | +1.71 | +2.56 |
| 2 s | 8.06 | 10.33 | +3.10 | +5.32 |
| 4 s | 10.94 | 10.28 | +5.98 | +5.27 |

Reading: HTTP/3 did **not** recover faster for 1 s and 2 s outages (it lost 0.9 s and 2.2 s more than HTTP/2); at a 4 s outage
HTTP/3 was 0.7 s ahead. The draft's "HTTP/3 recovers in 0.4 s vs 0.9 s for HTTP/2" is not supported. Likely contributor
(untested): QUIC's probe-timeout backoff after a total blackout vs TCP's retransmission timer; with n=8 per cell and very tight
spreads (e.g. 8.05-8.12 s for h2 at 2 s) the differences are real but this tests one link/size only. Also, the outage was
scripted from the client side with a fixed start time, so the stall position relative to the transfer is the same for both.

## 10 MB finding (data/results/*_10MB.*, data/processed/*_10MB.*; 9 cells, 10 iterations, 90 s cap)

HTTP/2 was faster in **every** 10 MB cell, including 0 % loss (1.13x at 20 ms, 1.23x at 100 and 300 ms, all significant),
where HTTP/3 won for 1 MB. With loss, h3 is far worse (20 ms/0.5 %: 34x; several h3 runs hit the 90 s cap).
Reading: for larger transfers, steady-state throughput of the QUIC stacks under test (nginx/ngtcp2 over a user-space UDP
path) trails kernel TCP; HTTP/3's handshake saving (~1 RTT) is a smaller fraction of a longer transfer. Cause not isolated
(CPU cost of user-space QUIC on a shared 12-core host, congestion control, pacing are candidates). Only 10 iterations and
3 shards ran in parallel, so treat magnitudes as indicative.

## Phase 7 finding (data/captures/, 100 ms RTT, 0 % loss)

curl timing: h2 handshake 0.218 s (~2 RTT) vs h3 0.111 s (~1 RTT). On the wire (handshake_timeline.txt): TCP SYN/SYN-ACK/ACK
takes 100 ms, then TLS ClientHello->ServerHello another ~100 ms, first request at ~203 ms; QUIC's client completes the
handshake and can send at ~102 ms. Note tcpdump cannot run in the rootless namespace (cannot drop privileges), so
`scripts/pcap_capture.py` (AF_PACKET) writes the pcaps; Wireshark opens them normally.

## Phase 5 findings so far (50 ms RTT, 2 % loss, 15 iterations, median total_s)

| Loss applied on | h2 | h3 |
|---|---|---|
| both directions (as in sweep) | 1.94 | 5.78 |
| data direction only (server->client) | 1.88 | 5.55 |
| ACK direction only (client->server) | 0.51 | 0.45 |

Reading: h3's penalty appears only when *data* packets are lost, i.e. it is about the sender's loss recovery /
congestion response, not the handshake or ACK path. Both curl and aioquic clients download from nginx, so the common
factor is nginx's QUIC sender. Hypothesis (to be confirmed by the nginx-vs-aioquic-server test): nginx's QUIC loss
recovery is less aggressive than the Linux TCP stack (SACK/RACK/TLP, CUBIC).

### Sender-implementation test (curl h3 client, median total_s, 12 iterations)

| Condition | nginx h2 | nginx h3 | aioquic-server h3 |
|---|---|---|---|
| 50 ms, 0 % | 0.48 | 0.43 | 0.45 |
| 50 ms, 1 % | 0.59 | 1.29 | 2.58 |
| 50 ms, 2 % | 1.99 | 4.95 | 6.00 |
| 100 ms, 2 % | 5.28 | 12.67 | 11.36 |

Reading: a second, independent QUIC sender is no better (often worse) than nginx, so the slowness is **not nginx-specific**.
It is a property of these QUIC stacks vs Linux kernel TCP under random data loss. Leading candidate: congestion control
(QUIC defaults to NewReno per RFC 9002; Linux TCP uses CUBIC + SACK/RACK-TLP). Being tested with server TCP set to reno.

### TCP congestion-control test (server TCP cubic vs reno, median total_s, 12 iterations)

| Condition | h2 cubic | h2 reno | h3 (cubic run) | h3 (reno run) |
|---|---|---|---|---|
| 50 ms, 1 % | 0.57 | 0.50 | 3.24 | 1.05 |
| 50 ms, 2 % | 2.40 | 2.46 | 6.24 | 6.00 |
| 100 ms, 2 % | 4.05 | 6.21 | 7.61 | 7.39 |

Reading: Reno slows h2 noticeably only at 100 ms (4.05 -> 6.21 s, closer to h3) and not at 50 ms. h3 stays slower than
h2 even against Reno at 50 ms (6.0 vs 2.5 s). So congestion-control *type* is a partial factor, not the full explanation.
Remaining candidates (untested): TCP's SACK/RACK-TLP/PRR loss recovery vs QUIC's PTO/packet-threshold detection, pacing,
and run-to-run noise (h3 at 50 ms/1 % gave 3.24 s vs 1.05 s in two identical configs, n=12).
**Report wording:** "HTTP/3 was slower under uniform random data-packet loss; the effect holds for two independent QUIC
senders and is only partly attributable to congestion control; we did not isolate the full mechanism."

## PRD goals scorecard

| Goal | Status | Notes |
|---|---|---|
| G1 h2 + h3 from one server | DONE | nginx 1.31 + curl 8.23; both verified (`http_version` 2 / 3 in CSV) |
| G2 netem matrix + 3 mobile profiles | MOSTLY | 5 RTT x 5 loss = 25 static cells + 3 profiles. PRD wants "~50+" cells (see A1) |
| G3 metrics per run | PARTIAL | connect/handshake/TTFB/total/throughput done. **Loss-burst recovery** and **migration** not done |
| G4 crossover rule | PARTIAL | Report generated, but data contradicts the PRD's expected story (see "Critical finding") |
| G5 Indian profiles, calibrated | PARTIAL | Profiles exist; **not calibrated** against real ping/speedtest data |
| G6 defensible report + demo | NOT STARTED | Project_Report.docx exists (Windows Desktop) but still placeholders; demo script drafted in Presentation.md |

## CRITICAL finding - read before writing the report

PRD section 8 pre-writes conclusions such as "HTTP/3 outperformed HTTP/2 in X% of conditions, gap widening as
RTT and loss increase". **The measured data says the opposite for uniform random loss**:

- Static grid: h3 faster in 7 of 25 cells, h2 faster in 18. At >= 1-2% loss h3 is 2.5-7x *slower*.
- h3 wins only at 0% loss (~11%, the handshake saving) and on India 4G (0.64x, bursty loss) / congested 4G (0.95x).
- India 5G: h2 wins (1.17x).

Do **not** fill the PRD's bracketed placeholders with assumed numbers (the PRD itself says "from your actual data").
Present the real result, and explain it (task B1). A true negative result with a mechanism is a stronger report than
a copied expectation. Conclusions 1, 2, 4 in PRD section 8 will need rewording to match the data.

## A. Data collection still missing

- [ ] **A1. More static cells** - PRD asks ~50+ cells. Add RTT 150 ms and loss 3 % (already in `run_tests.py` defaults,
      skipped in the sweep) -> 6x6 = 36; add 10 ms / 400 ms or 0.1 % / 10 % to exceed 50 if needed.
- [ ] **A2. 10 MB file runs** (PRD scope: 1 MB *and* 10 MB). `10MB.bin` exists but was never run (`--file 10MB.bin`).
- [ ] **A3. Loss-burst scenario** (one scenario in scope; G3 "loss-burst recovery"). `netem_loss_burst` exists in
      `netem.sh` but there is no runner mode that measures *recovery time* (e.g. inject a 1-2 s total blackout
      mid-transfer and record stall duration for h2 vs h3). Needs a new script.
- [ ] **A4. IP-migration scenario** (optional). Needs a client that supports QUIC migration (aioquic, curl cannot);
      change the client veth address mid-transfer and compare h3 survival vs h2 reconnect.
- [ ] **A5. aioquic secondary client** - PRD technical requirement. aioquic 1.3.0 is installed but no script uses it.
      Use it for A4 and as a cross-check that h3 slowness under loss is not a curl/ngtcp2 artefact.
- [~] **A6. Calibrate India profiles** (values applied; re-run pending) - (optional/recommended) - run `ping -c 100` and a speedtest from a phone on
      Jio/Airtel, fit RTT mean/jitter/loss, update `netem_india_4g/5g`. Otherwise report them as "modelled on typical
      variability and bursty loss" (PRD conclusion 6 wording).
- [ ] **A7. SSLKEYLOGFILE** - not set anywhere (grep finds nothing). Needed for decrypted captures (C1). Set it in
      `run_tests.py`'s curl env (and nginx `ssl_key_log_file` if supported by the OpenSSL build).

## B. Analysis & explanation

- [ ] **B1. Explain why h3 loses under uniform loss.** Candidates: curl/ngtcp2 default congestion control (try BBR vs
      Cubic - note PRD lists CC comparison as *out of scope / future work*, so keep it a small diagnostic, not a
      headline), nginx `http3_stream_buffer_size`, UDP socket buffers, netem loss applied on both directions
      (doubles effective loss for the 2-way handshake), single-host CPU contention. Run the A5 cross-check first.
- [ ] **B2. Stats rigour** - bootstrap CIs / Mann-Whitney on the 20 paired runs; several adjacent cells flip winner
      (e.g. RTT 300 ms crossings at 0.32 %, 0.61 %, 1.15 %), so the "crossover" is noisy. Consider 40+ iterations near
      the boundary.
- [x] **B3. Heatmap** (DONE 2026-10-28 -> data/results/crossover_heatmap.png) `crossover_heatmap.png` - RTT x loss, colour = winner / ratio, boundary contour. matplotlib 3.10
      is installed; add to `analyze_crossover.py`.
- [x] **B4. Line chart** (DONE -> data/results/completion_vs_rtt.png) - completion time vs RTT, one line per protocol (PRD section 7), per loss level.
- [x] **B5. Output path mismatch** (DONE: script now also writes data/results/crossover_summary.csv) - PRD deliverable 3 names `data/results/crossover_summary.csv`; code writes
      `data/processed/crossover_table.csv`. Either rename output or update the PRD.
- [ ] **B6. State the crossover rule in one sentence** from real data, e.g. "h3 only wins at ~0 % loss or under
      bursty loss; any uniform loss >= 0.5 % favours h2 in this testbed". Needs B1/B2 first so it is defensible.
- [ ] **B7. Rate-cap caveat** - netem uses `rate 1gbit` on static cells (to avoid UDP rcvbuf overflow). Mention in
      Limitations; PRD conclusion 2 mentions "high bandwidth", which matches.

## C. Captures & report

- [ ] **C1. Wireshark/tcpdump capture** with keylog: h2 vs h3 handshake at e.g. 100 ms RTT, 0 % loss. Screenshot
      showing TCP+TLS = 2 RTT vs QUIC = 1 RTT (tcpdump + wireshark installed; nothing captured yet).
      Note: our `handshake_s` data already shows it numerically (e.g. 0 % loss, 100 ms: h2 ~0.2 s vs h3 ~0.1 s) - verify.
- [ ] **C2. Project_Report.docx** - found at `/mnt/c/Users/abhil/OneDrive/Desktop/Project_Report.docx` (Windows side,
      not in the repo). Still has placeholders; fill with real numbers, graphs, screenshots. Do after B1/B3.
- [ ] **C3. Limitations section** - copy PRD scope-out items + emulated/single-host/single-client/self-signed cert.
- [ ] **C4. Rehearse live demo** - commands drafted in `Presentation.md`; update the narrative to match the real
      (non-placeholder) findings once B1 is resolved.

## D. Engineering hygiene

- [ ] D1. Root `README.md`, one-shot `run_all.sh` (sweep -> merge shards -> analyse -> plots), `requirements.txt`.
- [ ] D2. Toolchain build script (currently only in shell history) so the testbed is reproducible.
- [ ] D3. Remove hard-coded `/home/abhi` in `nginx.conf` / `run_tests.py`.
- [ ] D4. Delete `data/raw/smoke.csv`; document the shard-merge step.
- [ ] D5. Update `Presentation.md` / `Architecture.md` result sections after new data lands (they currently reflect the 1120-row sweep only).

## Done

- [x] Build OpenSSL 3.6, nghttp3, ngtcp2, nghttp2, curl (h3), nginx (h3)
- [x] Self-signed cert, 1 MB + 10 MB test files
- [x] Rootless namespace testbed (`testbed.sh`, `setup_netns.sh`) - verified
- [x] netem profiles: static, loss_burst (Gilbert-Elliott), india_4g, india_5g, india_4g_congested
- [x] Runner `run_tests.py` (sharding, alternating order, failures kept as 40 s right-censored)
- [x] Smoke test
- [x] Full sweep: 25 static cells + 3 mobile profiles x 20 iterations x 2 protocols = 1120 rows -> `data/raw/results.csv`
- [x] Crossover analysis script + medians / table / text report
- [x] Docs folder (PROJECT_GUIDE, Architecture, Presentation, this TODO)

## Suggested order of attack

1. B3 heatmap + B4 line chart (quick, unlocks the story)  2. A5 + B1 (explain h3 slowness; decides the narrative)
3. A1/A2 more data  4. A7 + C1 capture  5. A3 loss-burst  6. A4 migration (optional)  7. B2 stats  8. C2 report  9. C4 rehearse
