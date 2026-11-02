#!/usr/bin/env python3
"""Generate every number, table and data figure in the paper from data/rigor/*.csv.
usage (from repo root): python paper/make_assets.py
writes paper/gen/*.tex (tables, \\newcommand numbers) and paper/figs/*.pdf. Nothing in the paper is typed by hand."""
import os
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "data/rigor"
OUT = "paper"
PREV = os.environ.get("PREVIEW_DIR")  # optional: also write 300-dpi PNGs here
os.makedirs(f"{OUT}/gen", exist_ok=True)
os.makedirs(f"{OUT}/figs", exist_ok=True)
CFG = {"A": "A_offon.csv", "B": "B_offoff.csv", "F": "F_bridge.csv", "G": "G_bridge_rcvbuf4m.csv",
       "P": "P_nginx_patched.csv", "H": "H_bridge_rcvbuf4m_4senders.csv", "D": "D_qlog.csv"}
MAXT = 40.0
num = {}  # \newcommand values


def load(f):
    d = pd.read_csv(f"{R}/{f}")
    gap = pd.to_datetime(d.timestamp).groupby(d.run_id).diff().dt.total_seconds() - d.total_s.fillna(MAXT)
    keep = ~(gap > 60)  # transfers adjacent to host sleep (same rule as repro/analyze_rigor.py)
    excl = int((~keep).sum())
    d = d[keep].copy()
    d["t"] = np.where(d.ok == 1, d.total_s, MAXT)
    d["drop_pct"] = 100 * d.data_dropped / (d.data_sent_pkts + d.data_dropped).clip(lower=1)
    return d, excl


D, EX = {}, {}
for k, f in CFG.items():
    D[k], EX[k] = load(f)


def ratios(d):
    """identical procedure and RNG order to repro/analyze_rigor.py for a single configuration"""
    rng = np.random.default_rng(0)
    rows = []
    for (r, l), g in d.groupby(["rtt_ms", "loss_pct"]):
        p = g.pivot_table(index="iteration", columns="protocol", values="t")
        for q in [c for c in ("h3", "h3qg", "h3qc") if c in p and "h2" in p]:
            x = p[["h2", q]].dropna()
            rr = x[q].values / x["h2"].values
            bs = [np.median(rng.choice(rr, len(rr))) for _ in range(2000)]
            try:
                pv = wilcoxon(x[q], x["h2"]).pvalue
            except ValueError:
                pv = 1.0
            rows.append(dict(rtt=r, loss=l, proto=q, n=len(x), ratio=np.median(rr), lo=np.percentile(bs, 2.5),
                             hi=np.percentile(bs, 97.5), p=pv))
    c = pd.DataFrame(rows)
    c["pb"] = (c.p * len(c)).clip(upper=1)
    c["sig"] = ((c.hi < 1) | (c.lo > 1)) & (c.pb < .05)
    return c


RAT = {k: ratios(D[k]) for k in "ABFGPH"}
CELLS = [(50, 0), (50, 1), (50, 2), (50, 5), (100, 0), (100, 1), (100, 2), (100, 5)]


def cellfmt(k, q, r, l):
    s = RAT[k][(RAT[k].proto == q) & (RAT[k].rtt == r) & (RAT[k].loss == l)]
    if s.empty:
        return "--"
    s = s.iloc[0]
    v = f"{s.ratio:.2f}"
    if s.sig:
        v = r"\textbf{" + v + "}" + (r"$^{\downarrow}$" if s.hi < 1 else r"$^{\uparrow}$")
    return v


# ---------- Table: configurations ----------
desc = {"A": ("endpoint veth", "on", "208\\,KB", "h2, nginx, quic-go"),
        "B": ("endpoint veth", "off", "208\\,KB", "h2, nginx, quic-go"),
        "F": ("router netns", "off", "208\\,KB", "h2, nginx, quic-go"),
        "G": ("router netns", "off", "4\\,MB", "h2, nginx, quic-go"),
        "D": ("router netns", "off", "4\\,MB", "nginx, quic-go + qlog"),
        "P": ("router netns", "off", "4\\,MB", "h2, \\emph{patched} nginx, quic-go"),
        "H": ("router netns", "off", "4\\,MB", "h2, nginx, quic-go, quiche")}
lines = [r"\begin{tabular}{@{}clcclr@{}}", r"\toprule",
         r"Cfg & netem on & Offl. & rcvbuf & HTTP senders & $n$ \\", r"\midrule"]
for k in "ABFGDPH":
    p, o, b, s = desc[k]
    lines.append(f"{k} & {p} & {o} & {b} & {s} & {len(D[k]):,} \\\\".replace(",", "{,}", 1) if False else
                 f"{k} & {p} & {o} & {b} & {s} & {len(D[k])} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(f"{OUT}/gen/tab_configs.tex", "w").write("\n".join(lines) + "\n")

# ---------- Table: paired ratios across configurations ----------
cols = [("A", "h3"), ("F", "h3"), ("G", "h3"), ("H", "h3"), ("P", "h3"),
        ("A", "h3qg"), ("F", "h3qg"), ("G", "h3qg"), ("H", "h3qg"), ("H", "h3qc")]
lines = [r"\begin{tabular}{@{}lr|rrrr|r|rrrr|r@{}}", r"\toprule",
         r" & HTTP/2 & \multicolumn{5}{c|}{nginx HTTP/3 / HTTP/2} & \multicolumn{4}{c|}{quic-go / HTTP/2} & quiche \\",
         r"RTT, loss & G (s) & A & F & G & H & P$^\dagger$ & A & F & G & H & H \\", r"\midrule"]
for r, l in CELLS:
    h2 = D["G"][(D["G"].protocol == "h2") & (D["G"].rtt_ms == r) & (D["G"].loss_pct == l)].t.median()
    row = [f"{r}\\,ms, {l}\\,\\%", f"{h2:.2f}"] + [cellfmt(k, q, r, l) for k, q in cols]
    lines.append(" & ".join(row) + r" \\")
    if (r, l) == (50, 5):
        lines.append(r"\midrule")
lines += [r"\bottomrule", r"\end{tabular}"]
open(f"{OUT}/gen/tab_ratios.tex", "w").write("\n".join(lines) + "\n")

# ---------- Table: stock vs patched nginx ----------
def med(k, q, r, l):
    d = D[k]
    return d[(d.protocol == q) & (d.rtt_ms == r) & (d.loss_pct == l)].t.median()


lines = [r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
         r"RTT, loss & stock (G), s & patched (P), s & speed-up \\", r"\midrule"]
sp = []
for r, l in CELLS:
    a, b = med("G", "h3", r, l), med("P", "h3", r, l)
    sp.append((l, a / b))
    lines.append(f"{r}\\,ms, {l}\\,\\% & {a:.2f} & {b:.2f} & {a / b:.2f}$\\times$ \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(f"{OUT}/gen/tab_patch.tex", "w").write("\n".join(lines) + "\n")
lossy = [s for l, s in sp if l > 0]
num["PatchMinSpeedup"] = f"{min(lossy):.1f}"
num["PatchMaxSpeedup"] = f"{max(lossy):.1f}"

# ---------- numbers used in the text ----------
def realised(k, q, l, r=50):
    d = D[k]
    return d[(d.protocol == q) & (d.rtt_ms == r) & (d.loss_pct == l)].drop_pct.median()


for k in "ABF":
    for q, n in (("h2", "Tcp"), ("h3", "Ngx"), ("h3qg", "Qgo")):
        for l, ln in ((1, "One"), (2, "Two"), (5, "Five")):
            num[f"Loss{k}{n}{ln}"] = f"{realised(k, q, l):.2f}"
num["TotalTransfers"] = f"{sum(len(D[k]) for k in 'ABFGPH') + len(D['D']):,}"
num["Excluded"] = str(sum(EX.values()))
num["ExcludedNumerator"] = str(sum(EX.values()))
num["Failures"] = str(int(sum((D[k].ok == 0).sum() for k in "ABFGPHD")))
num["Hangs"] = str(int(sum(D[k].exit_hang.fillna(0).sum() for k in "ABFGPHD" if "exit_hang" in D[k])))
a0 = D["A"][(D["A"].protocol == "h3") & (D["A"].loss_pct == 0) & (D["A"].rtt_ms == 50)].udp_rcvbuf_errors.median()
num["RcvbufAZero"] = f"{a0:.0f}"
num["RcvbufFNgx"] = f"{int(D['F'][D['F'].protocol == 'h3'].udp_rcvbuf_errors.sum()):,}".replace(",", "{,}")
num["RcvbufFQgo"] = f"{int(D['F'][D['F'].protocol == 'h3qg'].udp_rcvbuf_errors.sum())}"
num["RcvbufG"] = str(int(D["G"].udp_rcvbuf_errors.sum() + D["H"].udp_rcvbuf_errors.sum() + D["P"].udp_rcvbuf_errors.sum()))
for k in "AFGPH":
    c = RAT[k]
    for q, n in (("h3", "Ngx"), ("h3qg", "Qgo"), ("h3qc", "Qch")):
        s = c[c.proto == q]
        if s.empty:
            continue
        num[f"Rat{k}{n}Min"] = f"{s.ratio.min():.2f}"
        num[f"Rat{k}{n}Max"] = f"{s.ratio.max():.2f}"
        num[f"Sig{k}{n}Faster"] = str(int((s.sig & (s.hi < 1)).sum()))
        num[f"Sig{k}{n}Slower"] = str(int((s.sig & (s.lo > 1)).sum()))
        sl = s[s.loss > 0]
        num[f"Sig{k}{n}LossySlower"] = str(int((sl.sig & (sl.lo > 1)).sum()))
        num[f"Sig{k}{n}LossyFaster"] = str(int((sl.sig & (sl.hi < 1)).sum()))
        num[f"Rat{k}{n}LossyMin"] = f"{sl.ratio.min():.2f}"
        num[f"Rat{k}{n}LossyMax"] = f"{sl.ratio.max():.2f}"


def r1(k, q, r, l):
    c = RAT[k]
    return c[(c.proto == q) & (c.rtt == r) & (c.loss == l)].ratio.iloc[0]


num["RatANgxFiftyTwo"] = f"{r1('A', 'h3', 50, 2):.2f}"
num["RatFNgxFiftyTwo"] = f"{r1('F', 'h3', 50, 2):.2f}"
num["RatANgxFiftyFive"] = f"{r1('A', 'h3', 50, 5):.2f}"
num["RatFNgxFiftyFive"] = f"{r1('F', 'h3', 50, 5):.2f}"
num["RatGNgxZeroLo"] = f"{(1 - max(r1('G', 'h3', 50, 0), r1('G', 'h3', 100, 0))) * 100:.0f}"
num["RatGNgxZeroHi"] = f"{(1 - min(r1('G', 'h3', 50, 0), r1('G', 'h3', 100, 0))) * 100:.0f}"
num["RatFNgxZeroLo"] = f"{(r1('F', 'h3', 50, 0) - 1) * 100:.0f}"
num["RatFNgxZeroHi"] = f"{(r1('F', 'h3', 100, 0) - 1) * 100:.0f}"
for k in "AF":
    h2 = lambda l: med(k, "h2", 50, l)
    num[f"Htwo{k}FiftyTwo"] = f"{h2(2):.2f}"
    num[f"Ngx{k}FiftyTwo"] = f"{med(k, 'h3', 50, 2):.2f}"
cpu = D["G"][D["G"].loss_pct == 0].groupby("protocol").cpu_client_s.median()
num["CpuClientMin"] = f"{cpu.min():.3f}"
num["CpuClientMax"] = f"{cpu.max():.3f}"
with open(f"{OUT}/gen/numbers.tex", "w") as f:
    for k, v in sorted(num.items()):
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

# ---------- figures ----------
NAME = {"h2": "HTTP/2 (kernel TCP)", "h3": "HTTP/3 nginx", "h3qg": "HTTP/3 quic-go", "h3qc": "HTTP/3 quiche"}
# reference categorical palette, fixed order, validated (dataviz validate_palette.js: all checks pass; contrast WARN ->
# secondary encoding by hatch / line style / marker, plus every value is in a table)
COL = {"h2": "#2a78d6", "h3": "#eb6834", "h3qg": "#1baf7a", "h3qc": "#eda100"}
HATCH = {"h2": "", "h3": "////", "h3qg": "....", "h3qc": "xx"}
LS = {"h2": "-", "h3": "--", "h3qg": "-.", "h3qc": ":"}
plt.rcParams.update({"font.size": 7.5, "font.family": "serif", "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "pdf.fonttype": 42, "hatch.linewidth": 0.5})
INK2 = "#52514e"

# Fig: realised loss (A, B, F), 50 ms
fig, axes = plt.subplots(1, 3, figsize=(3.5, 1.75), sharey=True)
for ax, (k, title) in zip(axes, (("A", "A: on endpoints"), ("B", "B: + offloads off"), ("F", "F: on router"))):
    g = D[k][D[k].loss_pct > 0]
    g = g[g.rtt_ms == 50].groupby(["loss_pct", "protocol"]).drop_pct.median().unstack()
    x = np.arange(len(g.index))
    ps = ["h2", "h3", "h3qg"]
    w = 0.26
    for i, p in enumerate(ps):
        ax.bar(x + (i - 1) * w, g[p], w * 0.9, color=COL[p], hatch=HATCH[p], edgecolor="white", lw=0, label=NAME[p])
    for xi, v in zip(x, g.index):
        ax.plot([xi - 0.42, xi + 0.42], [v, v], color="k", lw=0.9)
    ax.set_xticks(x, [f"{v:g}%" for v in g.index])
    ax.set_title(title, fontsize=7.5, pad=2)
    ax.tick_params(length=2, pad=1)
    ax.grid(axis="y", color="#e6e5e0", lw=0.4)
    ax.set_axisbelow(True)
axes[0].set_ylabel("loss events / data pkt (%)")
axes[1].set_xlabel("configured netem loss (black line = nominal)", labelpad=1)
h, lb = axes[0].get_legend_handles_labels()
fig.legend(h, lb, loc="upper center", ncol=3, fontsize=6.5, bbox_to_anchor=(0.55, 1.02), handlelength=1.2,
           columnspacing=0.8)
fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=0.3)
fig.savefig(f"{OUT}/figs/fig_loss.pdf"); PREV and fig.savefig(f"{PREV}/fig_loss.png", dpi=300)

# Fig: ratios across configurations (double column)
CF = ["A", "F", "G", "H", "P"]
CFN = {"A": "A original", "F": "F router", "G": "G +rcvbuf", "H": "H 4 senders", "P": "P patched nginx"}
MK = {"A": "s", "F": "^", "G": "o", "H": "D", "P": "v"}
qs = ["h3", "h3qg", "h3qc"]
fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.35), sharey=True)
for ax, q in zip(axes, qs):
    present = [k for k in CF if not RAT[k][RAT[k].proto == q].empty]
    w = 0.8 / len(present)
    for i, k in enumerate(present):
        s = RAT[k][RAT[k].proto == q].set_index(["rtt", "loss"]).reindex(CELLS)
        xs = np.arange(len(CELLS)) + (i - (len(present) - 1) / 2) * w * (1 if len(present) > 1 else 0)
        ax.errorbar(xs, s.ratio, yerr=[s.ratio - s.lo, s.hi - s.ratio], fmt=MK[k], ms=3.2, color=COL[q],
                    mfc=COL[q] if k in ("H", "P") else "white", mew=0.7, capsize=0, lw=0.6, label=CFN[k])
    ax.axhline(1, color="k", lw=0.6)
    ax.axvline(3.5, color="#c3c2b7", lw=0.5)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4, 8], ["0.25", "0.5", "1", "2", "4", "8"])
    ax.minorticks_off()
    ax.set_xticks(range(len(CELLS)), [f"{l}%" for r, l in CELLS])
    ax.text(1.5, 0.2, "50 ms RTT", ha="center", fontsize=6.5, color=INK2)
    ax.text(5.5, 0.2, "100 ms RTT", ha="center", fontsize=6.5, color=INK2)
    ax.set_ylim(0.17, 9)
    ax.set_title(NAME[q] + " / HTTP/2", fontsize=7.5, pad=2)
    ax.tick_params(length=2, pad=1)
axes[0].set_ylabel("completion-time ratio (log)")
from matplotlib.lines import Line2D
hd = [Line2D([], [], marker=MK[k], ls="", color="#52514e", mfc="#52514e" if k in ("H", "P") else "white", mew=0.7,
             ms=3.5, label=CFN[k]) for k in CF]
fig.legend(handles=hd, loc="upper center", ncol=5, fontsize=6.5, bbox_to_anchor=(0.5, 1.0), handletextpad=0.2,
           columnspacing=1.2, title="configuration (marker); colour = HTTP/3 sender; bars = 95 % bootstrap CI",
           title_fontsize=6.5)
fig.tight_layout(rect=(0, 0, 1, 0.84), w_pad=0.6)
fig.savefig(f"{OUT}/figs/fig_ratio.pdf"); PREV and fig.savefig(f"{PREV}/fig_ratio.png", dpi=300)

# Fig: CDFs. (a) H at 50 ms / 2 %, four senders in one run; (b) stock vs patched nginx at 100 ms / 2 %
fig, axes = plt.subplots(1, 2, figsize=(3.5, 2.0), sharey=True)
g = D["H"][(D["H"].rtt_ms == 50) & (D["H"].loss_pct == 2)]
for p in ["h2", "h3", "h3qg", "h3qc"]:
    v = np.sort(g[g.protocol == p].t.values)
    axes[0].step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=COL[p], ls=LS[p], lw=1.1,
                 label=NAME[p].replace("HTTP/3 ", "").replace("HTTP/2 (kernel TCP)", "HTTP/2"))
axes[0].set_title("(a) H: 50 ms, 2 %", fontsize=7.5, pad=2)
for k, p, lab, ls in (("G", "h2", "HTTP/2 (G)", "-"), ("G", "h3", "nginx stock (G)", "--"),
                      ("P", "h3", "nginx patched (P)", "-")):
    g = D[k][(D[k].rtt_ms == 100) & (D[k].loss_pct == 2) & (D[k].protocol == p)]
    v = np.sort(g.t.values)
    col = COL[p] if lab != "nginx patched (P)" else "#9a3412"
    axes[1].step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=col, ls=ls, lw=1.1, label=lab)
axes[1].set_title("(b) 100 ms, 2 %", fontsize=7.5, pad=2)
for ax in axes:
    ax.set_xlabel("completion time (s)", labelpad=1)
    ax.tick_params(length=2, pad=1)
    ax.grid(color="#e6e5e0", lw=0.4)
for ax, nc in zip(axes, (2, 1)):
    ax.legend(fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=nc, handlelength=2.0,
              columnspacing=0.6, borderaxespad=0)
axes[0].set_ylabel("CDF")
fig.subplots_adjust(left=0.12, right=0.98, top=0.9, bottom=0.40, wspace=0.12)
fig.savefig(f"{OUT}/figs/fig_cdf.pdf"); PREV and fig.savefig(f"{PREV}/fig_cdf.png", dpi=300)
print("excluded per config:", EX)
print("\n".join(f"{k} = {v}" for k, v in sorted(num.items())))
