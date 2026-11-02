#!/usr/bin/env python3
"""Figures for the controlled re-run. usage: plot_rigor.py <outdir> CONFIG=csv [CONFIG=csv ...]
e.g. plot_rigor.py data/rigor/figs A=data/rigor/A_offon.csv B=data/rigor/B_offoff.csv F=data/rigor/F_bridge.csv
fig_realised_loss.png  realised loss events per data packet vs nominal loss, per sender and configuration
fig_ratio.png          paired median h3/h2 ratio with bootstrap 95% CI, per sender, cell and configuration
fig_cdf_50ms_2pct.png  completion-time CDFs at 50 ms / 2 %, per sender and configuration"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
cfg = dict(a.split("=", 1) for a in sys.argv[2:])
D = {k: pd.read_csv(v) for k, v in cfg.items()}
for d in D.values():
    d["t"] = np.where(d.ok == 1, d.total_s, 40.0)
    d["drop_pct"] = 100 * d.data_dropped / (d.data_sent_pkts + d.data_dropped).clip(lower=1)
NAME = {"h2": "HTTP/2 (kernel TCP)", "h3": "HTTP/3 nginx", "h3qg": "HTTP/3 quic-go", "h3qc": "HTTP/3 quiche"}
COL = {"h2": "#555555", "h3": "#d1495b", "h3qg": "#00798c", "h3qc": "#edae49"}
rng = np.random.default_rng(0)
plt.rcParams.update({"font.size": 9, "figure.dpi": 150})

# 1. realised loss
protos = [p for p in NAME if any(p in d.protocol.unique() for d in D.values())]
fig, axes = plt.subplots(1, len(D), figsize=(3.2 * len(D), 2.8), sharey=True)
axes = np.atleast_1d(axes)
for ax, (k, d) in zip(axes, D.items()):
    g = d[d.loss_pct > 0].groupby(["loss_pct", "protocol"]).drop_pct.median().unstack()
    x = np.arange(len(g.index))
    w = 0.8 / len(protos)
    for i, p in enumerate([p for p in protos if p in g]):
        ax.bar(x + i * w - 0.4 + w / 2, g[p], w, color=COL[p], label=NAME[p])
    ax.plot(x, g.index, "k_", markersize=28, mew=1.5, label="nominal")
    ax.set_xticks(x, [f"{v:g} %" for v in g.index])
    ax.set_title(k)
    ax.set_xlabel("netem loss")
axes[0].set_ylabel("loss events per data packet (%)")
axes[-1].legend(fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(f"{out}/fig_realised_loss.png")

# 2. paired ratios
rows = []
for k, d in D.items():
    for (r, l), g in d.groupby(["rtt_ms", "loss_pct"]):
        p = g.pivot_table(index="iteration", columns="protocol", values="t")
        for q in [c for c in p if c != "h2"]:
            x = (p[q] / p["h2"]).dropna().values
            bs = [np.median(rng.choice(x, len(x))) for _ in range(2000)]
            rows.append(dict(cfg=k, rtt=r, loss=l, proto=q, ratio=np.median(x), lo=np.percentile(bs, 2.5),
                             hi=np.percentile(bs, 97.5)))
R = pd.DataFrame(rows)
cells = R[["rtt", "loss"]].drop_duplicates().sort_values(["rtt", "loss"]).values.tolist()
qs = [q for q in NAME if q in R.proto.unique()]
MK = dict(zip(D, "s^oDvP"))
fig, axes = plt.subplots(len(qs), 1, figsize=(6.5, 1.9 * len(qs) + 0.4), sharex=True, sharey=True)
axes = np.atleast_1d(axes)
for ax, q in zip(axes, qs):
    w = 0.8 / len(D)
    for i, k in enumerate(D):
        s = R[(R.cfg == k) & (R.proto == q)].set_index(["rtt", "loss"]).reindex([tuple(c) for c in cells])
        xs = np.arange(len(cells)) + i * w - 0.4 + w / 2
        ax.errorbar(xs, s.ratio, yerr=[s.ratio - s.lo, s.hi - s.ratio], fmt=MK[k], ms=3.5, color=COL[q],
                    mfc=COL[q] if i == len(D) - 1 else "white", label=k, capsize=1.5, lw=0.8)
    ax.axhline(1, color="k", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4, 8], ["0.25", "0.5", "1", "2", "4", "8"])
    ax.minorticks_off()
    ax.set_ylabel(f"{NAME[q]}\n/ HTTP/2")
    ax.legend(fontsize=7, ncol=len(D), frameon=False, loc="upper right", title="config", title_fontsize=7)
axes[-1].set_xticks(range(len(cells)), [f"{r:g} ms\n{l:g} %" for r, l in cells])
fig.text(0.01, 0.98, "completion-time ratio vs HTTP/2 (median of paired ratios, 95 % CI; < 1 = HTTP/3 faster)",
         fontsize=8, va="top")
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(f"{out}/fig_ratio.png")
R.round(4).to_csv(f"{out}/ratios.csv", index=False)

# 3. CDFs at 50 ms / 2 %
fig, axes = plt.subplots(1, len(D), figsize=(3.2 * len(D), 2.6), sharey=True, sharex=True)
axes = np.atleast_1d(axes)
for ax, (k, d) in zip(axes, D.items()):
    g = d[(d.rtt_ms == 50) & (d.loss_pct == 2)]
    for p in [p for p in protos if p in g.protocol.unique()]:
        v = np.sort(g[g.protocol == p].t.values)
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=COL[p], label=NAME[p])
    ax.set_title(f"{k}: 50 ms, 2 %")
    ax.set_xlabel("completion time (s)")
axes[0].set_ylabel("CDF")
axes[-1].legend(fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(f"{out}/fig_cdf_50ms_2pct.png")
print("wrote", out)
