# Coverage and skip plan: draft report vs real testbed

_Status update: phases 8 (blackout) and 9 (migration) were completed after this was first written; rows below marked 'added later'. Analysis only. Written 2026-10-28 from: the draft (`Computer Networks Lab Submission 9.pdf`, 7 pages), `data/raw/results.csv`
(1560 rows) and the other CSVs under `data/raw/`, `data/processed/*`, `data/captures/*`, and `scripts/`. No experiment was
started for this document and no raw data was modified._

**Evidence rule used:** the draft's result values are placeholders and are ignored. Only CSV rows I can count count as evidence.

**Provenance notes (read first)**
- `results.csv` is not a single run. It is sweep 1 (backup kept at `results_sweep1_backup.csv`, 1120 rows) with the old
  `india_4g`/`india_5g` rows removed, plus the phase-6 shards (`data/raw/p6/*.csv`). It has 2 `run_id`s. That merge was done
  earlier in this session, before this task's "do not modify" rule. Nothing was changed in this task.
- Your brief says "real 5x5 + 3 profiles grid". That was true for sweep 1 only. The current grid is **6 RTT x 6 loss = 36 static
  cells + 3 profiles**. I used the current state.
- The phase 8 blackout test was already running when this task began. It is **in flight and not counted as evidence** below.

## 1. Coverage table

Status: COVERED / PARTIAL / NOT DONE. "rows" = rows in `results.csv` unless another file is named.

### Objectives

| Planned measurement (draft section) | Status | Evidence / what is missing |
|---|---|---|
| Testbed serves same content over h2 and h3 (Obj. 1) | COVERED | `http_version` column = 2 for every h2 row and 3 for every h3 row (1519 successful rows); `nginx -V` has `--with-http_v3_module --with-http_v2_module` |
| Handshake time (Obj. 2) | COVERED | `handshake_s`, 1519 non-null rows; 36 static cells + 3 profiles x 20 iterations x 2 protocols |
| TTFB | COVERED | `ttfb_s`, same 1519 rows |
| Total completion time | COVERED | `total_s`; 41 timeouts kept as empty rows and counted at the 40 s cap in analysis |
| Throughput | COVERED | `throughput_Bps`, same 1519 rows |
| **Loss-burst recovery time** (Obj. 2, draft 9d) | **COVERED (added after this table was first written)** - `data/raw/blackout.csv`, 64 rows, 0 failures; original note: | The `loss_burst` profile is **not in the sweep** (0 rows mention it; `run_tests.py` does not call it). A separate blackout test (`scripts/blackout_test.py` -> `data/raw/blackout.csv`) is running: 32 of 64 rows written, outage 0 s and 1 s finished. Outages 2 s and 4 s still to come. Not usable until it completes and is reviewed. |
| **Connection migration** (Obj. 2, TC4, draft 9d) | **COVERED (added later)** | `data/raw/migration.csv`, 48 rows: curl h2 0/8, curl h3 0/8, aioquic h3 6/8 survived (see TODO.md). Original note: script had never been run. |
| RTT 20-300 ms x loss 0-5 % (Obj. 3) | COVERED | 36 cells: RTT {20,50,100,150,200,300} x loss {0,0.5,1,2,3,5}, 40 rows each (20 per protocol) |
| Indian 4G/5G profiles (Obj. 3) | COVERED | `india_4g`, `india_5g` re-run after the Airtel calibration (40 rows each) + `india_4g_congested` (40 rows). Note: RTT/jitter/rate measured, **loss modeled** (ICMP loss was 0 %). |
| Crossover point (Obj. 4) | COVERED | `data/processed/crossover_table.csv`, `significance.csv`; boundary is "loss > 0 %", not an RTT threshold |

### Test cases

| ID | Draft condition | Status | Evidence |
|---|---|---|---|
| TC1 | 20 ms RTT, 0 % loss | COVERED | static/20/0: 40 rows (h2 0.186 s, h3 0.169 s, ratio 0.91) |
| TC2 | 300 ms RTT, 0 % loss | COVERED | static/300/0: 40 rows (h2 2.706 s, h3 2.409 s, ratio 0.89) |
| TC3 | 100 ms RTT, 5 % loss | COVERED | static/100/5: 40 rows (h2 9.54 s, h3 18.87 s, ratio 1.98) |
| TC4 | India 4G profile **+ IP switch** | **PARTIAL** | IP switch run exists (`migration.csv`) but on a fixed 50 ms / 20 Mbit link, **not** the full India 4G profile (no bursty loss/jitter) |

### Modules and other planned items

| Item | Status | Evidence / gap |
|---|---|---|
| Server module (nginx h2+h3, 1 MB and 10 MB files) | COVERED | `conf/nginx.conf`; `~/srv/content/{1MB,10MB}.bin` |
| 10 MB file measurements | COVERED for its purpose | `data/raw/results_10MB.csv`: 180 rows, 9 cells (RTT 20/100/300 x loss 0/0.5/1), 10 iterations, 21 timeouts at the 90 s cap. Smaller grid and fewer iterations than the 1 MB sweep. |
| Network-emulation module | COVERED | `scripts/netem.sh`; `netem_loss_burst` exists but is unused by any sweep |
| Client / runner: "curl and aioquic" | PARTIAL | `run_tests.py` calls **curl only**. aioquic exists as a separate client: `data/raw/aioquic_check.csv` (120 rows, 4 conditions) and an aioquic *server* in `sender_test.csv` (144 rows). It is not in `results.csv` and the runner does not use it. |
| Capture module (tcpdump/Wireshark + SSLKEYLOGFILE) | PARTIAL | `data/captures/h2.pcap`, `h3.pcap` (100 ms RTT, 0 % loss) and `keys.log` (2 sessions: 2 of each of 5 secret labels) exist. **tcpdump could not run** in the rootless namespace; `scripts/pcap_capture.py` captured instead. **Decryption was never opened or verified** (no `tshark`; Wireshark 3.6.2 GUI only). No screenshot exists. |
| Analysis module (pandas/matplotlib, graphs, crossover) | PARTIAL | Winner heatmap and completion-time-vs-RTT charts exist (`data/results/*.png`). The draft's **completion-time-vs-loss** graph does not exist yet (can be made from existing data, no new run). |
| "Results of Execution" screenshots (Nginx with h3, `curl --http3` output, sweep output, Wireshark handshake) | NOT DONE | Manual screenshots; none taken. Terminal output exists in `logs/` and `data/captures/handshake_timing.txt`. |
| Draft grid: "50 static conditions" | PARTIAL | Real grid = 36 static cells (not 50). The PRD said "~50+" too. See Ambiguities. |
| Draft run count: "2,120 runs" | contradicted | Real `results.csv` = 1,560 rows (+180 10 MB rows + side experiments) |

## 2. What can safely be skipped

Skip = re-running adds no information, because real, countable data already answers it.

| Skip | Reason (one line) |
|---|---|
| TC1, TC2, TC3 | Each has 40 real rows with a significant result (0 %-loss cells are tight: CI width ~0.002); rerun adds nothing |
| Handshake / TTFB / throughput | Already recorded in every row of `results.csv`; handshake ratio is ~0.50-0.53 at every 0 %-loss RTT |
| Full 1 MB sweep / more static cells | 36 cells x 20 paired iterations already analysed with CIs; going to 50 cells is optional (see Ambiguities) |
| India 4G / 5G / congested profile runs | Re-run on the Airtel-calibrated values; old rows are replaced |
| 10 MB runs | 9 cells already show a clear, significant direction (h2 faster in all 9); larger grid is not needed |
| Why-h3-is-slower diagnostics | Four tests done (aioquic client, aioquic server, one-way loss, TCP cubic vs reno) |
| Statistics | `significance.csv` computed for 1 MB and 10 MB |
| Wider aioquic sweep | It was a cross-check; 120 + 144 rows answer that question. Just fix the draft wording (curl-only runner). |

**Not skippable even though the draft claims it was done:** loss-burst recovery, connection migration/TC4, the Wireshark
decrypted-handshake screenshot, and any "results" table or graph in the draft.

## 3. Must still be done before submission (priority order)

| # | Task | Why it is required | Est. time | Needs |
|---|---|---|---|---|
| 1 | **Let the blackout test finish, then review it** (`blackout.csv`) | Draft objective + 9d + conclusion rely on loss-burst recovery; currently 50 % done. Early partial look (not evidence): 1 s outage added ~1.7 s for h2 and ~2.6 s for h3. | ~15-25 min machine time | nothing; already running |
| 2 | **Connection migration / TC4**: validate and run `migration_test.py` | TC4 and the draft's "only HTTP/3 survived" claim have no data. Real outcome may be "curl cannot migrate", which must then be reported as a limitation, not claimed. | 5 min run; +30-60 min if an aioquic-based path is needed | machine to itself |
| 3 | **Wireshark screenshot of the decrypted handshake** (open `h2.pcap` / `h3.pcap`, TLS keylog = `data/captures/keys.log`) | Draft Results-of-Execution and capture module; decryption not yet verified | ~10-15 min | **you** (GUI) |
| 4 | **Other screenshots** (nginx -V showing h3, `curl --http3-only` output, sweep output) | Draft "Insert screenshots" placeholders | ~10 min | you / terminal |
| 5 | **Completion-time-vs-loss graph** (from existing data) | Draft names three graphs; this one is missing | ~10 min | no new run |
| 6 | **Rewrite the report with real numbers** (see `draft_vs_real_corrections.md`) | Every result sentence and the conclusion are placeholders or contradicted | ~1-1.5 h | OneDrive `Project_Report.docx` |
| 7 | **Insert architecture diagram** (draft has `[Insert architecture diagram here]`) | `docs/Architecture.md` has an ASCII version | ~15 min | you / me |

Remaining machine time that is not already running: roughly **10-70 min** (item 2 dominates and is uncertain).

## 4. Ambiguities (stated, not guessed)

- **50 conditions vs 36.** The draft and PRD say ~50. I cannot tell whether your instructor requires 50. If yes, adding 14 cells
  (e.g. RTT 10 and 400 ms, or loss 0.1 %/10 %) is ~45-60 min of parallel runs; if not, rewrite the draft to 36.
- **Migration feasibility.** curl's HTTP/3 stack (ngtcp2) may keep using the old source address and fail. Unknown until run.
- **Wireshark 3.6.2** is old; I believe it decodes QUIC v1 with a keylog but have not verified it on these captures.
- **"Up to 15 % run-to-run variation".** Real data: h2 at 20 ms/0 % has a 2.4 % spread; h3 has one large outlier (spread 147 %
  of median) but a 30 % coefficient of variation driven by that one run. The claim is neither supported nor cleanly refuted.
