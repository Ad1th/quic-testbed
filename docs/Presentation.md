# Presentation plan (STAR) - ~12 minutes + demo

## S - Situation (1-2 min)
- HTTP/3 over QUIC is now ~30 % of web traffic; it replaces TCP with UDP-based transport, promising faster
  handshakes and no head-of-line blocking on lossy links.
- Claim you hear everywhere: "HTTP/3 is better on bad networks, especially mobile." But **where exactly** does
  it stop being better? Most papers test a few hand-picked conditions on real cloud links - not reproducible.

## T - Task (1 min)
- Build a **reproducible, rootless testbed** on a single laptop that can sweep latency and loss and
  **locate the HTTP/2-vs-HTTP/3 crossover boundary**, including realistic Indian mobile profiles.

## A - Action (4-5 min)
1. Built the entire stack from source (OpenSSL-QUIC, ngtcp2, nghttp3, curl, nginx) because distro curl/nginx have no h3.
2. Network namespaces + veth + `tc netem` = virtual client/server with controllable RTT, loss, bandwidth.
   No sudo, no second machine (show Architecture.md diagram).
3. Automated runner: 28 conditions x 20 iterations x 2 protocols = 1120 measurements, alternating order,
   timeouts counted as 40 s (no cherry-picking), parallelised across 5 shards.
4. Analysis: medians, paired win-rates, interpolated crossover points.
5. Found and fixed a methodology artefact: without a rate cap, QUIC bursts overflowed the UDP receive buffer
   and created phantom loss only for h3 - a good "I validated my tool" story.

## R - Result (3 min)  [numbers from data/processed/significance.csv; refresh after final data]
- **0 % loss:** h3 consistently ~11 % faster, statistically significant at every RTT (handshake saving).
- **0.5-1 % uniform loss:** no clear winner - differences are not significant in most cells.
- **>= 2 % uniform loss:** h2 faster in all 18 cells (paired median ratio 1.3x-4.7x, ratio-of-medians up to 7.2x; 14 of 18 significant after correction), contrary to the common claim.
- **Why (diagnostics):** the penalty appears only when *data* packets are lost (ACK-only loss: h3 still faster);
  it is not nginx-specific (an independent aioquic server is just as slow); TCP congestion control (cubic vs reno)
  explains only part of it. Mechanism not fully isolated - say so.
- **Mobile profiles (Airtel-calibrated):** h3 faster - India 4G 0.79x, 5G 0.62x, congested 4G 0.77x; 95 % bootstrap CIs
  exclude 1, but none survive Bonferroni over 39 tests, so say "consistent trend", not "proven". (Before recalibration,
  India 4G's CI was 0.53-1.09, i.e. not even that.)
- Takeaway: *the h3-vs-h2 outcome depends on the loss pattern and where the packets are lost, not just the loss rate.*

## Why it is novel / what's the contribution
- A fully reproducible, **rootless** methodology (anyone can rerun with one command, no lab hardware).
- Fine-grained **crossover map** (RTT x loss) rather than single-point comparisons.
- Includes **India-specific mobile profiles** with Gilbert-Elliott burst loss, rarely covered in literature.
- Honest handling of failures (right-censoring) and measurement artefacts.
- Be honest: the novelty is methodology + the loss-pattern finding, not a new protocol. (Finish the TODO items
  - plots, explanation of h3 slowness - to make this claim strong.)

## Live demo (run from `~/quic-testbed`)

```bash
# 1. Show the toolchain really supports h3
~/.local/bin/curl -V | head -2
~/.local/nginx/sbin/nginx -V 2>&1 | head -3

# 2. Show project layout
tree -L 2 -I 'build' . || find . -maxdepth 2 | sort

# 3. Live mini-experiment (~10 s): 0% loss, 50 ms RTT, 3 iterations, h2 vs h3
scripts/testbed.sh python3 scripts/run_tests.py --out /tmp/demo.csv \
    --iterations 3 --rtts 50 --losses 0 --profiles static
column -s, -t /tmp/demo.csv | cut -c1-140

# 4. Same, with 2% loss - watch h3 get slower (~20 s)
scripts/testbed.sh python3 scripts/run_tests.py --out /tmp/demo_loss.csv \
    --iterations 3 --rtts 50 --losses 2 --profiles static

# 5. Mobile profile (India 4G), takes ~15 s
scripts/testbed.sh python3 scripts/run_tests.py --out /tmp/demo4g.csv --iterations 5 --profiles india_4g

# 6. Show the full-sweep analysis (no rerun needed; sweep took hours)
wc -l data/raw/results.csv
python3 scripts/analyze_crossover.py
cat data/processed/crossover_report.txt

# 7. (optional) Prove netem is doing its job
scripts/testbed.sh bash -c 'source scripts/netem.sh; netem_static 100 1; \
    ip netns exec client tc qdisc show dev veth-c; ip netns exec client ping -c3 10.0.0.2'
```
Tip: step 3's output shows `http_version` = 2 vs 3, proving each protocol was really used. Rehearse once
before the meeting; WSL must have `sch_netem` loaded (`sudo modprobe sch_netem`).
Note: step 6 overwrites `data/processed/*` with identical output - harmless.

## Likely questions from the professor
| Question | Answer |
|---|---|
| Why is h3 slower under loss - bug? | Tested: not curl-specific (aioquic client same), not nginx-specific (aioquic server same), only when data packets are lost, TCP cubic->reno explains part. Remaining: loss-recovery details (SACK/RACK vs PTO). |
| Is emulation valid? | Controlled & repeatable, but not real internet; limitation stated. |
| Why 20 iterations? | Medians + paired comparison; bootstrap CIs and Wilcoxon (Bonferroni) in scripts/stats_significance.py. |
| Why median not mean? | Heavy tails from timeouts/retransmits. |
| Why single stream? | Isolates transport behaviour; multi-stream HOL-blocking test is future work. |

## Suggested slide order
Title -> Problem -> Architecture diagram -> Method (grid + profiles) -> Heatmap (TODO: make it) -> Mobile result table
-> Insight (loss pattern) -> Live demo -> Limitations & future work.
