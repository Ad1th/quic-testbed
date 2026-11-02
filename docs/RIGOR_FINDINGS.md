# Controlled re-run: what survives when the testbed confounds are removed

_Branch `rigor/clean-rerun`, run 2026-11-02. Everything here is reproducible with `repro/` (Docker image with the exact
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
| Exit hangs | curl/ngtcp2 sometimes printed its timing line and then hung on connection close (one case: 17.5 min). Fetches are now killed after max-time+5 s and the already-printed measurement kept (`exit_hang` column). Timing data were never affected; only wall-clock run length |

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
| 50 / 1 % | 3.99* | 0.65 | | |
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

## Finding 4: curl/ngtcp2 can hang after a completed HTTP/3 transfer

One nginx-HTTP/3 transfer at 50 ms / 1 % reported a normal 4-7 s `time_total` and then did not exit for ~1050 s.
Not investigated further; reported upstream-worthy.

## Finding 5 (the main result): under equal per-packet loss most of the HTTP/3 penalty disappears

Configuration F: netem on a router namespace (bridge), endpoint offloads off, default rcvbuf. Every sender now experiences
the nominal loss (realised loss events per data packet at nominal 1/2/5 %: h2 1.01/2.20/4.91 %, nginx h3 1.05/2.05/5.02 %,
quic-go 1.06/2.16/4.89 %; 50 ms). Median completion time (s) and paired ratio vs h2 (* = significant after Bonferroni, 16 tests):

| RTT / loss | h2 A -> F | nginx h3 A -> F | nginx h3/h2 A -> F | quic-go h3/h2 F |
|---|---|---|---|---|
| 50 / 0 % | 0.57 -> 0.59 | 0.72 -> 0.73 | 1.23* -> 1.17* | 0.61* |
| 50 / 1 % | 0.94 -> 2.31 | 4.71 -> 4.82 | 3.99* -> 2.10 | 0.88 |
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

## Pending (filled in as runs complete)

- G (bridge, 4 MB rcvbuf): removes the receive-buffer confound.
- D (qlog): stall structure of nginx vs quic-go connections under 2 % loss -> mechanism.
- H (G + Cloudflare quiche as a fourth sender): does a second mature stack behave like quic-go?
