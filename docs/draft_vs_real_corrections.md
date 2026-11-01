# Draft claims vs real data: corrections

_Source of draft text: `Computer Networks Lab Submission 9.pdf` (page numbers below). Real numbers: `data/raw/results.csv`
(1560 rows), `data/processed/{medians,crossover_table,significance}.csv`, `data/raw/results_10MB.csv`.
All draft result values are placeholders; every row below is flagged **REWRITE** unless marked **KEEP**._

Medians are of per-request `total_s` (timeouts counted at the 40 s cap). "ratio" = h3 time / h2 time (below 1 = HTTP/3 faster).
"Significant" = 95 % bootstrap CI excludes 1 **and** Wilcoxon p < 0.05 after Bonferroni over all cells.

## A. Claims the real data contradicts

| # | Draft sentence (page) | Real number from your data | Action |
|---|---|---|---|
| 1 | "HTTP/3 was faster in most conditions, and the gap grew with RTT (about 22 % faster at 300 ms)." (p7) | Static grid: HTTP/3 faster in **8 of 36** cells, HTTP/2 faster in 27, 1 tie. At 300 ms and 0 % loss HTTP/3 is **11.0 %** faster (2.706 s vs 2.409 s, ratio 0.89). The relative gain is flat (0.89-0.91) at every RTT; only the absolute gap grows (0.017 s at 20 ms, 0.30 s at 300 ms). | REWRITE |
| 2 | "Under packet loss of 2 % and above, HTTP/3 completed 25-30 % faster because there is no head-of-line blocking." (p7) | **0 of 18** cells with loss >= 2 % were won by HTTP/3. HTTP/2 was faster in all 18, HTTP/3 taking **1.31x to 7.18x** as long (e.g. 50 ms/5 %: 6.00 s vs 10.01 s). 14 of 18 are significant after correction (the other 4 have a CI that excludes 1 but miss the corrected p threshold). Ratios are ratio-of-medians; the paired median ratio runs 1.3x-4.7x. | REWRITE (reverses the finding) |
| 3 | "Crossover point: below ~30 ms RTT with under 0.5 % loss and high bandwidth, HTTP/2 matched or slightly beat HTTP/3." (p7) | At 20 ms and **0 % loss HTTP/3 is faster** (0.186 vs 0.169 s, ratio 0.91, significant). HTTP/2 only wins once loss > 0. No RTT threshold exists: HTTP/3 wins at 0 % loss at all six RTTs. No cell was tested between 0 % and 0.5 %. | REWRITE |
| 4 | "On the India 4G profile, HTTP/3 was about 23 % faster." (p7) | Median completion 1.453 s (h2) vs 0.965 s (h3), ratio 0.66. Paired median ratio 0.79 (95 % CI 0.66-0.98, Wilcoxon p = 0.049 uncorrected). **Not significant after Bonferroni** (p = 1.0 over 39 tests). Loss in this profile is modeled, not measured. | REWRITE; say "consistent trend", not proven |
| 5 | "Only HTTP/3 survived the simulated network switch." (p7) and "the HTTP/3 transfer continued after the client IP change, while the HTTP/2 transfer failed" (p6) | **Now measured** (`migration.csv`): HTTP/2 survived 0/8; curl HTTP/3 0/8 (client limitation); aioquic HTTP/3 survived 6/8 (2 unexplained timeouts). So "only HTTP/3 survived" is roughly true for a migration-capable client but must carry the 6/8 and the curl caveat. | REWRITE with these numbers |
| 6 | "Loss-burst recovery: HTTP/3 recovered in ~0.4 s versus ~0.9 s for HTTP/2." (p6) | **Now measured** (`blackout.csv`, 10 MB, 50 ms, 20 Mbit): 1 s outage adds +1.71 s (h2) vs +2.56 s (h3); 2 s: +3.10 vs +5.32; 4 s: +5.98 vs +5.27. HTTP/3 did **not** recover faster except at 4 s. | REWRITE with these numbers |
| 7 | "QUIC performs better on high-latency, lossy and changing networks ... TCP remains competitive only on fast, clean, low-latency links." (Conclusion, p7) | Reverse for uniform loss: HTTP/3 wins only on **loss-free** links (all RTTs, ~11 %) and on the three bandwidth-limited mobile profiles (4G 0.66, 5G 0.59, congested 4G 0.95). HTTP/2 wins at >= 2 % uniform loss (18/18 cells, 14 significant) and in all 9 ten-MB cells, including 0 % loss (1.13x-1.23x). | REWRITE |
| 8 | "QUIC used more CPU than TCP because it runs in user space, which explains its small loss on the high-bandwidth 5G profile." (p6) | CPU was **never measured**. And HTTP/3 did **not** lose on India 5G: 1.328 s vs 0.781 s, ratio 0.59, HTTP/3 won 85 % of paired iterations. (CPU cost is only a hypothesis for the 10 MB result, where HTTP/2 won at 0 % loss.) | REMOVE / REWRITE |
| 9 | "Disabling NIC offloads and pinning processes to fixed CPU cores reduced variance." (p6) | Not done. `grep` for ethtool / taskset / affinity in `scripts/` and `conf/` finds nothing. | REMOVE |
| 10 | "Results at low RTT varied by up to 15 % between runs, so 20 repetitions and medians were used." (p6) | At 20 ms / 0 %: HTTP/2 spread (max-min)/median = 2.4 %, CV 0.5 %; HTTP/3 has one large outlier (spread 147 %, CV 30 %). Neither supports "15 %" cleanly. | REWRITE with the measured spread, or drop the number |
| 11 | "The sweep completed 50 static conditions and 3 mobile profiles, with 20 runs per protocol per condition (2,120 runs in total)." (p6) and "across 50+ network conditions" (p7) | **36 static cells** (6 RTT x 6 loss) + 3 profiles, 20 runs per protocol per cell = **1,560 runs** (plus 180 ten-MB runs and side experiments). | REWRITE |
| 12 | The "illustrative values" table (p6) | See section B. Every cell differs, and two winners flip. | REPLACE |

## B. Replacement for the draft's results table (1 MB, median completion time)

| Condition | Draft HTTP/2 / HTTP/3 (placeholder) | **Real HTTP/2 (s)** | **Real HTTP/3 (s)** | Real ratio | Real winner |
|---|---|---|---|---|---|
| 20 ms, 0 % | 0.21 / 0.19 | 0.186 | 0.169 | 0.91 | HTTP/3 (significant) |
| 100 ms, 0 % | 0.68 / 0.55 | 0.906 | 0.808 | 0.89 | HTTP/3 (significant) |
| 300 ms, 0 % | 1.92 / 1.49 | 2.706 | 2.409 | 0.89 | HTTP/3 (significant) |
| 50 ms, 5 % | 1.35 / 0.94, "HTTP/3" | 6.000 | 10.009 | 1.67 | **HTTP/2** (significant) |
| India 4G (50 ms, bursty ~1 %, 22 Mbit) | 2.10 / 1.62 | 1.453 | 0.965 | 0.66 | HTTP/3 (trend; not significant after correction) |
| India 5G (48 ms, 0.3 %, 35 Mbit) | 0.31 / 0.34, "HTTP/2" | 1.328 | 0.781 | 0.59 | **HTTP/3** (trend; not significant after correction) |

## C. Claims the real data supports (can be kept, with real numbers)

| Draft sentence | Real support | Action |
|---|---|---|
| "Handshake time: HTTP/3 took about 1 RTT versus 2 RTT for HTTP/2 + TLS 1.3." (p6) | `handshake_s` h3/h2 = 0.50-0.53 at every 0 %-loss RTT. Example, 300 ms: 0.303 s vs 0.603 s. Capture at 100 ms: h2 0.218 s vs h3 0.111 s; first request at ~203 ms (h2) vs ~102 ms (h3). | **KEEP**, add numbers |
| TC1 expected "QUIC faster handshake"; TC2 expected "QUIC faster due to 1-RTT handshake" | Handshake 0.043 vs 0.023 s (20 ms) and 0.603 vs 0.303 s (300 ms); total time 9-11 % better | KEEP |
| TC3 "Compare recovery behaviour" | HTTP/2 1.98x faster at 100 ms / 5 % | Fill in real result |

## D. Smaller statements that no longer match the real setup

| Draft statement | Real | Action |
|---|---|---|
| "Client / test runner module: Python script calling curl and aioquic" (p5) | `run_tests.py` calls **curl only**; aioquic was a separate cross-check | REWRITE |
| "Capture module: tcpdump/Wireshark with SSLKEYLOGFILE" (p5) | tcpdump could not run in the rootless namespace; a custom `pcap_capture.py` was used; decryption not yet verified | REWRITE |
| "Wireshark ... used to decrypt and inspect QUIC handshakes" (p5) | Pcaps and keylog captured; not yet opened in Wireshark | Keep only after the screenshot exists |
| Novelty: "locating the exact crossover point between QUIC and TCP" (p7) | The crossover is "any uniform loss > 0 %" along the loss axis, not an RTT/loss point | REWRITE |
| "Hardware: Laptop/PC, 8 GB RAM" (p5) | i5-11400H, 12 threads, 7.6 GiB RAM visible to WSL2 | Update (see `reusable_from_draft.md`) |

## E. New findings the draft does not mention (worth adding)

- HTTP/3's penalty appears only when **data** packets are lost: with loss on the ACK direction only, HTTP/3 (0.45 s) beat HTTP/2 (0.51 s); data-only loss: 5.55 s vs 1.88 s.
- It is **not** specific to curl or nginx (an aioquic client and an aioquic server behave the same); switching TCP from CUBIC to Reno slows HTTP/2 only at 100 ms (4.05 -> 6.21 s), so congestion control is a partial factor at best.
- 10 MB downloads: HTTP/2 faster in all 9 cells (significant), even at 0 % loss.
- The India RTT/jitter/bandwidth values are measured (Airtel, 28 Oct 2026); the loss component is modeled.
