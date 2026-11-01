# Literature and references

_Checked 2026-10-28 with web searches. "Confirmed" = bibliographic details matched at least one source found online; "From memory"
= standard references I did not re-check. Add the DOI/pages marked "to add" from the ACM Digital Library before final submission._

## Papers cited in the report

| # | Citation | Status | What the report says it shows | Where it connects to our results |
|---|---|---|---|---|
| 1 | A. Langley, A. Riddoch, A. Wilk, et al., "The QUIC Transport Protocol: Design and Internet-Scale Deployment," *Proc. ACM SIGCOMM 2017*, Los Angeles, Aug 21-25, 2017. Source: https://research.google/pubs/the-quic-transport-protocol-design-and-internet-scale-deployment/ | Confirmed (title, authors, venue, year; pages and DOI to add) | Google's QUIC deployment (Chrome, YouTube); lower search latency and fewer video rebuffers, especially on high-latency links; roughly 7 % of Internet traffic was QUIC | Our 0 %-loss result (HTTP/3 ~11 % faster at every RTT) matches the handshake-saving argument; our loss results do not reproduce a loss-driven advantage |
| 2 | A. M. Kakhki, S. Jero, D. Choffnes, C. Nita-Rotaru, A. Mislove, "Taking a Long Look at QUIC: An Approach for Rigorous Evaluation of Rapidly Evolving Transport Protocols," *Proc. ACM IMC 2017*, pp. 290-303. DOI 10.1145/3131365.3131368 | Confirmed (title, authors, venue, pages, DOI) | QUIC generally outperforms TCP, but has issues with window sizes, re-ordered packets and many small objects, and performs worse on mobile devices and cellular networks | Their "worse on mobile devices" point is the nearest published parallel to our 10 MB result (HTTP/2 faster at 0 % loss), but we did not measure CPU, so we cannot claim the same cause |
| 3 | A. Yu and T. A. Benson, "Dissecting Performance of Production QUIC," *Proc. The Web Conference (WWW) 2021*, Ljubljana, pp. 1157-1168. DOI 10.1145/3442381.3450103 | Confirmed (title, authors, venue, pages, DOI) | QUIC's performance depends heavily on the server's congestion-control algorithm and the robustness of the implementation; the faster handshake is an advantage but a secondary one; measurements often reflect implementation choices | Directly supports our diagnostic finding: two independent QUIC senders (nginx and aioquic) both lagged kernel TCP under data-packet loss, and TCP congestion control (Reno vs CUBIC) explained part of it |

Wording note: the draft says Yu and Benson found that "differences between QUIC implementations matter as much as the protocol
itself." That is a fair paraphrase; the paper's own wording is that results depend on implementation choices, bugs and configuration.

## Standards (from memory; stable)

- RFC 9000, J. Iyengar and M. Thomson (eds.), "QUIC: A UDP-Based Multiplexed and Secure Transport," IETF, May 2021.
- RFC 9001, M. Thomson and S. Turner (eds.), "Using TLS to Secure QUIC," IETF, May 2021.
- RFC 9002, J. Iyengar and I. Swett (eds.), "QUIC Loss Detection and Congestion Control," IETF, May 2021. (Relevant to our loss results: it specifies a NewReno-style default.)
- RFC 9114, M. Bishop (ed.), "HTTP/3," IETF, June 2022.

## Tools and documentation

- nginx HTTP/3 (QUIC) documentation: https://nginx.org/en/docs/quic.html
- aioquic: https://github.com/aiortc/aioquic
- curl HTTP/3 documentation: https://curl.se/docs/http3.html
- ngtcp2 / nghttp3: https://github.com/ngtcp2/ngtcp2, https://github.com/ngtcp2/nghttp3
- tc-netem(8), Linux manual page.
- Wireshark (version used: 3.6.2): https://www.wireshark.org

## Our own measurement evidence

- Airtel calibration (28 Oct 2026): `docs/Network_Measurement_Evidence.docx`
- Data and scripts: see the root `README.md`.
