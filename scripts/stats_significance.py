#!/usr/bin/env python3
"""Per-condition significance of h3 vs h2: bootstrap 95% CI of the median-of-paired-ratios + Wilcoxon signed-rank
on paired iterations. Failures counted at --cap (right-censored). Writes data/processed/significance.csv."""
import argparse, numpy as np, pandas as pd
from scipy.stats import wilcoxon

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="data/raw/results.csv")
ap.add_argument("--cap", type=float, default=40.0)
ap.add_argument("--boot", type=int, default=5000)
ap.add_argument("--tag", default="")
ap.add_argument("--alpha", type=float, default=0.05)
a = ap.parse_args()
rng = np.random.default_rng(0)

df = pd.read_csv(a.csv); df["t"] = df.total_s.fillna(a.cap)
piv = df.pivot_table(index=["profile", "rtt_ms", "loss_pct", "iteration"], columns="protocol", values="t").dropna().reset_index()
rows = []
for (p, r, l), g in piv.groupby(["profile", "rtt_ms", "loss_pct"]):
    ratio = (g.h3 / g.h2).values
    idx = rng.integers(0, len(ratio), (a.boot, len(ratio)))
    meds = np.median(ratio[idx], axis=1)
    lo, hi = np.percentile(meds, [2.5, 97.5])
    try: pv = wilcoxon(g.h3, g.h2).pvalue
    except ValueError: pv = np.nan
    med = np.median(ratio)
    # Bonferroni across all conditions is applied below
    rows.append(dict(profile=p, rtt_ms=r, loss_pct=l, n=len(g), median_ratio=med, ci_lo=lo, ci_hi=hi, wilcoxon_p=pv))
s = pd.DataFrame(rows)
s["p_bonf"] = (s.wilcoxon_p * len(s)).clip(upper=1)
def verdict(x):
    if x.ci_hi < 1 and x.p_bonf < a.alpha: return "h3 (significant)"
    if x.ci_lo > 1 and x.p_bonf < a.alpha: return "h2 (significant)"
    if x.ci_hi < 1: return "h3 (CI only)"
    if x.ci_lo > 1: return "h2 (CI only)"
    return "no clear difference"
s["verdict"] = s.apply(verdict, axis=1)
s.to_csv(f"data/processed/significance{a.tag}.csv", index=False)
pd.set_option("display.width", 200)
print(s.round(3).to_string(index=False))
print("\n", s.verdict.value_counts().to_string())
