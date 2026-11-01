# Reusable content from the draft (no result values)

_Taken from `Computer Networks Lab Submission 9.pdf`. Each block says what to keep and what no longer matches the real setup.
Environment facts were read from the machine on 2026-10-28 (`nginx -V`, `curl --version`, `uname -r`, `lsb_release`, `nproc`, `free`)._

## 1. Hardware and software requirements (section 9a)

| Item | Draft says | Real environment | Match? |
|---|---|---|---|
| Hardware | "Laptop/PC, 8 GB RAM, multi-core CPU" | Intel Core i5-11400H @ 2.70 GHz, 12 logical CPUs; 7.6 GiB RAM visible inside WSL2 | Update with specifics |
| OS | "Ubuntu 22.04+" | Ubuntu 22.04.5 LTS under **WSL2** on Windows, kernel `6.6.87.2-microsoft-standard-WSL2` | Add "WSL2" and kernel |
| Web server | "Nginx 1.25+ (HTTP/3)" | nginx **1.31.9**, built from source: `--with-http_ssl_module --with-http_v3_module --with-http_v2_module --with-openssl=~/build/openssl`, gcc 11.4.0 | Update version + flags |
| TLS library | not stated | OpenSSL **3.6.5** (QUIC API), built from source | Add |
| curl | "curl with HTTP/3" | curl **8.23.1-DEV** with OpenSSL 3.6.5, nghttp2 1.71.0-DEV, ngtcp2 1.26.0-DEV, nghttp3 1.1.x (version string was cut off in my output; read it before quoting) | Add versions |
| Python | "Python 3 with aioquic, pandas, matplotlib" | Python 3.10.12; pandas 2.3.3, numpy 2.2.6, matplotlib 3.10.9, scipy 1.15.3, aioquic 1.3.0 | OK, but aioquic is only used for cross-checks |
| Network emulation | "iproute2 (tc netem)" | iproute2 5.15.0; `tc netem` on a veth pair between two network namespaces, created rootless via `unshare -Urnm` | Add "rootless user namespace" |
| Capture | "Wireshark" (and "tcpdump/Wireshark" in modules) | Wireshark 3.6.2 GUI installed, **no `tshark`**; **tcpdump fails in the rootless namespace** (cannot drop privileges), so `scripts/pcap_capture.py` (AF_PACKET) writes the pcaps | Must change |
| Test files | "1 MB, 10 MB" | `~/srv/content/1MB.bin`, `10MB.bin`; self-signed certificate for 10.0.0.2 | OK |

## 2. Module descriptions (section 8) - reusable with small edits

- **Server module** - Nginx configured for HTTP/2 (TCP 443) and HTTP/3 (UDP 443) with TLS 1.3 and the two test files. *Keep.* (Real file: `conf/nginx.conf`, listening on 10.0.0.2.)
- **Network emulation module** - `tc netem` scripts for the RTT x loss matrix and the Indian mobile profiles. *Keep; add:* delay is applied per direction on both ends (RTT = 2x), a 1 Gbit rate cap is used on static cells, India 4G uses a Gilbert-Elliott burst-loss model. (Real file: `scripts/netem.sh`.)
- **Client / test runner module** - "Python script calling curl and aioquic, recording timing metrics." *Change to:* a Python runner calls curl (`--http2` / `--http3-only`) inside the client namespace and records connect, handshake, TTFB, total time and throughput; aioquic is used separately as a cross-check client/server. (Real files: `scripts/run_tests.py`, `aioquic_client.py`, `aioquic_server.py`.)
- **Capture module** - "tcpdump/Wireshark with SSLKEYLOGFILE for QUIC decryption." *Change to:* a raw-socket pcap writer in the client namespace plus `SSLKEYLOGFILE`, opened in Wireshark. (Real files: `scripts/capture_handshake.sh`, `pcap_capture.py`.)
- **Analysis module** - "pandas/matplotlib aggregation, graphs and crossover detection." *Keep; add* bootstrap confidence intervals and a Wilcoxon test. (Real files: `scripts/analyze_crossover.py`, `stats_significance.py`.)

## 3. Test-case IDs and intent (section 9b) - IDs and intent are reusable; the "Expected" column is a hypothesis, not a result

| ID | Condition | Intent (reusable) | Draft "Expected" | Status |
|---|---|---|---|---|
| TC1 | 20 ms RTT, 0 % loss | Baseline on a fast, clean link | Both similar; QUIC faster handshake | Covered; handshake expectation held |
| TC2 | 300 ms RTT, 0 % loss | Effect of handshake round trips at high RTT | QUIC faster due to 1-RTT handshake | Covered; held (~11 %) |
| TC3 | 100 ms RTT, 5 % loss | Compare recovery behaviour under heavy loss | Compare recovery behaviour | Covered; HTTP/2 faster |
| TC4 | India 4G profile + IP switch | Connection migration on a mobile profile | QUIC connection survives migration | **Not run** |

Label the "Expected" column "Hypothesis" in the report and add an "Observed" column from `draft_vs_real_corrections.md`.

## 4. Introduction, problem statement and objectives (sections 1-3)

Reusable as written, except the measurement objective: say "measure ... loss-burst recovery time and connection migration"
only if those two get real data (see `coverage_and_skip_plan.md`). The RTT/loss ranges (20-300 ms, 0-5 %) match the real
grid (RTT 20/50/100/150/200/300 ms, loss 0/0.5/1/2/3/5 %).

## 5. Literature review and existing system (section 4) - reusable; verify citations

Draft text, summarised by source:
- **Langley et al., SIGCOMM 2017** - Google's QUIC deployment; lower search latency and fewer video rebuffers, especially on high-latency links.
- **Kakhki et al., IMC 2017** - QUIC outperforms TCP in most cases but can lose under packet reordering and on low-powered mobile devices.
- **Yu and Benson, 2021** - differences between QUIC implementations matter as much as the protocol itself.
- **RFC 9000 and RFC 9114** - standardise QUIC and HTTP/3.
- Gap statement: most studies use stable links or Western networks and do not model Indian mobile conditions or bursty mobile loss.

Notes:
- I could not check these citations online from here. Before submission, confirm authors, titles, venues and years (I believe the titles are "The QUIC Transport Protocol: Design and Internet-Scale Deployment", "Taking a Long Look at QUIC" and "Dissecting Performance of Production QUIC", but verify).
- **Your own results connect to the Yu and Benson point:** two independent QUIC senders (nginx and aioquic) both lagged kernel TCP under data-packet loss, which supports "implementation matters". Say it only as consistent with their finding.
- The "Kakhki ... can lose on low-powered devices" point may relate to your 10 MB result (HTTP/2 faster at 0 % loss), but you did not measure CPU, so do not claim a link.

## 6. Abstract of the proposed work (section 5) - reusable with two edits

Keep the description of the analyzer (Nginx with HTTP/3, curl, tc netem, namespaces, automated sweep, CSV, analysis, Wireshark
keylog). Edits: "curl ... and aioquic as clients" -> aioquic is a cross-check; "Wireshark ... to decrypt and inspect QUIC
handshakes" -> only once the decrypted capture is verified.

## 7. System design and workflow (section 6) - reusable

Draft flow: client namespace (curl / aioquic) -> veth link with tc netem (delay, jitter, loss, rate) -> server namespace
(Nginx :443 TCP h2 + UDP h3). Workflow: set up namespaces -> apply netem profile -> run N downloads over h2 and h3 -> log to CSV
-> capture pcap with keylog -> aggregate and plot -> find crossover. *Keep.* The draft has `[Insert architecture diagram here]`;
`docs/Architecture.md` has an ASCII diagram you can redraw. Real addresses: client 10.0.0.1 (`veth-c`), server 10.0.0.2 (`veth-s`).

## 8. Contribution of individual team member (section 7) - reusable as is

Abhilash Singh, 24BCI0054: testbed setup, netem profiles, automation scripts, analysis and report.

## 9. Limitations and future enhancement (section 12) - keep and extend

Keep: emulated network may not match real mobile networks; single client/server pair, no concurrent flows; future work on
real-device tests on Indian carriers, BBR vs CUBIC, video streaming.
Add from the real work: loss on the India profiles is modeled (ICMP loss measured 0 %); one object per connection, no multiplexed
page load; self-signed certificate; single host with other processes sharing 12 cores (several sweeps ran as parallel shards);
mechanism behind HTTP/3's slowness under loss only partly isolated; curl as the main client.
Note: the PRD lists BBR vs CUBIC as out of scope, yet a CUBIC-vs-Reno diagnostic on the **TCP** side was run; mention it
as a diagnostic, not a congestion-control study.

## 10. References (draft list) - reusable; verify URLs and add

- RFC 9000 - QUIC: A UDP-Based Multiplexed and Secure Transport.
- RFC 9114 - HTTP/3.
- Nginx HTTP/3 documentation - nginx.org.
- aioquic - github.com/aiortc/aioquic.
- tc-netem(8) Linux manual page.

Suggested additions (the draft relies on them but does not list them): the three papers in section 5; RFC 9002 (QUIC loss detection and
congestion control, relevant to the loss results); RFC 9001 (QUIC with TLS); ngtcp2 / nghttp3 / curl HTTP/3 documentation;
the Airtel measurement evidence (`docs/Network_Measurement_Evidence.docx`) as an appendix.
