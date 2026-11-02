# Paper plan (draft, 2026-11-02)

Status: the controlled re-run (`docs/RIGOR_FINDINGS.md`) changed the story. The course-report claim ("HTTP/3 is 1.3-4.7x slower
than HTTP/2 under >= 2 % loss") does not hold as a protocol result. What holds is stronger and more publishable:

## Working title
**"Equal Loss Is Not Equal: How Emulator Placement and Implementation Choice Flip HTTP/2-vs-HTTP/3 Verdicts"**
(alt: "Why HTTP/3 Lost to HTTP/2 in Our Testbed: Two Emulation Pitfalls and a One-Line Congestion-Control Bug")

## Status (2026-11-02)
Done: A, B, F, G, D, P, H (about 3,300 serial transfers; quiche added as a 4th sender, behaves like quic-go).
The full narrative now exists: artifact -> confound -> implementation -> root cause -> intervention.

## Claims (each backed by a configuration in `data/rigor/`)
1. **netem on an endpoint does not apply the configured loss rate equally to TCP and QUIC.** Because netem drops per skb, and
   Linux TCP (always-GSO) and GSO-batching QUIC stacks (quic-go) hand it multi-packet skbs, they see ~40-60 % of the nominal
   loss events, while non-batching QUIC senders (nginx) see ~100 %. `ethtool` offload settings do not fix it; placing netem on a
   separate forwarding namespace does. (A vs B vs F; per-transfer netem counters.)
2. **That artifact accounts for most of the reported HTTP/3 loss penalty.** At 50 ms / 2 %, nginx-h3/h2 drops from 4.69x
   (netem on endpoints) to 1.55x (equal per-packet loss); at 5 % from 2.50x to 1.08x (not significant). HTTP/2 gets 2-3x slower
   once it stops receiving half the loss; nginx HTTP/3 is unchanged.
3. **Under equal loss, the verdict depends on the QUIC implementation, not the protocol.** quic-go HTTP/3 is faster than kernel
   TCP HTTP/2 in every cell (0.5-0.9x); nginx HTTP/3 is slower (1.1-2.1x). (F, G; mechanism from qlog in D.)
4. **Client receive-buffer overflow is a second, host-dependent confound** that only hits unpaced QUIC senders and flips the
   0 %-loss verdict between hosts. (A at 0 %: ~180 RcvbufErrors per nginx-h3 transfer; G removes it and nginx h3 becomes
   13-15 % faster than h2, reproducing the course report's 0 % result.)
5. **The residual nginx penalty has a one-line root cause, confirmed by intervention.** nginx's CUBIC reads bytes-in-flight
   for the multiplicative decrease after the ACK's acked and lost packets have been subtracted, so each loss cuts more than
   beta. qlog shows nginx holding ~4 packets/RTT vs quic-go's ~12 at 2 % loss. Rebuilding the same commit with the reduction
   taken from the window makes nginx 1.5-4.5x faster under loss with no change at 0 %, and removes every significant
   HTTP/3 deficit vs HTTP/2. (D, P.) -> report upstream to nginx with a proper fix (snapshot flight size before ACK processing).

## What is NOT claimed (and why)
- Not "QUIC beats TCP" in general: two mature stacks (quic-go, quiche) vs one kernel TCP (CUBIC), one object size, one host.
  The defensible statement is "no HTTP/3 loss penalty for mature stacks under equal loss in this setup".
- Not India-specific results: the original India profiles have modeled loss and are not significant; drop them from the paper or
  keep as a short "realistic-profile" sanity section with the caveat. (Real on-device runs would be a separate paper.)
- Not the receiver-side throughput bottleneck: Zhang et al. WWW'24 (cite).
- Blackout and migration results (n=8, client-limited): leave out or one sentence in discussion.

## Structure (6 pages, IEEE two-column)
1. Introduction - conflicting QUIC-vs-TCP verdicts in the literature; we show two testbed choices that can flip them.
2. Background - netem enqueue-time drops, GSO/TSO, UDP GSO, RFC 9002 vs Linux TCP recovery.
3. Testbed - three namespaces, pinned toolchain, serial runs, per-transfer kernel counters, Docker artifact.
4. Pitfall 1: netem placement (Fig: realised loss-event rate per sender, A/B/F; Fig: h3/h2 ratio A vs F).
5. Pitfall 2: receiver buffer (Fig: RcvbufErrors vs sender; 0 % verdict F vs G).
6. Implementation dependence under equal loss (Fig: completion-time CDFs, three/four senders; qlog delivery rate per RTT).
6b. Root cause and intervention (code excerpt of `ngx_quic_congestion_lost`; Table: stock vs patched nginx; Fig: ratio
   shift G -> P).
7. Related work (docs/related_work_verified.md) - closest: Jaeger et al. IFIP Networking'23 (offloads/buffers for throughput),
   Yu & Benson WWW'21, Marx et al. EPIQ'20, Zhang et al. WWW'24. Delta: we quantify how emulator placement biases *loss*
   comparisons, which none of them do (verify by reading B2/B4 in full before submitting).
8. Recommendations checklist for QUIC-vs-TCP emulation studies.
9. Limitations - single host (Docker VM on Apple M3), 1 MB objects, uniform loss, two RTTs, one TCP CC (CUBIC).

## Experiments still worth adding (in priority order)
1. ~~One more mature QUIC sender~~ done (quiche, config H).
1b. **Proper nginx fix** (snapshot flight size before ACK processing, keep RFC 9438 app-limited safeguard), re-run P with it,
    and send it upstream with the data. Strongest single addition: turns a finding into a merged fix.
2. **More RTT/loss cells under G** (20, 200 ms; 0.5, 3 %) for the figure, and 10 MB objects. ~half a day of machine time.
3. **Bare-metal Linux replication** of A vs F (any spare Linux laptop): removes "it's a Docker VM" objection. ~half a day.
4. **Original WSL2 host replication of A vs F** by Abhilash - closes the loop with the course data.
5. BBR on TCP and quic-go (if exposed) - optional.

## Venues (verify dates; none of the 2027 calls were published when checked)
- IEEE LCN (historically April deadline), IFIP Networking (IEEE co-sponsored; historically Jan-Mar),
  IEEE ICC workshops, COMSNETS (IEEE, Bengaluru; historically ~Aug-Sep), ANRW (ACM/IRTF, good fit for measurement methodology).
- A methodology/pitfalls paper fits ANRW or an IFIP Networking short paper very well.

## Authorship and integrity (do first)
- Abhilash owns the project: he decides whether this becomes a paper and leads it.
- The submitted lab draft (`Computer Networks Lab Submission 9.pdf`) contains illustrative numbers that contradict the data; send
  the instructor the real-results report as a correction. Nothing from that draft goes into the paper.
