"""Reddit collage (r/dataisbeautiful): both charts with their distortion grids, the true Mediterranean with every place
read, error by sea, and a full legend. Light paper background; every label sits on the paper margin, never on the maps."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import numpy as np, pandas as pd
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from figstyle import *

Image.MAX_IMAGE_PIXELS = None
R = jload(f"{DATA}/results.json")
P = pd.read_csv(f"{DATA}/points.csv")
OV = jload(f"{WORK}/overlays.json")


def chart_panel(ax, ch, lw, ms):
    im = Image.open(f"{IMG}/{ch}_3200.jpg").convert("RGBA")
    s = im.size[0] / OV[ch]["w"]
    if ch == "pisana":
        a = np.asarray(im).copy(); a[..., 3][a[..., :3].min(2) > 232] = 0; a[:int(430 * s), int(2780 * s):, 3] = 0; im = Image.fromarray(a)
    ax.imshow(im, extent=(0, OV[ch]["w"], OV[ch]["h"], 0))
    for L in OV[ch]["grid_tps"]:
        a = np.array(L); ax.plot(a[:, 0], a[:, 1], color=RED, lw=lw, alpha=.92, zorder=3)
    g = P[P.chart == ch]
    ax.scatter(g.x, g.y, s=ms, c=[BCOL[b] for b in g.basin], edgecolors=INKC, linewidths=.6, zorder=4)
    ax.set_xlim(0, OV[ch]["w"]); ax.set_ylim(OV[ch]["h"], 0); ax.axis("off")


fig = plt.figure(figsize=(16, 15.5), dpi=170); parchment(fig, seed=5, alpha=.05)
fig.text(0.03, 0.962, "How accurate were the first sea charts?", fontproperties=HAND, fontsize=40, color=RED)
fig.text(0.03, 0.937, f"I read {R['counts']['all']} places on two medieval portolan charts and measured them against the real coast. "
         f"Both are turned about {R['rot_mean']:.0f}° anticlockwise,", fontproperties=FELL, fontsize=18.5, color=INKC)
fig.text(0.03, 0.918, "the Mediterranean is drawn to within a few dozen kilometres, and the Atlantic coasts are shrunk and misplaced.",
         fontproperties=FELL, fontsize=18.5, color=INKC)

# row 1: the charts
a1 = fig.add_axes([0.02, 0.60, 0.47, 0.27]); chart_panel(a1, "pisana", 1.2, 12)
a2 = fig.add_axes([0.51, 0.585, 0.47, 0.285]); chart_panel(a2, "catalan", 0.9, 7)
fp, fc = R["fit"]["pisana"], R["fit"]["catalan"]
fig.text(0.03, 0.885, "Carta Pisana, about 1275", fontproperties=HAND, fontsize=22, color=INKC)
fig.text(0.03, 0.588, f"{fp and R['counts']['pisana']['n']} places · turned {fp['rot_deg']:.1f}° · median miss {fp['median_km']} km",
         fontproperties=FELLIT, fontsize=16, color=MUT)
fig.text(0.52, 0.885, "Catalan Atlas, 1375", fontproperties=HAND, fontsize=22, color=INKC)
fig.text(0.52, 0.573, f"{R['counts']['catalan']['n']} places · turned {fc['rot_deg']:.1f}° · median miss {fc['median_km']} km",
         fontproperties=FELLIT, fontsize=16, color=MUT)

# row 2: the true Mediterranean
CRS = "+proj=lcc +lat_1=35 +lat_2=48 +lat_0=40 +lon_0=13 +units=m"
a3 = fig.add_axes([0.02, 0.13, 0.55, 0.40])
ext, f = ink_base(a3, CRS, (-20, 42, 28, 58), ripple_m=(12e3, 30e3), coast_lw=.7)
g = P[P.chart == "pisana"]
x0, y0 = f(g.lon.values, g.lat.values); x1, y1 = f(g.fit_lon.values, g.fit_lat.values)
for a, b, c, d in zip(x0, y0, x1, y1):
    an = a3.annotate("", (c, d), (a, b), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.2, mutation_scale=9), zorder=6)
    an.arrow_patch.set_clip_box(a3.bbox)
a3.scatter(x0, y0, s=22, c=[BCOL[b] for b in g.basin], edgecolors=INKC, linewidths=.6, zorder=7)
xr = max(np.max(x0), np.max(x1)) + 120e3                                   # keep the Levant coast and its arrows inside
a3.set_xlim(f(np.array([-12.5]), np.array([45.0]))[0][0], max(xr, f(np.array([40.5]), np.array([45.0]))[0][0]))
a3.set_ylim(f(np.array([13.0]), np.array([30.0]))[1][0], f(np.array([13.0]), np.array([57.0]))[1][0])
fig.text(0.03, 0.54, "The real coast: where the Pisana puts each place", fontproperties=HAND, fontsize=22, color=INKC)

# row 2 right: error by sea
a4 = fig.add_axes([0.725, 0.19, 0.245, 0.31])
labels, glob, cols = [], [], []
for ch in ("pisana", "catalan"):
    for b in BNAMES:
        x = R["fit"][ch]["basins"].get(BSHORT[b])
        if not x or x["n"] < 5: continue
        labels.append(f"{CHARTS[ch]['name']}\n{b}"); glob.append(x["global_median_km"]); cols.append(BCOL[b])
y = np.arange(len(labels))[::-1]
a4.barh(y, glob, color=cols, edgecolor=INKC, lw=.8, height=.66)
for yy, v in zip(y, glob): a4.text(v + 5, yy, f"{v}", va="center", fontsize=13, color=INKC)
a4.set_yticks(y); a4.set_yticklabels(labels, fontproperties=FELL, fontsize=12.5, linespacing=1.05)
a4.set_xlabel("median miss, km", fontproperties=FELL, fontsize=14)
for s_ in ("top", "right"): a4.spines[s_].set_visible(False)
a4.set_xlim(0, max(glob) * 1.18)
fig.text(0.60, 0.54, "Median miss by sea", fontproperties=HAND, fontsize=22, color=INKC)

# legend
h = [Line2D([], [], marker="o", ls="", mfc=c, mec=INKC, ms=11, label=n) for n, c in BASINS]
h += [Line2D([], [], color=RED, lw=2, label="True 5° meridians and parallels, bent onto the chart"),
      Line2D([], [], color=RED, lw=1.4, marker=">", ms=6, label="True place to where the chart puts it (best single scale, turn and shift)")]
fig.legend(handles=h, loc="lower left", bbox_to_anchor=(0.02, 0.06), ncol=3, frameon=False, prop=fm.FontProperties(fname=FELL.get_file(), size=18), columnspacing=1.6, handletextpad=.5)
fig.text(0.03, 0.017, "Sources: Carta Pisana (BnF GE B-1118) and Catalan Atlas (BnF Espagnol 30), public domain scans via Wikimedia Commons; Jomard's facsimile; Natural Earth. "
         "Positions read by eye.", fontproperties=FELL, fontsize=13, color=MUT)
fig.text(0.97, 0.036, "maps.tristanhotham.com/portolan-charts", fontproperties=HAND, fontsize=20, color=RED, ha="right")
OUT = os.path.join(ROOT, "reddit", "portolan_charts.png")
fig.savefig(OUT, dpi=170, facecolor=fig.get_facecolor()); plt.close(fig)
im = Image.open(OUT); print(im.size); assert im.size[0] >= 2400
