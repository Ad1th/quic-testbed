# Related work (expanded for a paper; checked by web search on 2026-11-02)

"Verified" = title, authors, venue and year matched at least one bibliographic source online. Pages/DOIs still to be filled
from IEEE Xplore / ACM DL before submission. Grouped by the claim each one constrains.

## A. QUIC vs TCP performance comparisons (what is already known)

| # | Reference | Status | Why it matters for this paper |
|---|---|---|---|
| A1 | A. Langley et al., "The QUIC Transport Protocol: Design and Internet-Scale Deployment," ACM SIGCOMM 2017 | verified | Handshake saving and deployment gains; our 0 %-loss result is the expected 1-RTT saving, not new |
| A2 | A. M. Kakhki, S. Jero, D. Choffnes, C. Nita-Rotaru, A. Mislove, "Taking a Long Look at QUIC," ACM IMC 2017, DOI 10.1145/3131365.3131368 | verified | Already showed QUIC losing in some conditions and the need for calibrated, instrumented comparisons |
| A3 | A. Yu, T. A. Benson, "Dissecting Performance of Production QUIC," WWW 2021, DOI 10.1145/3442381.3450103 | verified | Implementation and congestion-control choices dominate; directly anticipates "it is the stack, not the protocol" |
| A4 | K. Wolsing, J. Rüth, K. Wehrle, O. Hohlfeld, "A Performance Perspective on Web Optimized Protocol Stacks: TCP+TLS+HTTP/2 vs. QUIC," ANRW 2019 (arXiv 1906.07415) | verified | Fairness argument: compare tuned stacks; QUIC wins on setup and HoL-blocking under loss in their setup |
| A5 | X. Zhang, S. Jin, Y. He, A. Hassan, Z. M. Mao, F. Qian, Z.-L. Zhang, "QUIC is not Quick Enough over Fast Internet," WWW 2024 (arXiv 2310.09423) | verified | Receiver-side processing limits QUIC throughput on fast links: explains our 10 MB / 1 Gbit result and the client UDP rcvbuf overflows we measure; we must not claim this as new |
| A6 | P. Megyesi, Z. Krämer, S. Molnár, "How quick is QUIC?," IEEE ICC 2016 | verified (venue/year only) | Early IEEE comparison; venue precedent |
| A7 | P. Biswal, O. Gnawali, "Does QUIC make the Web faster?," IEEE GLOBECOM 2016 | verified | Only prior Indian-network QUIC measurement found (2G/3G India vs US 4G); pre-HTTP/3 |
| A8 | M. Moulay, J. Díez Muñoz, V. Mancuso, QUIC/HTTP3 over operational mobile networks (MONROE), MedComNet 2021 | verified (details to complete) | Real cellular measurement methodology; CC choice dominates |

## B. Implementation diversity and high-rate / loss studies

| # | Reference | Status | Why it matters |
|---|---|---|---|
| B1 | R. Marx, J. Herbots, W. Lamotte, P. Quax, "Same Standards, Different Decisions: A Study of QUIC and HTTP/3 Implementation Diversity," EPIQ 2020 | verified | 15 stacks behave very differently; qlog/qvis for root-cause analysis (our method) |
| B2 | B. Jaeger, J. Zirngibl, M. Kempf, K. Ploch, G. Carle, "QUIC on the Highway: Evaluating Performance on High-rate Links," IFIP Networking 2023, DOI 10.23919/IFIPNETWORKING57963.2023.10186365 | verified | Studies OS buffer sizes and NIC offloading effects on QUIC vs TCP: closest prior work to our confound analysis |
| B3 | M. Kempf et al., "QUIC on the Fast Lane," Computer Communications 2024, DOI 10.1016/j.comcom.2024.04.038 | verified | Journal extension of B2 |
| B4 | IFIP Networking 2025 paper evaluating QUIC implementations under delay and loss (networking.ifip.org/2025, paper 1571125566) | found, details to complete | Direct prior work on per-stack loss behaviour; must be read before claiming novelty |
| B5 | Pacing study of quiche/picoquic/ngtcp2 (arXiv 2505.09222) | found, details to complete | Spurious-loss detection and HyStart++ interacting with pacing |
| B6 | Endres et al., "Performance of QUIC Implementations Over Geostationary Satellite Links," 2022 (arXiv 2202.08228) | verified | quic-go/ngtcp2/quiche goodput collapses under loss on long links |

## C. Emulation methodology (threats to validity)

| # | Reference | Status | Why it matters |
|---|---|---|---|
| C1 | A. Jurgelionis, J.-P. Laulajainen, M. Hirvonen, A. I. Wang, "An Empirical Study of NetEm Network Emulation Functionalities," IEEE ICCCN 2011, DOI 10.1109/ICCCN.2011.6005933 | verified | netem loss/delay accurate without correlation; jitter under-realised (affects our India profiles) |
| C2 | L. Nussbaum, O. Richard, "A Comparative Study of Network Link Emulators," CNS 2009 | found | Emulator accuracy baseline |
| C3 | netdev discussion on netem and GSO (E. Dumazet / N. Horman, Apr 2016, lore.kernel.org) | verified (mailing list) | Dropping a GSO super-segment drops several wire packets and skews netem loss %; motivates our offload-off condition |
| C4 | J. Rüth, I. Poese, C. Dietzel, O. Hohlfeld, "A First Look at QUIC in the Wild," PAM 2018, DOI 10.1007/978-3-319-76481-8_19 | verified | Deployment context |

## D. Standards
RFC 9000 (QUIC), RFC 9001 (QUIC-TLS), RFC 9002 (loss detection and congestion control), RFC 9114 (HTTP/3), RFC 9369 (QUIC v2, optional).

## Still to do before submission
- Read B2, B4, B5 in full: they are the papers most likely to already contain our headline. State the delta explicitly.
- Get DOIs/pages for A6–A8, B4–B6, C2.
- Target 25–30 references; candidates: QUIC Interop Runner (Seemann & Iyengar, EPIQ 2020), BBR (Cardwell et al., ACM Queue 2016),
  RACK-TLP (RFC 8985), HyStart++ (RFC 9406), Gilbert-Elliott loss modelling.
