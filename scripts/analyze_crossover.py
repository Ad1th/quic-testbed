#!/usr/bin/env python3
"""Median completion time per condition per protocol + approximate HTTP/2 <-> HTTP/3 crossover boundary.
Failed/timed-out requests (empty total_s) are counted at the --cap value (right-censored), not dropped."""
import argparse, os, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="data/raw/results.csv")
ap.add_argument("--cap", type=float, default=40.0, help="curl --max-time used by the runner")
ap.add_argument("--tie", type=float, default=0.05, help="|h3/h2-1| below this is called a tie")
ap.add_argument("--tag", default="", help="suffix for output files, e.g. _10MB")
a = ap.parse_args()

df = pd.read_csv(a.csv)
df["failed"] = df.total_s.isna()
df["t"] = df.total_s.fillna(a.cap)
os.makedirs("data/processed", exist_ok=True)
out = []
def P(*x):
    s = " ".join(str(i) for i in x); print(s); out.append(s)

g = df.groupby(["profile", "rtt_ms", "loss_pct", "protocol"])
med = g.agg(n=("t", "size"), fails=("failed", "sum"), median_total_s=("t", "median"),
            p25=("t", lambda s: s.quantile(.25)), p75=("t", lambda s: s.quantile(.75)),
            median_ttfb_s=("ttfb_s", "median"), median_handshake_s=("handshake_s", "median"),
            median_throughput_Bps=("throughput_Bps", "median")).reset_index()
med.to_csv(f"data/processed/medians{a.tag}.csv", index=False)

# paired by iteration: fraction of iterations where h3 beat h2
piv = df.pivot_table(index=["profile", "rtt_ms", "loss_pct", "iteration"], columns="protocol", values="t").dropna().reset_index()
piv["h3_wins"] = piv.h3 < piv.h2
paired = piv.groupby(["profile", "rtt_ms", "loss_pct"]).h3_wins.mean().rename("h3_win_frac")

w = med.pivot_table(index=["profile", "rtt_ms", "loss_pct"], columns="protocol", values=["median_total_s", "fails"]).reset_index()
w.columns = ["profile", "rtt_ms", "loss_pct", "fails_h2", "fails_h3", "h2_s", "h3_s"]
w = w.merge(paired.reset_index(), on=["profile", "rtt_ms", "loss_pct"], how="left")
w["ratio_h3_over_h2"] = w.h3_s / w.h2_s
w["winner"] = np.where(w.ratio_h3_over_h2 < 1 - a.tie, "h3", np.where(w.ratio_h3_over_h2 > 1 + a.tie, "h2", "tie"))
w.to_csv(f"data/processed/crossover_table{a.tag}.csv", index=False)

P(f"# Crossover analysis  ({a.csv}, {len(df)} rows, {int(df.failed.sum())} failed/timeouts counted at {a.cap:g}s)\n")
st = w[w.profile == "static"]
P("## Static grid - median total_s  (h2 / h3, ratio h3/h2; * = winner by >%d%%)" % (a.tie * 100))
rtts = sorted(st.rtt_ms.unique()); losses = sorted(st.loss_pct.unique())
P("loss%\\RTT " + "".join(f"{int(r):>22}ms" for r in rtts))
for l in losses:
    row = f"{l:>8g}  "
    for r in rtts:
        c = st[(st.rtt_ms == r) & (st.loss_pct == l)]
        if c.empty: row += " " * 24; continue
        c = c.iloc[0]
        mk = {"h3": "3", "h2": "2", "tie": "="}[c.winner]
        row += f"  {c.h2_s:6.2f}/{c.h3_s:6.2f} {c.ratio_h3_over_h2:5.2f}x {mk}"
    P(row)
P("(winner marks: 2 = HTTP/2 faster, 3 = HTTP/3 faster, = within tie band)\n")

def crossings(xs, ratios):
    """x values where log-ratio changes sign, by linear interpolation between neighbours."""
    res = []
    for (x0, r0), (x1, r1) in zip(zip(xs, ratios), zip(xs[1:], ratios[1:])):
        l0, l1 = np.log(r0), np.log(r1)
        if l0 == 0 or l0 * l1 < 0:
            res.append(x0 + (x1 - x0) * (0 - l0) / (l1 - l0) if l1 != l0 else x0)
    return res

P("## Boundary along the loss axis (per RTT): loss% where h3/h2 crosses 1")
for r in rtts:
    c = st[st.rtt_ms == r].sort_values("loss_pct")
    x = crossings(c.loss_pct.tolist(), c.ratio_h3_over_h2.tolist())
    first, last = c.iloc[0], c.iloc[-1]
    P(f"  RTT {int(r):>3}ms: ratio {first.ratio_h3_over_h2:.2f}x @ {first.loss_pct:g}% -> {last.ratio_h3_over_h2:.2f}x @ {last.loss_pct:g}%   crossing at loss ~ " +
      (", ".join(f"{v:.2f}%" for v in x) if x else "none in range"))
P("\n## Boundary along the RTT axis (per loss): RTT where h3/h2 crosses 1")
for l in losses:
    c = st[st.loss_pct == l].sort_values("rtt_ms")
    x = crossings(c.rtt_ms.tolist(), c.ratio_h3_over_h2.tolist())
    first, last = c.iloc[0], c.iloc[-1]
    P(f"  loss {l:>4g}%: ratio {first.ratio_h3_over_h2:.2f}x @ {int(first.rtt_ms)}ms -> {last.ratio_h3_over_h2:.2f}x @ {int(last.rtt_ms)}ms   crossing at RTT ~ " +
      (", ".join(f"{v:.0f}ms" for v in x) if x else "none in range"))

nh3, nh2, nt = (st.winner == "h3").sum(), (st.winner == "h2").sum(), (st.winner == "tie").sum()
P(f"\nStatic conditions: h3 faster in {nh3}, h2 faster in {nh2}, tie in {nt} of {len(st)}.")
lo = st[st.loss_pct == min(losses)]; P("Zero/lowest-loss row, h3/h2 by RTT:", ", ".join(f"{int(r)}ms={v:.2f}x" for r, v in zip(lo.rtt_ms, lo.ratio_h3_over_h2)))
mob = w[w.profile != "static"]
if len(mob):
    P("\n## Mobile profiles - median total_s")
    for _, c in mob.iterrows():
        P(f"  {c.profile:<20} h2 {c.h2_s:6.2f}s  h3 {c.h3_s:6.2f}s  ratio {c.ratio_h3_over_h2:5.2f}x  winner={c.winner}  (h3 won {c.h3_win_frac:.0%} of paired iterations, fails h2/h3 = {int(c.fails_h2)}/{int(c.fails_h3)})")
    hs = med[med.profile != "static"].pivot_table(index="profile", columns="protocol", values="median_handshake_s")
    P("  median handshake_s:", "; ".join(f"{i}: h2 {r.h2:.3f} / h3 {r.h3:.3f}" for i, r in hs.iterrows()))
open(f"data/processed/crossover_report{a.tag}.txt", "w").write("\n".join(out) + "\n")

# ---- figures (PRD deliverables: data/results/crossover_summary.csv, crossover_heatmap.png, completion_vs_rtt.png) ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap

os.makedirs("data/results", exist_ok=True)
w.to_csv(f"data/results/crossover_summary{a.tag}.csv", index=False)
H2C, H3C, INK, MUTED, SURF = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.edgecolor": "#e1e0d9", "font.size": 10})

# heatmap: RTT x loss, colour = log2(h3/h2); blue arm = h2 faster, orange arm = h3 faster, gray = equal
piv_r = st.pivot(index="loss_pct", columns="rtt_ms", values="ratio_h3_over_h2").sort_index()
lr = np.log2(piv_r.values)
lim = max(abs(lr).max(), 1e-9)
cmap = LinearSegmentedColormap.from_list("d", ["#eb6834", "#f0efec", "#2a78d6"])
fig, ax = plt.subplots(figsize=(8, 5.2))
im = ax.imshow(lr, cmap=cmap, norm=TwoSlopeNorm(0, -lim, lim), origin="lower", aspect="auto")
ax.set_xticks(range(piv_r.shape[1]), [f"{int(c)}" for c in piv_r.columns])
ax.set_yticks(range(piv_r.shape[0]), [f"{l:g}" for l in piv_r.index])
ax.set_xlabel("RTT (ms)"); ax.set_ylabel("packet loss (%)")
win = np.where(piv_r.values < 1 - a.tie, 1, np.where(piv_r.values > 1 + a.tie, -1, 0))
for i in range(win.shape[0]):
    for j in range(win.shape[1]):
        ax.text(j, i, f"{piv_r.values[i, j]:.2f}x\n{'h3' if win[i, j] > 0 else 'h2' if win[i, j] < 0 else 'tie'}",
                ha="center", va="center", fontsize=8.5, color=INK)
        if j + 1 < win.shape[1] and win[i, j] != win[i, j + 1]:
            ax.plot([j + .5] * 2, [i - .5, i + .5], color=INK, lw=2)
        if i + 1 < win.shape[0] and win[i, j] != win[i + 1, j]:
            ax.plot([j - .5, j + .5], [i + .5] * 2, color=INK, lw=2)
for s in ax.spines.values(): s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=.04, pad=.03)
cb.set_ticks([-lim, 0, lim]); cb.set_ticklabels([f"h3 {2**lim:.1f}x faster", "equal", f"h2 {2**lim:.1f}x faster"])
ax.set_title("HTTP/3 vs HTTP/2, 1 MB download: who wins? (cell = h3 time / h2 time; black line = winner changes)",
             fontsize=9.5, loc="left", color=INK)
fig.tight_layout(); fig.savefig(f"data/results/crossover_heatmap{a.tag}.png", dpi=160); plt.close(fig)

# line charts: median total_s vs RTT, one panel per loss level, h2 vs h3
med_s = med[med.profile == "static"]
fig, axs = plt.subplots(1, len(losses), figsize=(3.1 * len(losses), 3.4), sharex=True)
for ax, l in zip(np.atleast_1d(axs), losses):
    for proto, col, name in (("h2", H2C, "HTTP/2"), ("h3", H3C, "HTTP/3")):
        c = med_s[(med_s.loss_pct == l) & (med_s.protocol == proto)].sort_values("rtt_ms")
        ax.plot(c.rtt_ms, c.median_total_s, color=col, lw=2, marker="o", ms=5, mec=SURF, mew=1.5, label=name)
        ax.fill_between(c.rtt_ms, c.p25, c.p75.clip(upper=a.cap), color=col, alpha=.12, lw=0)
    ax.set_title(f"loss {l:g}%", fontsize=10, color=INK, loc="left"); ax.set_xlabel("RTT (ms)")
    ax.grid(color="#e1e0d9", lw=.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
np.atleast_1d(axs)[0].set_ylabel("median completion time (s)")
np.atleast_1d(axs)[0].legend(frameon=False, loc="upper left")
fig.suptitle("Completion time vs RTT (line = median, band = IQR; timeouts counted at cap)", fontsize=10, x=.01, ha="left")
fig.tight_layout(); fig.savefig(f"data/results/completion_vs_rtt{a.tag}.png", dpi=160); plt.close(fig)
print("figures -> data/results/")

# completion time vs loss, one panel per RTT (draft names this graph)
if a.tag == "":
    rtts_all = sorted(st.rtt_ms.unique())
    fig, axs = plt.subplots(1, len(rtts_all), figsize=(3.1 * len(rtts_all), 3.4), sharex=True)
    for ax, r in zip(np.atleast_1d(axs), rtts_all):
        for proto, col, name in (("h2", H2C, "HTTP/2"), ("h3", H3C, "HTTP/3")):
            c = med_s[(med_s.rtt_ms == r) & (med_s.protocol == proto)].sort_values("loss_pct")
            ax.plot(c.loss_pct, c.median_total_s, color=col, lw=2, marker="o", ms=5, mec=SURF, mew=1.5, label=name)
        ax.set_title(f"RTT {int(r)} ms", fontsize=10, color=INK, loc="left"); ax.set_xlabel("packet loss (%)")
        ax.grid(color="#e1e0d9", lw=.8); ax.set_axisbelow(True)
        for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    np.atleast_1d(axs)[0].set_ylabel("median completion time (s)"); np.atleast_1d(axs)[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Completion time vs packet loss (1 MB; timeouts counted at the 40 s cap)", fontsize=10, x=.01, ha="left")
    fig.tight_layout(); fig.savefig("data/results/completion_vs_loss.png", dpi=160); plt.close(fig)
