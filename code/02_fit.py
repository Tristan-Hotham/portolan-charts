"""Step 2: positions, fits, residuals, the distortion grid and the morph lines.

Carta Pisana. Names are read on Jomard's facsimile where the original is too faded, and carried back to the scan by a
thin-plate spline through 24 nodes of the two wind-rose circles (read on both images; the facsimile's nodes are found
automatically as the points where many straight rhumb lines meet) and the points I could read on both images with
confidence 1 or 2. Leave-one-out tests on those tie points measure the transfer error. Where a place was read on both,
the reading on the scan wins.

Catalan Atlas. Positions are on the half-size sheet scans. The four sheets are physically separate panels, and the
folds between them hide part of the drawing. The scan of panel 7 repeats the eastern strip of panel 6 (Corsica, Sardinia,
Tabarka to Tunis), so sheets 7 and 8 are shifted west by the offset measured on six coast points read on both; the other
folds are left abutted. As a sensitivity test, a second fit gives sheets 5, 7 and 8 a free offset
against sheet 6 (two numbers each), with scale and rotation shared.

Fits (chart pixels, y turned upward, against true positions in a projection):
  similarity: z = a w + t   (a complex: one scale, one rotation; 4 numbers)   affine: 6 numbers
  projections: Mercator, equirectangular with standard parallel 38 N, and an azimuthal equidistant plane about the
  centre of the points (a 'local' frame in kilometres).
Residuals are great-circle kilometres between the true place and where the fit puts the chart's point back on the
globe. Local error: each point predicted from an affine fit to its 8 nearest neighbours (true distance), as in the
al-Idrisi study. Bearings: pairs at least 100 km apart, chart direction against the true rhumb-line (Mercator) bearing.
Distortion grid: a smoothed thin-plate spline from Mercator to the chart, evaluated along the 5 degree graticule within
400 km of a control point; the same for the Natural Earth coastline (for the morph between chart and truth).
"""
import numpy as np, pandas as pd
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point, LineString, MultiPoint
from shapely.ops import unary_union
from pyproj import Transformer
from common import *

IM = jload(f"{DATA}/images.json")
LAT0 = 38.0
FREE = False
OUT = {}


# ---------------------------------------------------------------- Carta Pisana: carry facsimile readings to the scan
nodes = pd.read_csv(f"{DATA}/pisana_rhumb_nodes.csv")
scan = pd.read_csv(f"{DATA}/readings_pisana_scan.csv")
jom = pd.read_csv(f"{DATA}/readings_pisana_jomard.csv")
assert not scan.identification.duplicated().any() and not jom.identification.duplicated().any()
S = scan.set_index("identification")
ties = [r for r in jom.itertuples() if r.identification in S.index and r.conf <= 2 and S.loc[r.identification, "conf"] <= 2]


def transfer(skip=None):
    src = [[r.x_jomard, r.y_jomard] for r in nodes.itertuples()] + [[t.x, t.y] for t in ties if t.identification != skip]
    dst = [[r.x_scan, r.y_scan] for r in nodes.itertuples()] + [[S.loc[t.identification, "x"], S.loc[t.identification, "y"]] for t in ties if t.identification != skip]
    return RBFInterpolator(np.array(src, float), np.array(dst, float), kernel="thin_plate_spline", smoothing=20)


loo = []
for t in ties:
    p = transfer(t.identification)(np.array([[t.x, t.y]]))[0]
    loo.append(float(np.hypot(p[0] - S.loc[t.identification, "x"], p[1] - S.loc[t.identification, "y"])))
TR = transfer()
jom[["x_scan", "y_scan"]] = TR(jom[["x", "y"]].values.astype(float)).round(1)
both = set(scan.identification) & set(jom.identification)
pis = pd.concat([scan.assign(source="scan", x_facsimile=np.nan, y_facsimile=np.nan),
                 jom[~jom.identification.isin(both)].rename(columns={"x": "x_facsimile", "y": "y_facsimile", "x_scan": "x", "y_scan": "y"}).assign(source="facsimile")],
                ignore_index=True)
pis["chart"], pis["sheet"] = "pisana", np.nan
OUT["transfer"] = {"nodes": len(nodes), "ties": len(ties), "loo_median_px": round(float(np.median(loo)), 1), "loo_max_px": round(float(max(loo)), 1),
                   "read_on_both": len(both), "from_scan": int((pis.source == "scan").sum()), "from_facsimile": int((pis.source == "facsimile").sum())}
print("transfer", OUT["transfer"])

# ---------------------------------------------------------------- Catalan Atlas: mosaic positions
cat = pd.read_csv(f"{DATA}/readings_catalan.csv")
assert not cat.identification.duplicated().any()
SH = IM["catalan"]["sheets"]
cat["x_sheet"], cat["y_sheet"] = cat.x, cat.y
cat["x"] = [r.x + SH[str(int(r.sheet))]["mosaic_x"] for r in cat.itertuples()]
cat["chart"], cat["source"] = "catalan", "scan"
# The Commons scans of panels 6 and 7 overlap: the eastern strip of panel 6 (Corsica, Sardinia and the Tunisian coast from
# Tabarka to Tunis) is drawn again along the western edge of panel 7. The same coast points read on both give the shift
# (sheet 6 x, y ; sheet 7 x, y, half-size sheet pixels). Panels 7 and 8 meet without overlap (Crete runs on across the
# fold), and so do panels 5 and 6.
JOIN67 = [("bisert, first letter", 2833, 4717, 475, 4717), ("tabarcha, first letter", 2680, 4765, 330, 4782),
          ("tunis, first letter", 2915, 4802, 547, 4795), ("Sardinia, north tip", 2677, 3875, 332, 3872),
          ("Sardinia, south tip", 2677, 4419, 332, 4412), ("Corsica, north tip", 2640, 3456, 297, 3475)]
DX67 = float(np.median([a - c for _, a, b, c, d in JOIN67]))
DY67 = float(np.median([b - d for _, a, b, c, d in JOIN67]))
GAP = round(SH["7"]["mosaic_x"] - SH["6"]["mosaic_x"] - DX67, 1)       # mosaic px that panels 7 and 8 sit too far east when abutted
FIXED = {7: (GAP, DY67), 8: (GAP, DY67)}                                # (x, y up) to subtract
print("panel 7 repeats panel 6: shift", DX67, DY67, "-> panels 7 and 8 moved west by", GAP, "mosaic px; spread",
      [round(a - c - DX67) for _, a, b, c, d in JOIN67])
P = pd.concat([pis, cat], ignore_index=True)
P["basin"] = [basin(a, b) for a, b in zip(P.lat, P.lon)]
P["id"] = [f"{c[0]}{i:03d}" for c, i in zip(P.chart, P.groupby("chart").cumcount() + 1)]

# check the typed modern positions against the Natural Earth coast
land = unary_union([shape(f["geometry"]).buffer(0) for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
                    if shape(f["geometry"]).intersects(Point(15, 40).buffer(40))])
coast = land.boundary
tr_m = Transformer.from_crs(4326, 3035, always_xy=True)
P["coast_km"] = [round(coast.distance(Point(lo, la)) * 111.2 * np.cos(np.radians(la)), 1) for la, lo in zip(P.lat, P.lon)]
SMALL_ISLANDS = {"Alboran Island", "Columbretes Islands", "La Galite", "Gorgona", "Ponza", "Palagruza", "Tremiti", "Linosa", "Lampedusa"}   # too small for Natural Earth 1:10m
far = P[(P.coast_km > 15) & ~P.identification.isin(SMALL_ISLANDS) & ~P.identification.str.contains("centre|Strait|estuary|delta|Kerch|Bosporus|mouth", case=False)]
assert far.empty, far[["identification", "coast_km"]].values.tolist()
OUT["coast_check_median_km"] = round(float(P.coast_km.median()), 1)


# ---------------------------------------------------------------- fitting
def project(kind, lat, lon, centre=None):
    if kind == "mercator":
        x, y = merc(lat, lon); return x * np.cos(np.radians(LAT0)), y * np.cos(np.radians(LAT0))   # degrees of arc at 38 N
    if kind == "equirect":
        return np.asarray(lon) * np.cos(np.radians(LAT0)), np.asarray(lat, float)
    if kind == "local":
        t = Transformer.from_crs(4326, f"+proj=aeqd +lat_0={centre[0]} +lon_0={centre[1]} +units=km", always_xy=True)
        x, y = t.transform(np.asarray(lon), np.asarray(lat)); return np.asarray(x) / 111.2, np.asarray(y) / 111.2
    raise ValueError(kind)


def unproject(kind, x, y, centre=None):
    if kind == "mercator":
        return merc_inv(x / np.cos(np.radians(LAT0)), y / np.cos(np.radians(LAT0)))
    if kind == "equirect":
        return np.asarray(y), np.asarray(x) / np.cos(np.radians(LAT0))
    if kind == "local":
        t = Transformer.from_crs(f"+proj=aeqd +lat_0={centre[0]} +lon_0={centre[1]} +units=km", 4326, always_xy=True)
        lo, la = t.transform(np.asarray(x) * 111.2, np.asarray(y) * 111.2); return np.asarray(la), np.asarray(lo)


# Fixed sheet offsets for the Catalan Atlas (mosaic pixels to subtract): see JOIN67 above. FREE = True instead fits an
# offset for every sheet (a sensitivity test; it lets the offsets soak up real distortion).


def design(g, model):
    """Least squares in real form. Unknowns: similarity (a_re, a_im, t_x, t_y) or affine (6), plus 2 per extra sheet."""
    n = len(g)
    wx, wy = g._wx.values, g._wy.values
    sheets = sorted({int(s) for s in g.sheet.dropna()} - {6}) if FREE else []
    if model == "sim":
        A = np.zeros((2 * n, 4 + 2 * len(sheets)))
        A[0::2, 0], A[0::2, 1], A[0::2, 2] = wx, -wy, 1
        A[1::2, 0], A[1::2, 1], A[1::2, 3] = wy, wx, 1
        k0 = 4
    else:
        A = np.zeros((2 * n, 6 + 2 * len(sheets)))
        A[0::2, 0], A[0::2, 1], A[0::2, 2] = wx, wy, 1
        A[1::2, 3], A[1::2, 4], A[1::2, 5] = wx, wy, 1
        k0 = 6
    for j, s in enumerate(sheets):
        m = (g.sheet.values == s)
        A[0::2, k0 + 2 * j][m] = 1; A[1::2, k0 + 2 * j + 1][m] = 1
    b = np.empty(2 * n); b[0::2], b[1::2] = g._zx.values, g._zy.values
    return A, b, sheets, k0


def fit(g, kind, model, centre):
    g = g.copy()
    g["_wx"], g["_wy"] = project(kind, g.lat.values, g.lon.values, centre)
    g["_zx"], g["_zy"] = g.x.values, -g.y.values
    if not FREE:
        g["_zx"] = g._zx.values - np.array([FIXED.get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet])
        g["_zy"] = g._zy.values - np.array([FIXED.get(int(s), (0, 0))[1] if s == s else 0 for s in g.sheet])
    A, b, sheets, k0 = design(g, model)
    c = np.linalg.lstsq(A, b, rcond=None)[0]
    off = {s: (c[k0 + 2 * j], c[k0 + 2 * j + 1]) for j, s in enumerate(sheets)} if FREE else dict(FIXED)
    ox = np.array([off.get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet]); oy = np.array([off.get(int(s), (0, 0))[1] if s == s else 0 for s in g.sheet])
    if not FREE:
        ox, oy = 0 * ox, 0 * oy                                         # the fixed offsets are already applied above
    zx, zy = g._zx.values - ox, g._zy.values - oy                      # chart position in the sheet-corrected frame
    if model == "sim":
        a = complex(c[0], c[1]); t = complex(c[2], c[3])
        w = ((zx + 1j * zy) - t) / a; wx, wy = w.real, w.imag
        par = {"scale_px_per_deg": abs(a), "rot_deg": float(np.degrees(np.angle(a))), "a": a, "t": t}
    else:
        M = np.array([[c[0], c[1]], [c[3], c[4]]]); t = np.array([c[2], c[5]])
        w = np.linalg.solve(M, np.vstack([zx - t[0], zy - t[1]])); wx, wy = w
        par = {"M": M, "t": t}
    la, lo = unproject(kind, wx, wy, centre)
    res = gc_km(g.lat.values, g.lon.values, la, lo)
    par["offsets"] = off
    return res, par, (la, lo)


def summary(res):
    return {"median_km": round(float(np.median(res))), "mean_km": round(float(np.mean(res))), "p90_km": round(float(np.quantile(res, .9))),
            "rms_km": round(float(np.sqrt(np.mean(res ** 2)))), "n": int(len(res))}


FITS = {}
for ch, g in P.groupby("chart"):
    g = g.copy()
    centre = (float(g.lat.mean()), float(g.lon.mean()))
    F = {"n": len(g), "centre": [round(centre[0], 2), round(centre[1], 2)], "proj": {}}
    for kind in ("mercator", "equirect", "local"):
        for model in ("sim", "aff"):
            res, par, _ = fit(g, kind, model, centre)
            d = summary(res)
            if model == "sim":
                d["rot_deg"] = round(par["rot_deg"], 1)
            F["proj"][f"{kind}_{model}"] = d
    # the headline frame: similarity on Mercator
    res, par, (la, lo) = fit(g, "mercator", "sim", centre)
    P.loc[g.index, "res_km"] = res.round(1)
    P.loc[g.index, "fit_lat"], P.loc[g.index, "fit_lon"] = la.round(3), lo.round(3)
    F["rot_deg"] = round(par["rot_deg"], 1)
    F["a"], F["t"] = [par["a"].real, par["a"].imag], [par["t"].real, par["t"].imag]
    F["offsets"] = {str(k): [round(v[0], 1), round(-v[1], 1)] for k, v in par["offsets"].items()}   # x, y in image pixels (y down)
    F["km_per_px_38"] = round(111.32 / par["scale_px_per_deg"], 3)
    # per basin: global residuals and the basin's own similarity fit
    F["basins"] = {}
    for bn in BNAMES:
        h = g[g.basin == bn]
        if len(h) < 3:
            continue
        d = {"n": int(len(h)), "global_median_km": round(float(np.median(P.loc[h.index, "res_km"])))}
        if len(h) >= 8 and (h.sheet.isna().all() or h.sheet.nunique() == 1 or True):
            r2, p2, _ = fit(h, "mercator", "sim", centre)
            d.update({"own_median_km": round(float(np.median(r2))), "rot_deg": round(p2["rot_deg"], 1),
                      "rel_scale": round(p2["scale_px_per_deg"] / par["scale_px_per_deg"], 3)})
            P.loc[h.index, "basin_res_km"] = r2.round(1)
        F["basins"][bn] = d
    # local error: affine fit to the 8 nearest neighbours (true distance), Mercator
    wx, wy = project("mercator", g.lat.values, g.lon.values)
    tree = cKDTree(np.c_[wx, wy])
    ZX = g.x.values - np.array([par["offsets"].get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet])      # sheet-corrected chart frame
    ZY = -g.y.values - np.array([par["offsets"].get(int(s), (0, 0))[1] if s == s else 0 for s in g.sheet])
    loc = []
    for i in range(len(g)):
        _, nb = tree.query([wx[i], wy[i]], k=9)
        nb = [j for j in nb if j != i][:8]
        A = np.c_[wx[nb], wy[nb], np.ones(8)]
        cx = np.linalg.lstsq(A, ZX[nb], rcond=None)[0]; cy = np.linalg.lstsq(A, ZY[nb], rcond=None)[0]
        # invert at point i: chart -> Mercator
        M = np.array([[cx[0], cx[1]], [cy[0], cy[1]]])
        w = np.linalg.solve(M, [ZX[i] - cx[2], ZY[i] - cy[2]])
        la_, lo_ = unproject("mercator", w[0], w[1])
        loc.append(float(gc_km(g.lat.values[i], g.lon.values[i], la_, lo_)))
    P.loc[g.index, "local_km"] = np.round(loc, 1)
    nn8 = [float(gc_km(g.lat.values[i], g.lon.values[i], g.lat.values[j], g.lon.values[j]))
           for i, j in enumerate(tree.query(np.c_[wx, wy], k=9)[1][:, 8])]                  # spread of the neighbourhoods
    F["local"] = {"median_km": round(float(np.median(loc))), "p90_km": round(float(np.quantile(loc, .9))), "nn8_median_km": round(float(np.median(nn8)))}
    F["local_by_basin"] = {bn: round(float(np.median(np.array(loc)[g.basin.values == bn]))) for bn in BNAMES if (g.basin == bn).sum() >= 5}
    # bearings between pairs >= 100 km, chart (sheet-corrected) against the rhumb line
    zx = g.x.values - np.array([par["offsets"].get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet])
    zy = -g.y.values - np.array([par["offsets"].get(int(s), (0, 0))[1] if s == s else 0 for s in g.sheet])
    mx, my = merc(g.lat.values, g.lon.values)
    i, j = np.triu_indices(len(g), 1)
    dkm = gc_km(g.lat.values[i], g.lon.values[i], g.lat.values[j], g.lon.values[j])
    keep = dkm >= 100
    i, j = i[keep], j[keep]
    b_true = np.degrees(np.arctan2(mx[j] - mx[i], my[j] - my[i]))
    b_map = np.degrees(np.arctan2(zx[j] - zx[i], zy[j] - zy[i]))
    err = (b_map - b_true + 180) % 360 - 180
    corr = (err + par["rot_deg"] + 180) % 360 - 180                     # after turning the chart back by its fitted rotation
    F["bearing"] = {"pairs": int(keep.sum()), "median_signed_deg": round(float(np.median(err)), 1), "median_abs_deg": round(float(np.median(np.abs(err))), 1),
                    "median_abs_corrected_deg": round(float(np.median(np.abs(corr))), 1), "within5_corrected_pct": round(100 * float(np.mean(np.abs(corr) <= 5)), 1),
                    "neg_pct": round(100 * float(np.mean(err < 0)), 1)}
    if ch == "catalan":
        FREE = True
        rf, pf, _ = fit(g, "mercator", "sim", centre)
        FREE = False
        F["free_offsets"] = {"median_km": round(float(np.median(rf))), "rot_deg": round(pf["rot_deg"], 1),
                             "offsets": {str(k): [round(v[0], 1), round(-v[1], 1)] for k, v in pf["offsets"].items()}}
        F["rose_gap_px"] = GAP
    FITS[ch] = F
    print(ch, json.dumps({k: F[k] for k in ("n", "rot_deg", "local", "bearing")}), json.dumps(F["proj"]))
    print("  basins", F["basins"], "offsets", F["offsets"])

# ---------------------------------------------------------------- distortion grid and coast morph, in chart pixels
NE = jload(f"{GEO}/ne_50m_land.geojson")["features"]
LANDL = unary_union([shape(f["geometry"]) for f in NE]).intersection(shape({"type": "Polygon", "coordinates": [[[-20, 26], [45, 26], [45, 60], [-20, 60], [-20, 26]]]}))


OV = {}
for ch, g in P.groupby("chart"):
    F = FITS[ch]
    off = {int(k): (v[0], v[1]) for k, v in F["offsets"].items()}      # image pixels, y down
    ox = np.array([off.get(int(s), (0, 0))[0] if s == s else 0 for s in g.sheet]); oy = np.array([off.get(int(s), (0, 0))[1] if s == s else 0 for s in g.sheet])
    zx, zy = g.x.values - ox, g.y.values - oy                         # sheet-corrected image pixels (sheet 6 frame)
    mx, my = merc(g.lat.values, g.lon.values)
    tps = RBFInterpolator(np.c_[mx, my], np.c_[zx, zy], kernel="thin_plate_spline", smoothing=3.0)
    a, t = complex(*F["a"]), complex(*F["t"])
    c38 = np.cos(np.radians(LAT0))

    def sim(lat, lon):
        x, y = merc(lat, lon); z = a * (x * c38 + 1j * y * c38) + t
        return z.real, -z.imag

    hull = MultiPoint(list(zip(g.lon, g.lat))).buffer(0.01)
    bc = g.basin.value_counts()
    gn = g[g.basin.map(bc) >= 5]                      # no grid or coast where a basin has fewer than 5 points (the Pisana's Black Sea)
    near = unary_union([Point(lo, la).buffer(4.0 / max(.3, np.cos(np.radians(la)))) for la, lo in zip(gn.lat, gn.lon)])   # about 400 km

    if ch == "catalan":
        spans = {s: (SH[str(s)]["x0"] + SH[str(s)]["mosaic_x"], SH[str(s)]["x1"] + SH[str(s)]["mosaic_x"]) for s in CAT_SHEETS}

        def to_img(x, y):
            """sheet-corrected frame -> mosaic pixels: find the sheet whose corrected span holds x"""
            X, Y = np.array(x, float), np.array(y, float)
            for s in CAT_SHEETS:
                o = off.get(s, (0, 0)); lo_, hi_ = spans[s][0] - o[0], spans[s][1] - o[0]
                m = (x >= lo_) & (x < hi_)
                X[m] = x[m] + o[0]; Y[m] = y[m] + o[1]
            return X, Y
    else:
        def to_img(x, y):
            return np.asarray(x, float), np.asarray(y, float)

    def lines_of(geoms, step=0.25):
        out = []
        for ln in geoms:
            ln = ln.intersection(near)
            for part in (ln.geoms if hasattr(ln, "geoms") else [ln]):
                if part.is_empty or part.length < 0.5 or part.geom_type != "LineString":
                    continue
                part = part.segmentize(step)
                cs = np.asarray(part.coords)
                out.append(cs)
        return out

    lon_rng = (np.floor(g.lon.min() / 5) * 5 - 5, np.ceil(g.lon.max() / 5) * 5 + 5)
    lat_rng = (np.floor(g.lat.min() / 5) * 5 - 5, np.ceil(g.lat.max() / 5) * 5 + 5)
    grat = [LineString([(lo, la) for la in np.arange(lat_rng[0], lat_rng[1] + .01, .25)]) for lo in np.arange(lon_rng[0], lon_rng[1] + .1, 5)]
    grat += [LineString([(lo, la) for lo in np.arange(lon_rng[0], lon_rng[1] + .01, .25)]) for la in np.arange(lat_rng[0], lat_rng[1] + .1, 5)]
    gl = lines_of(grat)
    cl = lines_of([b for p in (LANDL.geoms if hasattr(LANDL, "geoms") else [LANDL]) for b in [p.exterior] if p.area > 0.02], step=0.1)
    cl = [c for c in cl if len(c) >= 3]

    def warp(arrs, how):
        out = []
        for cs in arrs:
            lon, lat = cs[:, 0], cs[:, 1]
            if how == "tps":
                x, y = merc(lat, lon); q = tps(np.c_[x, y]); X, Y = to_img(q[:, 0], q[:, 1])
            else:
                x, y = sim(lat, lon); X, Y = to_img(x, y)
            out.append(np.c_[X, Y].round(1).tolist())
        return out

    W, H = IM[ch]["w"], IM[ch]["h"]
    OV[ch] = {"grid_tps": warp(gl, "tps"), "grid_sim": warp(gl, "sim"), "coast_tps": warp(cl, "tps"), "coast_sim": warp(cl, "sim"),
              "grid_lab": [], "w": W, "h": H}
    # labels for the graticule: where each meridian/parallel crosses the middle of the data
    for lo in np.arange(lon_rng[0], lon_rng[1] + .1, 5):
        for la in np.arange(lat_rng[0], lat_rng[1] + .1, 5):
            if near.contains(Point(lo, la)):
                x, y = merc(np.array([la]), np.array([lo])); q = tps(np.c_[x, y]); X, Y = to_img(q[:, 0], q[:, 1])
                OV[ch]["grid_lab"].append([round(float(X[0]), 1), round(float(Y[0]), 1), f"{abs(int(la))}°N {abs(int(lo))}°{'E' if lo >= 0 else 'W'}"])
    # where the similarity fit puts each place back on the chart (for residual arrows)
    sx, sy = sim(g.lat.values, g.lon.values); sx, sy = to_img(sx, sy)
    P.loc[g.index, "sim_x"], P.loc[g.index, "sim_y"] = np.round(sx, 1), np.round(sy, 1)
    tq = tps(np.c_[mx, my]); tx_, ty_ = to_img(tq[:, 0], tq[:, 1])
    P.loc[g.index, "tps_x"], P.loc[g.index, "tps_y"] = np.round(tx_, 1), np.round(ty_, 1)
    print(ch, "grid lines", len(gl), "coast lines", len(cl), "labels", len(OV[ch]["grid_lab"]))

jsave(OV, f"{WORK}/overlays.json")
cols = ["id", "chart", "sheet", "label", "identification", "lat", "lon", "basin", "conf", "source", "x", "y", "x_sheet", "y_sheet", "x_facsimile", "y_facsimile",
        "coast_km", "res_km", "basin_res_km", "local_km", "fit_lat", "fit_lon", "sim_x", "sim_y", "tps_x", "tps_y", "note"]
P[cols].to_csv(f"{DATA}/points.csv", index=False)
jsave({"fits": FITS, "transfer": OUT["transfer"], "coast_check_median_km": OUT["coast_check_median_km"], "lat0": LAT0}, f"{DATA}/fit.json", indent=1)
print(P.groupby(["chart", "basin"]).size())
