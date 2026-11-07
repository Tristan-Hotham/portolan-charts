"""Step 5: figures for the page (img/), the blog (release/blog/b_*.png), the paper (release/paper/f_*.png) and the header."""
import shutil
import numpy as np, pandas as pd
from PIL import Image
from figstyle import *

Image.MAX_IMAGE_PIXELS = None
R = jload(f"{DATA}/results.json")
P = pd.read_csv(f"{DATA}/points.csv")
OV = jload(f"{WORK}/overlays.json")
BLOG, PAPERD = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (BLOG, PAPERD):
    os.makedirs(d, exist_ok=True)


def out(fig, name, page=True, blog=True, paper=True, dpi=200):
    fig.savefig(f"{WORK}/{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{WORK}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=84, optimize=True)
    if blog:
        w = min(1800, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        w = min(2000, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{PAPERD}/f_{name}.png", optimize=True)


def chart_panel(ax, ch, grid=True, pts=True, coast=False, lw=1.0, ms=9):
    im = Image.open(f"{IMG}/{ch}_3200.jpg").convert("RGBA")
    s = im.size[0] / OV[ch]["w"]
    if ch == "pisana":                      # the scan's white surround and the Commons caption become transparent
        a = np.asarray(im).copy()
        white = (a[..., :3].min(2) > 232)
        a[..., 3][white] = 0
        y1, x0 = int(430 * s), int(2780 * s)
        a[:y1, x0:, 3] = 0
        im = Image.fromarray(a)
    ax.imshow(im, extent=(0, OV[ch]["w"], OV[ch]["h"], 0))
    if grid:
        for L in OV[ch]["grid_tps"]:
            a = np.array(L); ax.plot(a[:, 0], a[:, 1], color=RED, lw=lw, alpha=.9, zorder=3)
    if coast:
        for L in OV[ch]["coast_tps"]:
            a = np.array(L); ax.plot(a[:, 0], a[:, 1], color=INKC, lw=lw * .7, alpha=.8, zorder=3)
    if pts:
        g = P[P.chart == ch]
        ax.scatter(g.x, g.y, s=ms, c=[BCOL[b] for b in g.basin], edgecolors=INKC, linewidths=.5, zorder=4)
    ax.set_xlim(0, OV[ch]["w"]); ax.set_ylim(OV[ch]["h"], 0); ax.axis("off")


# ---------- 1. the two charts with their distortion grids
fig = plt.figure(figsize=(14, 12.2)); parchment(fig)
ax1 = fig.add_axes([0.03, 0.53, 0.94, 0.40]); chart_panel(ax1, "pisana", lw=1.3, ms=14)
ax2 = fig.add_axes([0.03, 0.06, 0.94, 0.42]); chart_panel(ax2, "catalan", lw=1.0, ms=9)
fig.text(0.03, 0.965, "Carta Pisana, about 1275", fontproperties=HAND, fontsize=24, color=RED)
fig.text(0.03, 0.495, "Catalan Atlas, 1375 (the four chart panels)", fontproperties=HAND, fontsize=24, color=RED)
fig.text(0.97, 0.965, f"turned {R['fit']['pisana']['rot_deg']:.1f}°", fontproperties=FELLIT, fontsize=19, color=INKC, ha="right")
fig.text(0.97, 0.495, f"turned {R['fit']['catalan']['rot_deg']:.1f}°", fontproperties=FELLIT, fontsize=19, color=INKC, ha="right")
fig.text(0.03, 0.025, "Red: the true meridians and parallels every 5°, bent onto each chart through the places I read (dots, coloured by sea).",
         fontproperties=FELL, fontsize=14, color=MUT)
out(fig, "charts", dpi=170)

# ---------- 2. error by sea
fig = plt.figure(figsize=(12, 6.2)); parchment(fig)
ax = fig.add_axes([0.31, 0.13, 0.66, 0.74])
labels, glob, own, cols = [], [], [], []
for ch in ("pisana", "catalan"):
    for b in BNAMES:
        x = R["fit"][ch]["basins"].get(BSHORT[b])
        if not x or x["n"] < 5: continue
        labels.append(f"{CHARTS[ch]['short']}: {b} ({x['n']})"); glob.append(x["global_median_km"]); own.append(x.get("own_median_km", np.nan)); cols.append(BCOL[b])
y = np.arange(len(labels))[::-1]
ax.barh(y + .18, glob, height=.36, color=cols, edgecolor=INKC, lw=.8, label="one fit for the whole chart")
ax.barh(y - .18, own, height=.36, color=cols, alpha=.38, edgecolor=INKC, lw=.8, hatch="////", label="each sea fitted on its own")
for yy, g_, o_ in zip(y, glob, own):
    ax.text(g_ + 4, yy + .18, f"{g_} km", va="center", fontsize=12, color=INKC)
    if o_ == o_: ax.text(o_ + 4, yy - .18, f"{int(o_)} km", va="center", fontsize=11, color=MUT)
ax.set_yticks(y); ax.set_yticklabels(labels, fontproperties=FELL, fontsize=14)
ax.set_xlabel("median error, km", fontproperties=FELL, fontsize=14)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.legend(frameon=False, prop=FELL, fontsize=13, loc="center right")
fig.text(0.03, 0.93, "Superb at home, lost in the Atlantic", fontproperties=HAND, fontsize=24, color=RED)
out(fig, "basins")

# ---------- 3. bearings
fig = plt.figure(figsize=(12, 5.4)); parchment(fig)
from common import merc
for k, ch in enumerate(("pisana", "catalan")):
    ax = fig.add_axes([0.06 + k * 0.48, 0.15, 0.42, 0.68])
    g = P[P.chart == ch].reset_index(drop=True)
    F = jload(f"{DATA}/fit.json")["fits"][ch]
    off = {int(a): v for a, v in F["offsets"].items()}
    zx = g.x.values - np.array([off.get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet]); zy = -g.y.values
    mx, my = merc(g.lat.values, g.lon.values)
    i, j = np.triu_indices(len(g), 1)
    keep = gc_km(g.lat.values[i], g.lon.values[i], g.lat.values[j], g.lon.values[j]) >= 100
    i, j = i[keep], j[keep]
    err = (np.degrees(np.arctan2(zx[j] - zx[i], zy[j] - zy[i])) - np.degrees(np.arctan2(mx[j] - mx[i], my[j] - my[i])) + 180) % 360 - 180
    corr = (err + F["rot_deg"] + 180) % 360 - 180
    bins = np.arange(-40, 41, 1.5)
    ax.hist(err, bins=bins, color="#B9AC92", edgecolor="none", label="as drawn")
    ax.hist(corr, bins=bins, color=RED, alpha=.75, edgecolor="none", label="turned back")
    ax.axvline(0, color=INKC, lw=.8); ax.axvline(-F["rot_deg"], color=INKC, lw=.8, ls=(0, (3, 2)))
    ax.set_title(f"{CHARTS[ch]['name']}: median {R['fit'][ch]['bearing']['median_signed_deg']:.1f}° as drawn", fontproperties=FELL, fontsize=15)
    ax.set_xlabel("direction error, degrees (negative = anticlockwise)", fontproperties=FELL, fontsize=12.5)
    ax.set_yticks([])
    for s_ in ("top", "right", "left"): ax.spines[s_].set_visible(False)
    if k == 0: ax.legend(frameon=False, prop=FELL, fontsize=12, loc="upper left")
fig.text(0.06, 0.92, "Ten degrees off north", fontproperties=HAND, fontsize=24, color=RED)
out(fig, "bearings")

# ---------- 4. arrows on an ink map, both charts
CRS = "+proj=lcc +lat_1=35 +lat_2=48 +lat_0=40 +lon_0=13 +units=m"
fig = plt.figure(figsize=(16, 7.4)); parchment(fig)
for k, ch in enumerate(("pisana", "catalan")):
    ax = fig.add_axes([0.01 + k * 0.495, 0.08, 0.485, 0.9])
    ext, f = ink_base(ax, CRS, (-20, 42, 28, 58), ripple_m=(12e3, 30e3), coast_lw=.7)
    g = P[P.chart == ch]
    x0, y0 = f(g.lon.values, g.lat.values); x1, y1 = f(g.fit_lon.values, g.fit_lat.values)
    for a, b, c, d, bn in zip(x0, y0, x1, y1, g.basin):
        an = ax.annotate("", (c, d), (a, b), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.1, mutation_scale=8), zorder=6)
        an.arrow_patch.set_clip_box(ax.bbox)
    ax.scatter(x0, y0, s=16, c=[BCOL[b] for b in g.basin], edgecolors=INKC, linewidths=.5, zorder=7)
    xs, ys = f(np.array([-14, 42]), np.array([34, 34]))
    ax.set_xlim(f(np.array([-17.5]), np.array([45.0]))[0][0], f(np.array([42.0]), np.array([45.0]))[0][0])
    ax.set_ylim(f(np.array([13.0]), np.array([29.5]))[1][0], f(np.array([13.0]), np.array([58.5]))[1][0])
    ax.text(0.01, 0.97, f"{CHARTS[ch]['name']}, {CHARTS[ch]['date']}", transform=ax.transAxes, fontproperties=HAND, fontsize=21, color=RED, va="top", zorder=20,
            bbox=dict(fc=PAPER, ec="none", alpha=.9, pad=3))
    ax.text(0.99, 0.03, f"median error {R['fit'][ch]['median_km']} km", transform=ax.transAxes, fontproperties=FELLIT, fontsize=15, color=INKC, ha="right", zorder=20,
            bbox=dict(fc=PAPER, ec="none", alpha=.9, pad=3))
fig.text(0.01, 0.025, "Arrows run from each true place to where the chart puts it, after the chart's best single scale, turn and shift.", fontproperties=FELL, fontsize=14, color=MUT)
out(fig, "arrows", dpi=160)

# ---------- 5. comparison with other maps
C = R["compare"]
names = ["Carta Pisana\n(c. 1275)", "Catalan Atlas\n(1375)", "Ptolemy's Geography\n(c. 150)", "al-Idrisi\n(1154, affine fit)", "Hereford Mappa Mundi\n(c. 1300)"]
vals = [R["fit"]["pisana"]["median_km"], R["fit"]["catalan"]["median_km"], C["ptolemy_helmert_median_km"], C["idrisi_affine_median_km"], C["hereford_median_km"]]
fig = plt.figure(figsize=(12, 5.6)); parchment(fig)
ax = fig.add_axes([0.25, 0.12, 0.7, 0.72])
y = np.arange(len(names))[::-1]
ax.barh(y, vals, color=[RED, BLUE, "#B9AC92", "#B9AC92", "#B9AC92"], edgecolor=INKC, lw=.8, height=.6)
for yy, v in zip(y, vals): ax.text(v + 6, yy, f"{v} km", va="center", fontsize=13, color=INKC)
ax.set_yticks(y); ax.set_yticklabels(names, fontproperties=FELL, fontsize=13.5)
ax.set_xlabel("median error after the best fit, km", fontproperties=FELL, fontsize=14)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
fig.text(0.03, 0.91, "The first maps that look right", fontproperties=HAND, fontsize=24, color=RED)
out(fig, "compare")

# ---------- 6. projections (paper)
fig = plt.figure(figsize=(12, 5.0)); parchment(fig)
ax = fig.add_axes([0.08, 0.16, 0.88, 0.68])
PR = [("mercator", "Mercator"), ("equirect", "Equirectangular, 38° N"), ("local", "Azimuthal equidistant")]
w = .2
for k, (ch, col) in enumerate((("pisana", RED), ("catalan", BLUE))):
    for m, (mod, hatch) in enumerate((("sim", None), ("aff", "////"))):
        v = [R["fit"][ch]["proj"][f"{p}_{mod}"]["median_km"] for p, _ in PR]
        xx = np.arange(3) + (k * 2 + m - 1.5) * w
        ax.bar(xx, v, width=w, color=col, alpha=1 if mod == "sim" else .45, hatch=hatch, edgecolor=INKC, lw=.7,
               label=f"{CHARTS[ch]['short']}, {'similarity' if mod == 'sim' else 'affine'}")
        for a, b in zip(xx, v): ax.text(a, b + 2, str(b), ha="center", fontsize=10)
ax.set_xticks(range(3)); ax.set_xticklabels([n for _, n in PR], fontproperties=FELL, fontsize=14)
ax.set_ylabel("median error, km", fontproperties=FELL, fontsize=14)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.legend(frameon=False, prop=FELL, fontsize=11.5, ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.13))
out(fig, "projections", page=False, blog=False)

# ---------- 7. how the Pisana was read (paper): a detail with the facsimile alongside
from scipy.interpolate import RBFInterpolator
fig = plt.figure(figsize=(12, 5.4)); parchment(fig)
ax1 = fig.add_axes([0.02, 0.08, 0.47, 0.82]); ax2 = fig.add_axes([0.51, 0.08, 0.47, 0.82])
scan = Image.open(f"{RAW}/Carte_Pisane_Portolan.jpg").crop((1350, 980, 1700, 1300))
jom = Image.open(f"{RAW}/Carte_Pisane_Jomard.png").convert("L").crop((2080, 1620, 2620, 2110))
ax1.imshow(scan, extent=(1350, 1700, 1300, 980)); ax2.imshow(jom, cmap="gray", extent=(2080, 2620, 2110, 1620))
g = P[(P.chart == "pisana")]
for _, r in g.iterrows():
    if 1350 < r.x < 1700 and 980 < r.y < 1300:
        ax1.scatter(r.x, r.y, s=40, facecolors="none", edgecolors=RED if r.source == "facsimile" else BLUE, linewidths=1.5)
    if r.x_facsimile == r.x_facsimile and 2080 < r.x_facsimile < 2620 and 1620 < r.y_facsimile < 2110:
        ax2.scatter(r.x_facsimile, r.y_facsimile, s=40, facecolors="none", edgecolors=RED, linewidths=1.5)
for a in (ax1, ax2): a.axis("off")
ax1.set_title("the original scan (Sicily)", fontproperties=FELLIT, fontsize=15)
ax2.set_title("Jomard's facsimile, same area", fontproperties=FELLIT, fontsize=15)
out(fig, "reading", page=False, blog=True, paper=True)

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100); parchment(fig)
ax = fig.add_axes([0.36, 0.05, 0.62, 0.9]); chart_panel(ax, "pisana", lw=1.4, ms=10)
fig.text(0.04, 0.80, "How accurate", fontproperties=DISP if "DISP" in globals() else FELL, fontsize=40, color=INKC, fontweight="bold")
fig.text(0.04, 0.70, "were portolan", fontproperties=FELL, fontsize=40, color=INKC)
fig.text(0.04, 0.58, "charts?", fontproperties=HAND, fontsize=50, color=RED)
fig.text(0.04, 0.44, f"{R['counts']['all']} places on two medieval\nsea charts, measured against\nthe real coast. Both are turned\nabout {R['rot_mean']:.0f}° off true north.", fontproperties=FELL, fontsize=17, color=INKC, linespacing=1.35, va="top")
fig.text(0.04, 0.06, "maps.tristanhotham.com/portolan-charts", fontproperties=FELL, fontsize=13, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
