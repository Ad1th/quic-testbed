# Controlled re-run: what survives when the testbed confounds are removed

_Branch `rigor/clean-rerun`, run 2026-11-02. Canonical numbers: `paper/make_assets.py` (A excludes one sleep-adjacent transfer, which moved A 50 ms / 1 % from 3.99 to 3.54). Everything here is reproducible with `repro/` (Docker image with the exact
toolchain commits of `scripts/build_toolchain.sh`: curl 8.23.1-DEV / ngtcp2 1.26.0-DEV / nghttp3 / OpenSSL 3.6.5, nginx 1.31.9),
plus quic-go v0.64.1 as an additional, independent HTTP/3 sender._

## Why a re-run

Review of the original results raised four confounds that could each produce "HTTP/3 is 1.3-4.7x slower than HTTP/2 under loss":

1. **Concurrent experiments.** Sweeps ran as parallel shards on one 12-core host; user-space QUIC is CPU-heavy, kernel TCP is not.
2. **netem placement.** netem was attached to the endpoints' own veth devices.
3. **Client UDP receive buffer.** Default 208 KB `rmem_default`; overflow drops packets that netem never dropped.
4. **Single QUIC implementation family.** nginx (OpenSSL-compat QUIC) and aioquic are the only senders; neither is a
   widely used high-performance stack.

## Method changes (`repro/run_rigor.py`)

| Confound | Control |
|---|---|
| Concurrency | strictly serial (one transfer at a time, one container), runner/client/nginx/quic-go pinned to separate vCPUs, per-transfer client and server CPU time logged |
| netem placement | `--topology bridge`: client and server are joined through a third *router* namespace (L2 bridge); netem sits on the router's egress ports; endpoint TSO/GSO/UDP-GSO off, router GRO off. Per-transfer netem `sent`/`dropped` counters logged, so the *realised* loss is measured, not assumed |
| UDP rcvbuf | per-transfer client `Udp RcvbufErrors` logged; `--rcvbuf 4194304` condition raises `net.core.rmem_default` |
| Implementation | third sender `h3qg`: quic-go v0.64.1 HTTP/3 static file server (`repro/quicgo-server`) |
| Process hangs / host pauses | every fetch is killed after max-time+5 s (`exit_hang` column; never triggered); transfers next to a wall-clock gap > 60 s (host sleep) are excluded in analysis; later runs under `caffeinate` |
| Sender sanity | preflight: each sender must serve the object over the intended HTTP version on a clean link before measuring |

Grid for every configuration: RTT {50, 100} ms x uniform random loss {0, 1, 2, 5} % x 20 rotated-order iterations x 3 senders
(nginx HTTP/2 `h2`, nginx HTTP/3 `h3`, quic-go HTTP/3 `h3qg`), 1 MB object, 1 Gbit netem rate, 40 s cap. Statistics:
median of per-iteration paired ratios vs h2, 2000-sample bootstrap 95 % CI, Wilcoxon signed-rank, Bonferroni over all rows
of a configuration.

## Finding 1 (methodological): netem's loss rate is not the loss each protocol experiences

netem decides drop/keep per **skb** at enqueue. Linux TCP always builds GSO skbs (segmented only after the qdisc), and
quic-go batches datagrams with UDP GSO, so on a sender's own device one netem "packet" can be several wire packets. nginx's
QUIC sends one datagram per skb. Measured loss events per data packet at nominal 2 % / 5 % (50 ms RTT, 20 transfers each):

| Configuration | nominal | HTTP/2 (TCP) | nginx HTTP/3 | quic-go HTTP/3 |
|---|---|---|---|---|
| A: netem on endpoints, offloads on (= original testbed) | 2 % | 0.94 % | 1.97 % | 0.57 % |
| A | 5 % | 2.51 % | 5.01 % | 2.02 % |
| B: netem on endpoints, `ethtool -K tso/gso/gro off` | 2 % | 1.01 % | 1.83 % | 0.72 % |
| B | 5 % | 3.03 % | 4.69 % | 1.90 % |
| bridge (smoke test, 3 transfers) | 2 % | 1.6-2.5 % | 1.8-2.4 % | 1.3-2.6 % |

So in the original testbed, at "2 % loss" nginx's HTTP/3 suffered about **twice as many loss events as TCP**. Turning offloads
off with ethtool does **not** fix this (B), because TCP's GSO and UDP GSO happen above the device features ethtool controls;
only moving netem off the senders (bridge) equalises it. This applies to any netem-on-endpoint QUIC-vs-TCP comparison.

## Finding 2: client receive-buffer overflow is phantom loss that only hits non-paced QUIC

At 0 % netem loss, nginx's HTTP/3 transfers lost a median of ~180 datagrams each to client `RcvbufErrors` (A, 50 ms), while
quic-go (paced) and TCP lost none. This makes nginx HTTP/3 23-34 % *slower* than HTTP/2 at 0 % loss on this host; the original
WSL2 host showed HTTP/3 11 % *faster*, so the 0 %-loss verdict is host-dependent. This is the receiver-side bottleneck described
by Zhang et al. (WWW'24); we do not claim it as new, but it is a confound the original sweep did not log.

## Finding 3: the HTTP/3 "loss penalty" is implementation-specific, not protocol-wide

Configurations A and B (netem on endpoints), paired median ratio vs HTTP/2 (< 1 = HTTP/3 faster; * = significant after Bonferroni):

| RTT / loss | A: nginx h3 | A: quic-go h3 | B: nginx h3 | B: quic-go h3 |
|---|---|---|---|---|
| 50 / 0 % | 1.23* | 0.62* | see report_B.md | see report_B.md |
| 50 / 1 % | 3.54* | 0.65 | | |
| 50 / 2 % | 4.69* | 0.76 | | |
| 50 / 5 % | 2.50* | 0.52* | | |
| 100 / 0 % | 1.34* | 0.68* | | |
| 100 / 1 % | 4.23* | 0.85 | | |
| 100 / 2 % | 6.11* | 0.78 | | |
| 100 / 5 % | 1.88* | 0.56* | | |

The original result (nginx HTTP/3 much slower than HTTP/2 under uniform loss) **replicates** in a different environment
(Docker / Linux 6.10 / Apple M3 instead of WSL2 / x86). But a mature QUIC stack (quic-go) is never slower than TCP in any cell,
and significantly faster in 4 of 8. "HTTP/3 loses under loss" is therefore a property of the nginx sender (and aioquic), not of
QUIC. The bridge configurations (F, G) below test whether this survives equal per-packet loss.

## Finding 4 (withdrawn): "curl/ngtcp2 hang after a completed transfer"

One nginx-HTTP/3 transfer at 50 ms / 1 % reported a normal `time_total` and the next transfer started ~1050 s later. This was
first read as a curl exit hang; the exit-hang guard added afterwards never fired in ~2,500 transfers, and the gap matches a
macOS idle sleep (see Data hygiene). The transfer is excluded.

## Finding 5 (the main result): under equal per-packet loss most of the HTTP/3 penalty disappears

Configuration F: netem on a router namespace (bridge), endpoint offloads off, default rcvbuf. Every sender now experiences
the nominal loss (realised loss events per data packet at nominal 1/2/5 %: h2 1.01/2.20/4.91 %, nginx h3 1.05/2.05/5.02 %,
quic-go 1.06/2.16/4.89 %; 50 ms). Median completion time (s) and paired ratio vs h2 (* = significant after Bonferroni, 16 tests):

| RTT / loss | h2 A -> F | nginx h3 A -> F | nginx h3/h2 A -> F | quic-go h3/h2 F |
|---|---|---|---|---|
| 50 / 0 % | 0.57 -> 0.59 | 0.72 -> 0.73 | 1.23* -> 1.17* | 0.61* |
| 50 / 1 % | 0.94 -> 2.31 | 4.71 -> 4.82 | 3.54* -> 2.10 | 0.88 |
| 50 / 2 % | 1.50 -> 4.65 | 7.28 -> 7.38 | 4.69* -> **1.55*** | 0.61* |
| 50 / 5 % | 4.47 -> 10.50 | 11.70 -> 11.06 | 2.50* -> **1.08** | 0.50* |
| 100 / 0 % | 0.96 -> 0.97 | 1.42 -> 1.31 | 1.34* -> 1.36* | 0.70* |
| 100 / 1 % | - -> 4.17 | - -> 8.43 | 4.23* -> 1.99* | 0.76 |
| 100 / 2 % | - -> 6.37 | - -> 12.89 | 6.11* -> 2.02* | 0.50* |
| 100 / 5 % | - -> 18.67 | - -> 19.97 | 1.88* -> 1.10 | 0.59* |

Reading:
- **nginx HTTP/3 times barely change between A and F; HTTP/2 times grow 2-3x.** The original penalty was mostly TCP being
  given half the loss, not QUIC being slow.
- What remains for nginx is a 1.1-2.1x deficit (largest at 1-2 %, not significant at 5 %).
- quic-go HTTP/3 is faster than kernel-TCP HTTP/2 in all 8 cells (0.50-0.88x; significant in 6 of 8).
- The verdict "HTTP/3 loses under loss" is therefore a property of (a) where netem sits and (b) nginx's QUIC sender.
- 0 failures, 0 exit hangs in F. nginx h3 still had 7,673 client RcvbufErrors over its 160 transfers (quic-go 12): see G.

## Finding 6: with the receive buffer fixed too (G), the 0 %-loss result of the course report replicates

Configuration G = F + 4 MB client UDP rcvbuf. Zero RcvbufErrors, zero failures, zero exit hangs (480 transfers).

| RTT / loss | h2 (s) | nginx h3 (s) | quic-go h3 (s) | nginx h3/h2 | quic-go h3/h2 |
|---|---|---|---|---|---|
| 50 / 0 % | 0.55 | 0.47 | 0.35 | **0.85*** | 0.63* |
| 50 / 1 % | 1.62 | 4.58 | 1.19 | 2.72* | 0.70 |
| 50 / 2 % | 4.29 | 6.86 | 2.86 | 1.63* | 0.62 (p_bonf 0.07) |
| 50 / 5 % | 9.58 | 11.19 | 6.03 | 1.15* | 0.57* |
| 100 / 0 % | 0.99 | 0.87 | 0.69 | **0.87*** | 0.69* |
| 100 / 1 % | 4.44 | 8.14 | 2.70 | 2.07* | 0.77 |
| 100 / 2 % | 7.72 | 12.95 | 5.39 | 1.60* | 0.64 (p_bonf 0.08) |
| 100 / 5 % | 17.04 | 20.40 | 10.38 | 1.23 | 0.59* |

- At 0 % loss nginx HTTP/3 is now 13-15 % faster than HTTP/2, matching the course report's "~11 % faster" (the 1-RTT handshake
  saving). In F/A it was 17-36 % *slower*: the difference is entirely the client receive-buffer overflow.
- CPU per transfer is small for every sender (median client 0.016-0.022 s, server 0.01-0.02 s per 1 MB at 0 % loss), so
  in serial runs CPU is not the bottleneck at these rates.

## Finding 7 (mechanism, qlog run D at 50 ms / 2 %, G settings, 10 transfers per QUIC sender)

- Neither QUIC sender shows receive stalls > 150 ms at the client (no PTO-driven idle periods); quic-go's server qlog shows
  0-7 PTO expiries and 12-23 declared losses per connection.
- What differs is the **steady sending rate**: the client receives a median of **4.0 packets per 50 ms RTT from nginx** vs
  **11.5 from quic-go**, whose server-side congestion window has a time-weighted median of **13.9 packets**. A Reno/CUBIC
  AIMD sender in the TCP-friendly region at p = 2 % is expected near 1.22/sqrt(p) ~ 8.6 packets. nginx runs at less than half of
  that, i.e. its window is held below what its own CUBIC implementation should reach.
- Candidate cause (from source, `src/event/quic/ngx_event_quic_ack.c`, `ngx_quic_congestion_lost`): on each congestion event
  nginx sets `ssthresh = in_flight * 0.7`, computed after the lost packet (and already-acked packets) have been subtracted
  from `in_flight`, instead of reducing from the congestion window as in RFC 9438 Sec. 4.6. If the sender is not fully
  window-limited at that moment, every loss shrinks the window by more than the 30 % CUBIC intends.
- **Intervention test (P), below.**

## Finding 8 (root cause, intervention): one line in nginx's loss handler accounts for most of the remaining penalty

Configuration P = G with nginx rebuilt from the same commit with **only** `ssthresh = in_flight * 0.7` changed to
`ssthresh = window * 0.7` in `ngx_quic_congestion_lost` (`repro/Dockerfile.nginxpatch`). 3 transfers adjacent to host sleep
excluded (see "Data hygiene").

| RTT / loss | nginx h3 stock (G), s | nginx h3 patched (P), s | speed-up | nginx h3/h2 G | nginx h3/h2 P |
|---|---|---|---|---|---|
| 50 / 0 % | 0.47 | 0.47 | 1.00 | 0.85* | 0.81* |
| 50 / 1 % | 4.58 | 2.05 | 2.2x | 2.72* | 1.31 (n.s.) |
| 50 / 2 % | 6.86 | 3.77 | 1.8x | 1.63* | 0.84 (n.s.) |
| 50 / 5 % | 11.19 | 6.73 | 1.7x | 1.15* | **0.64*** |
| 100 / 0 % | 0.87 | 0.88 | 0.99 | 0.87* | 0.87* |
| 100 / 1 % | 8.14 | 1.81 | 4.5x | 2.07* | 0.66 (n.s.) |
| 100 / 2 % | 12.95 | 4.31 | 3.0x | 1.60* | **0.65*** |
| 100 / 5 % | 20.40 | 13.73 | 1.5x | 1.23 | 0.87 (p_bonf 0.08) |

- Loss-free performance is unchanged (the patch only touches the congestion-event path), lossy performance improves
  1.5-4.5x. Stock nginx is significantly slower than HTTP/2 in 5 of 6 lossy cells; patched nginx in **none**, and
  significantly faster in 2.
- Cross-run absolute times drift (HTTP/2 medians in P are 0-60 % above G at 1 %, where TCP's completion time is bimodal),
  which is why the within-run paired ratios are the primary metric; both metrics agree.
- **How to describe it precisely.** RFC 9438 Sec. 4.6 itself defines the reduction from `flight_size` (bytes outstanding) and
  allows `cwnd` only with safeguards against growing the window while application-limited. So using bytes in flight is
  not by itself non-compliant. The problem is *when* nginx reads it: `ngx_quic_congestion_lost` runs after the ACK's
  newly-acknowledged packets and the lost packet itself have already been subtracted from `in_flight`, so the value is
  smaller than the flight size at the congestion event and each loss cuts the window by more than beta. Our patch
  (use `window`) is a mechanism test, not a proposed upstream fix as-is (it lacks the RFC's app-limited safeguard).
  A proper fix would snapshot the flight size before the ACK is processed. Worth reporting to nginx with this data.

## Data hygiene

- Host sleep: the Mac idle-slept three times during unattended runs (macOS `pmset` log: DarkWake from Deep Idle), freezing the
  Docker VM between transfers. Analysis and plots drop any transfer whose wall-clock gap to the previous transfer of the same
  run exceeds its own duration by > 60 s (A: 1 transfer, which is also the "17-minute curl hang" first attributed to curl;
  P: 3 transfers). Later runs used `caffeinate`. The exit-hang guard never fired, so the curl-hang note in Finding 4 is
  withdrawn: it was host sleep.

## Finding 9: a second mature QUIC stack (Cloudflare quiche 0.29.3) also beats or matches TCP under equal loss

Configuration H = G conditions with four senders in the same run (634 transfers after excluding 6 next to host sleep;
0 failures, 0 RcvbufErrors). Paired ratio vs HTTP/2 (* = significant after Bonferroni over 24 tests):

| RTT / loss | h2 (s) | nginx h3 | quic-go h3 | quiche h3 |
|---|---|---|---|---|
| 50 / 0 % | 0.60 | 0.79* | 0.60* | 0.84* |
| 50 / 1 % | 2.28 | 1.86* | 0.61 | 0.97 |
| 50 / 2 % | 4.32 | 1.49* | 0.62* | 0.84 |
| 50 / 5 % | 10.16 | 1.22 | 0.58* | 0.78* |
| 100 / 0 % | 0.96 | 0.89* | 0.70* | 0.89 |
| 100 / 1 % | 2.42 | 2.62* | 0.94 | 1.01 |
| 100 / 2 % | 7.02 | 1.51* | 0.79 | 0.85 |
| 100 / 5 % | 19.21 | 1.09 | 0.54* | 0.70* |

- quiche is never significantly slower than kernel TCP (0.70-1.01x) and significantly faster in 3 of 8 cells; quic-go
  (0.54-0.94x) is significantly faster in 5 of 8 and never slower.
- Stock nginx repeats its G pattern inside the same run (slower at 1-2 %, faster at 0 %), so the nginx result is not an
  artefact of run-to-run drift.
- Conclusion across F, G, H, P: **under equal per-packet loss, the HTTP/3 "loss penalty" is specific to stock nginx's QUIC
  sender; two independent mature stacks and a one-line-patched nginx do not show it.**

## Figures (`data/rigor/figs/`)

- `loss/fig_realised_loss.png`: realised loss events per data packet vs nominal, per sender, A / B / F.
- `main/fig_ratio.png`: paired h3/h2 ratios with 95 % CI per sender across A, F, G, P, H.
- `main/fig_cdf_50ms_2pct.png`: completion-time CDFs at 50 ms / 2 % across A, F, G, P, H.

## Limitations of this re-run

- One host type (Docker Desktop VM, Linux 6.10, Apple M3); not bare metal. The original WSL2 host was not re-run.
- 1 MB objects only, uniform random loss only, two RTTs, 1 Gbit netem rate (no bottleneck queue), TCP CUBIC only.
- Client is always curl/ngtcp2; client-side effects (ACK frequency, flow control) were not varied.
- Configurations ran sequentially over ~20 hours, so cross-configuration comparisons of absolute times include drift;
  within-run paired ratios are the primary metric.
