#!/usr/bin/env python3
"""Summarise run_rigor.py CSVs: per (offloads, rtt, loss, protocol) medians, failures, netem loss events and CPU;
paired h3/h2 and h3qg/h2 ratios with bootstrap 95% CI and Wilcoxon signed-rank (failed transfers = max_time, censored).
usage: analyze_rigor.py <csv>... [--max-time 40] [--out report.md]"""
import argparse, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

ap = argparse.ArgumentParser()
ap.add_argument("csv", nargs="+")
ap.add_argument("--max-time", type=float, default=40)
ap.add_argument("--out", default=None)
a = ap.parse_args()
df = pd.concat([pd.read_csv(f) for f in a.csv], ignore_index=True)
if "topology" not in df:
    df["topology"] = "direct"
df["topology"] = df.topology.fillna("direct")
if "quicgo_gso" not in df:
    df["quicgo_gso"] = "on"
df["quicgo_gso"] = df.quicgo_gso.fillna("on")
# host sleep guard: if the wall-clock gap to the previous row exceeds the transfer time by > 60 s, the Docker VM was
# suspended (macOS idle sleep) around this transfer; drop it (5 rows of ~2700 in the first runs)
df["_gap"] = (pd.to_datetime(df.timestamp).groupby(df.run_id).diff().dt.total_seconds()
             - df.total_s.fillna(a.max_time))
_n = len(df)
df = df[~(df._gap > 60)].copy()
print(f"excluded {_n - len(df)} transfers adjacent to host sleep", file=sys.stderr)
df["t"] = np.where(df.ok == 1, df.total_s, a.max_time)
# data-direction loss events per transfer and what fraction of netem's dequeued packets they are
df["drop_frac_pct"] = 100 * df.data_dropped / (df.data_sent_pkts + df.data_dropped).clip(lower=1)
key = ["topology", "offloads", "rcvbuf", "quicgo_gso", "rtt_ms", "loss_pct"]
rng = np.random.default_rng(0)

summ = (df.groupby(key + ["protocol"])
        .agg(n=("t", "size"), fails=("ok", lambda s: int((s == 0).sum())), median_s=("t", "median"),
             p25=("t", lambda s: s.quantile(.25)), p75=("t", lambda s: s.quantile(.75)),
             loss_events=("data_dropped", "median"), pkts=("data_sent_pkts", "median"),
             drop_pct=("drop_frac_pct", "median"), tcp_retx=("tcp_retrans_segs", "median"),
             rcvbuf_err=("udp_rcvbuf_errors", "sum"), cpu_client=("cpu_client_s", "median"),
             cpu_server=("cpu_server_s", "median"))
        .reset_index())

rows = []
for k, g in df.groupby(key):
    p = g.pivot_table(index="iteration", columns="protocol", values="t")
    for q in [c for c in ("h3", "h3qg") if c in p and "h2" in p]:
        x = p[["h2", q]].dropna()
        r = x[q].values / x["h2"].values
        bs = [np.median(rng.choice(r, len(r))) for _ in range(2000)]
        try:
            pv = wilcoxon(x[q], x["h2"]).pvalue
        except ValueError:
            pv = 1.0
        rows.append(dict(zip(key, k), proto=q, n=len(x), ratio=np.median(r), ci_lo=np.percentile(bs, 2.5),
                         ci_hi=np.percentile(bs, 97.5), p=pv))
cmp_ = pd.DataFrame(rows)
cmp_["p_bonf"] = (cmp_.p * len(cmp_)).clip(upper=1)
cmp_["verdict"] = np.select([(cmp_.ci_hi < 1) & (cmp_.p_bonf < .05), (cmp_.ci_lo > 1) & (cmp_.p_bonf < .05)],
                            [cmp_.proto + " faster", "h2 faster"], "no sig. difference")

pd.set_option("display.width", 200, "display.max_rows", 500)
out = ["# Rigor re-run summary", "", f"files: {', '.join(a.csv)}; {len(df)} transfers, failures counted at {a.max_time:g}s",
       "", "## Per protocol", "", "```\n" + summ.round(3).to_string(index=False) + "\n```", "",
       "## Paired ratios vs h2 (median of per-iteration ratios; Bonferroni over all rows)", "",
       "```\n" + cmp_.round(4).to_string(index=False) + "\n```", ""]
txt = "\n".join(out)
print(txt)
if a.out:
    open(a.out, "w").write(txt)
