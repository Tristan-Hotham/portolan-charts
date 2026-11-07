"""Step 3: data/results.json (every number quoted anywhere), tables, and the page data (data/site.json).
Page coordinates: every chart pixel becomes the pseudo longitude/latitude used to lay the chart image in MapLibre."""
import numpy as np, pandas as pd
from common import *

P = pd.read_csv(f"{DATA}/points.csv")
FJ = jload(f"{DATA}/fit.json")
F = FJ["fits"]
IM = jload(f"{DATA}/images.json")
OV = jload(f"{WORK}/overlays.json")
PT, HF, ID = jload(PTOLEMY), jload(HEREFORD), jload(IDRISI)
R = {}

# ---- readings
R["counts"] = {"all": len(P)}
for ch, g in P.groupby("chart"):
    R["counts"][ch] = {"n": len(g), "conf1": int((g.conf == 1).sum()), "conf2": int((g.conf == 2).sum()), "conf3": int((g.conf == 3).sum()),
                       "conf12_pct": round(100 * float((g.conf <= 2).mean()), 1),
                       "basins": {BSHORT[b]: int((g.basin == b).sum()) for b in BNAMES}}
R["transfer"] = dict(FJ["transfer"])
R["transfer"]["loo_median_km"] = round(R["transfer"]["loo_median_px"] * F["pisana"]["km_per_px_38"])
R["counts"]["catalan"]["sheets"] = {str(s): int((P[P.chart == "catalan"].sheet == s).sum()) for s in CAT_SHEETS}
R["coast_check_median_km"] = FJ["coast_check_median_km"]
pg = P[P.chart == "pisana"]
R["transfer"]["local_scan_km"] = round(float(pg[pg.source == "scan"].local_km.median()))
R["transfer"]["local_facsimile_km"] = round(float(pg[pg.source == "facsimile"].local_km.median()))

# ---- fits
PRJ = {"mercator": "Mercator", "equirect": "Equirectangular (38° N)", "local": "Azimuthal equidistant (local)"}
R["fit"] = {}
for ch in ("pisana", "catalan"):
    f = F[ch]
    d = {"rot_deg": f["rot_deg"], "median_km": f["proj"]["mercator_sim"]["median_km"], "p90_km": f["proj"]["mercator_sim"]["p90_km"],
         "aff_median_km": f["proj"]["mercator_aff"]["median_km"], "local_median_km": f["local"]["median_km"], "local_p90_km": f["local"]["p90_km"],
         "proj": f["proj"], "bearing": f["bearing"], "km_per_px": f["km_per_px_38"]}
    best = min(f["proj"], key=lambda k: f["proj"][k]["median_km"] if k.endswith("_sim") else 1e9)
    d["best_sim_proj"] = PRJ[best.split("_")[0]]
    d["best_sim_median_km"] = f["proj"][best]["median_km"]
    d["basins"] = {}
    for b in BNAMES:
        x = f["basins"].get(b)
        if x:
            d["basins"][BSHORT[b]] = x
    d["local_basins"] = {BSHORT[b]: v for b, v in f["local_by_basin"].items()}
    R["fit"][ch] = d
R["fit"]["catalan"]["rose_gap_px"] = F["catalan"]["rose_gap_px"]
R["fit"]["catalan"]["free"] = F["catalan"]["free_offsets"]
for ch in ("pisana", "catalan"):
    B = R["fit"][ch]["basins"]
    R["fit"][ch]["atl_vs_med"] = round(B["Atlantic"]["global_median_km"] / np.median([B["W Med"]["global_median_km"], B["E Med"]["global_median_km"]]), 1)
R["rot_mean"] = round((R["fit"]["pisana"]["rot_deg"] + R["fit"]["catalan"]["rot_deg"]) / 2, 1)

# Atlantic: Britain and the Atlantic on each chart, own-fit scale relative to the whole chart
R["atlantic"] = {ch: {"rel_scale": R["fit"][ch]["basins"]["Atlantic"]["rel_scale"], "shrink_pct": round(100 * (1 - R["fit"][ch]["basins"]["Atlantic"]["rel_scale"]))}
                 for ch in ("pisana", "catalan")}

# ---- places to quote
PL = {}
for ch, g in P.groupby("chart"):
    gi = g.set_index("identification")
    for k in ("Gibraltar", "Alexandria", "Acre", "Beirut", "Cap Corse", "Capo Passero", "Malta", "Land's End", "A Coruna", "Constantinople",
              "Bosporus, Constantinople", "Valencia", "Mallorca (centre)", "Madeira", "South Foreland, Dover", "Cape Akamas, Cyprus W", "Dunnet Head", "Mizen Head"):
        if k in gi.index:
            PL.setdefault(ch, {})[norm(k).replace(" ", "_")] = {"res_km": round(float(gi.loc[k, "res_km"])), "local_km": round(float(gi.loc[k, "local_km"]))}
    worst = g.sort_values("res_km", ascending=False).head(5)
    PL.setdefault(ch, {})["worst"] = [{"name": r.identification, "res_km": round(r.res_km), "basin": BSHORT[r.basin]} for r in worst.itertuples()]
    best = g.sort_values("local_km").head(3)
    PL[ch]["best_local"] = [{"name": r.identification, "local_km": round(r.local_km)} for r in best.itertuples()]
R["places"] = PL

# ---- comparisons with my other studies (same habit of measuring, different maps)
PS = PT["regions"]
R["compare"] = {
    "ptolemy_helmert_median_km": PT["fit"]["f3"]["median_km"], "ptolemy_n": PT["fit"]["f3"].get("n", 2358) if isinstance(PT["fit"]["f3"], dict) else 2358,
    "ptolemy_shape_all_km": PT["fit"]["shape_all"]["median_km"],
    "ptolemy_britain_km": PS["EU01"]["shape_km"], "ptolemy_iberia_km": PS["EU02"]["shape_km"], "ptolemy_italy_km": PS["EU06"]["shape_km"],
    "ptolemy_greece_km": PS["EU10"]["shape_km"],
    "hereford_median_km": HF["fit"]["median_disp_km"], "hereford_bearing_deg": HF["bearing"]["median_abs_err"],
    "idrisi_affine_median_km": ID["affine"]["median_resid_km"], "idrisi_local_km": ID["local"]["median_km"],
    "idrisi_med_local_km": ID["groups"]["Mediterranean"]["median_local_km"], "idrisi_bearing_deg": ID["pairs"]["median_brg_err"],
}
R["compare"]["ratio_ptolemy_pisana"] = round(R["compare"]["ptolemy_helmert_median_km"] / R["fit"]["pisana"]["median_km"], 1)
R["compare"]["ratio_hereford_pisana"] = round(R["compare"]["hereford_median_km"] / R["fit"]["pisana"]["median_km"], 1)

# ---- facts written in words: check them
fp, fc = R["fit"]["pisana"], R["fit"]["catalan"]
assert 8 <= fp["rot_deg"] <= 12 and 8 <= fc["rot_deg"] <= 12                     # "about ten degrees", "the famous tilt"
assert fp["bearing"]["median_signed_deg"] < 0 and fc["bearing"]["median_signed_deg"] < 0   # directions on the chart point anticlockwise of true
assert fp["bearing"]["median_abs_corrected_deg"] < 4 and fc["bearing"]["median_abs_corrected_deg"] < 4
for ch in ("pisana", "catalan"):
    B = R["fit"][ch]["basins"]
    assert B["Atlantic"]["global_median_km"] > max(B["W Med"]["global_median_km"], B["E Med"]["global_median_km"])   # the Atlantic is worst
    assert B["Atlantic"]["rel_scale"] < 0.9                                           # the Atlantic coasts are drawn smaller
    assert R["fit"][ch]["local_median_km"] < R["fit"][ch]["median_km"]
assert fp["local_median_km"] < fc["local_median_km"]                              # the Pisana is the tighter of the two locally
assert fp["proj"]["equirect_sim"]["median_km"] <= fp["proj"]["mercator_sim"]["median_km"]
assert fc["proj"]["equirect_sim"]["median_km"] <= fc["proj"]["mercator_sim"]["median_km"]   # "no better on Mercator"
assert fp["proj"]["local_sim"]["median_km"] > fp["proj"]["equirect_sim"]["median_km"]
assert R["compare"]["ptolemy_helmert_median_km"] > fp["median_km"] and R["compare"]["hereford_median_km"] > 4 * fp["median_km"]
assert fp["basins"]["W Med"]["own_median_km"] < R["compare"]["ptolemy_italy_km"] and fp["basins"]["E Med"]["own_median_km"] < R["compare"]["ptolemy_greece_km"]
jsave(R, f"{DATA}/results.json", indent=1)

# ---- tables
rows = []
for ch in ("pisana", "catalan"):
    for b in BNAMES:
        x = F[ch]["basins"].get(b)
        if not x: continue
        rows.append({"chart": CHARTS[ch]["name"], "basin": b, "n": x["n"], "global_fit_median_km": x["global_median_km"],
                     "own_fit_median_km": x.get("own_median_km"), "own_rotation_deg": x.get("rot_deg"), "own_relative_scale": x.get("rel_scale"),
                     "local_median_km": F[ch]["local_by_basin"].get(b)})
pd.DataFrame(rows).to_csv(f"{DATA}/basins.csv", index=False)
rows = []
for ch in ("pisana", "catalan"):
    for k, v in F[ch]["proj"].items():
        pr, m = k.split("_")
        rows.append({"chart": CHARTS[ch]["name"], "projection": PRJ[pr], "model": {"sim": "similarity", "aff": "affine"}[m], **v})
pd.DataFrame(rows).to_csv(f"{DATA}/fits.csv", index=False)

# ---- page data
site = {"charts": {}}
for ch in ("pisana", "catalan"):
    W, H = IM[ch]["w"], IM[ch]["h"]
    ll = lambda x, y: list(px2ll(ch, x, y, W, H))
    g = P[P.chart == ch]
    pts = []
    for r in g.itertuples():
        pts.append({"id": r.id, "l": r.label, "n": r.identification, "b": BNAMES.index(r.basin), "c": int(r.conf), "s": r.source[0],
                    "t": [round(r.lon, 3), round(r.lat, 3)], "p": ll(r.x, r.y), "q": ll(r.sim_x, r.sim_y), "w": ll(r.tps_x, r.tps_y),
                    "f": [round(r.fit_lon, 2), round(r.fit_lat, 2)], "e": round(r.res_km), "o": round(r.local_km),
                    "sh": None if r.sheet != r.sheet else int(r.sheet)})
    ov = OV[ch]
    def cv(lines, step=1):
        return [[[round(v, 4) for v in ll(x, y)] for x, y in L[::step] + ([L[-1]] if (len(L) - 1) % step else [])] for L in lines]
    site["charts"][ch] = {"name": CHARTS[ch]["name"], "date": CHARTS[ch]["date"], "bounds": IM[ch]["bounds"], "tz": IM[ch]["tz"],
                          "points": pts, "grid_tps": cv(ov["grid_tps"], 2), "grid_sim": cv(ov["grid_sim"], 2),
                          "coast_tps": cv(ov["coast_tps"], 2), "coast_sim": cv(ov["coast_sim"], 2),
                          "grid_lab": [ll(x, y) + [t] for x, y, t in ov["grid_lab"]],
                          "rot": R["fit"][ch]["rot_deg"], "median": R["fit"][ch]["median_km"], "local": R["fit"][ch]["local_median_km"]}
site["basins"] = [[b, c] for b, c in BASINS]
jsave(site, f"{DATA}/site.json")
print("site.json KB", os.path.getsize(f"{DATA}/site.json") // 1024)
print(json.dumps({k: R[k] for k in ("counts", "transfer", "rot_mean", "atlantic", "compare")}, indent=0)[:2500])
