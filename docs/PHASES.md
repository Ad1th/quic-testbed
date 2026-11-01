# Phases explained

What is happening in each phase, why it exists, and what you can say about it. Status lives in [TODO.md](TODO.md).

## Phase 0 - Build the testbed (DONE)
**What:** Compile OpenSSL 3.6 (has the QUIC API), nghttp3 (HTTP/3 framing), ngtcp2 (QUIC transport), nghttp2, then curl
and nginx against them. Create namespaces `client`/`server` joined by a veth cable, add `tc netem` on both ends, write
the runner that calls curl in the client namespace.
**Why:** Ubuntu's curl/nginx have no HTTP/3, and you need a network you can degrade on demand without a second machine.
**Say:** "Everything from the crypto library up was built from source; network conditions are set by the kernel."

## Phase 1 - Full sweep + analysis (DONE)
**What:** For 25 (RTT, loss) pairs and 3 mobile profiles, download a 1 MB file 20 times with h2 and 20 with h3
(alternating order). Result: 1120 rows in `data/raw/results.csv`. `analyze_crossover.py` turns it into medians, h3/h2
ratios, win-rates, crossover points.
**Why:** PRD goals G2-G4: a matrix of conditions and a crossover rule backed by data.

## Phase 2 - Docs (DONE)
**What:** `docs/` folder: file guide, architecture, presentation plan, TODO, this file.
**Why:** So you can explain and reproduce the project.

## Phase 3 - Figures (DONE)
**What:** `analyze_crossover.py` now draws a heatmap (colour = h3/h2 ratio, black line = where winner flips) and
per-loss line charts of completion time vs RTT, saved in `data/results/`, plus `crossover_summary.csv`.
**Why:** PRD section 7 requires a heatmap and a time-vs-RTT chart; a picture shows the result faster than a table.

## Phase 4 - Second client cross-check (IN PROGRESS)
**What:** `aioquic_client.py` is an independent Python HTTP/3 client. `aioquic_crosscheck.py` downloads the same file
with curl-h2, curl-h3 and aioquic-h3 under the same loss (50 ms: 0/1/2 % loss, 100 ms: 2 %), 10 times each.
**Why:** The surprising finding is "h3 is much slower under uniform loss". Before believing it, rule out that it is
just curl/ngtcp2's behaviour. If aioquic is also slow -> likely real/server-side or netem-related; if aioquic is
fast -> it is a curl/ngtcp2 matter. Also satisfies the PRD requirement for aioquic as a secondary client.

## Phase 5 - Explain the h3-under-loss result
**What:** Run targeted diagnostics at one bad cell (e.g. 50 ms, 2 % loss): (a) apply loss one-way only, since our netem
drops on both directions, (b) vary UDP buffer sizes / nginx `http3_stream_buffer_size`, (c) compare congestion
controllers if the stacks allow it, (d) look at retransmission counts in a packet capture.
**Why:** A finding that contradicts common belief needs a mechanism, otherwise it looks like a bug. This is what makes the
result defensible in front of a professor. Note the PRD lists CC comparison as future work, so keep this as a diagnostic.

## Phase 6 - Extra data cells
**What:** Re-run the runner with `--rtts 150 ... --losses 3 ...` to fill the grid toward the PRD's "~50+" cells, and
`--file 10MB.bin` for the large-file case.
**Why:** PRD scope says 1 MB *and* 10 MB, and more cells make the crossover boundary less noisy.

## Phase 7 - Handshake capture
**What:** Set `SSLKEYLOGFILE` for curl, run `tcpdump` on the veth link during one h2 and one h3 request at e.g. 100 ms
RTT, open in Wireshark with the keylog to decrypt, and screenshot the round trips.
**Why:** PRD conclusion 3: QUIC's handshake needs fewer round trips than TCP+TLS. Our CSV already shows it in numbers
(handshake_s ~2x smaller for h3); the capture shows it on the wire.

## Phase 8 - Loss-burst recovery
**What:** New script: start a download, make the link drop everything for ~1-2 s mid-transfer (netem 100 % loss, then
clear), and measure how long each protocol stalls before throughput resumes.
**Why:** PRD conclusion 4 (resilience). It tests the real claim about QUIC avoiding TCP head-of-line stalls, which a
steady uniform-loss test does not.

## Phase 9 - Connection migration (optional)
**What:** With aioquic, change the client's IP address (add a second veth address / switch path) mid-transfer; see whether
the QUIC connection survives vs HTTP/2 having to reconnect.
**Why:** PRD conclusion 5. Marked optional in the PRD.

## Phase 10 - Statistics and the crossover sentence
**What:** Bootstrap confidence intervals on the h3/h2 ratio per cell and a paired test (Wilcoxon) across iterations;
mark cells whose difference is not significant as ties. Then write the one-sentence rule from what survives.
**Why:** Neighbouring cells flip winner (e.g. 300 ms column), so without significance the boundary is partly noise.

## Phase 11 - Calibrate India profiles (optional)
**What:** You run `ping -c 100` and a speed test from a phone on Jio/Airtel; we fit RTT mean/jitter, loss, and rate and
update `netem_india_4g/5g`.
**Why:** PRD G5 "ideally calibrated". Without it, the report must say the profiles are modelled, not measured.

## Phase 12 - Report
**What:** Fill `Project_Report.docx` (OneDrive Desktop) with real numbers, the two figures, the capture screenshot, the
limitations list; reword PRD conclusions that the data contradicts.
**Why:** PRD deliverable 4 and G6.

## Phase 13 - Hygiene and rehearsal
**What:** Root README, a `run_all.sh` (sweep -> merge -> analyse -> plots), toolchain build script, remove `/home/abhi`
hard-coding, rehearse the demo from `Presentation.md`.
**Why:** Reproducibility and a smooth live demo.
