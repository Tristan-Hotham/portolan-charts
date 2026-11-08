"""Step 7: README.md, LICENSE and the Reddit post text, from data/results.json.
10.5281/zenodo.24044645 and https://blog.tristanhotham.com/2026/10/31/portolan-charts/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
C, T, F, A, X = R["counts"], R["transfer"], R["fit"], R["atlantic"], R["compare"]
fp, fc = F["pisana"], F["catalan"]
DOI, BLOG = "10.5281/zenodo.24044645", "https://blog.tristanhotham.com/2026/10/31/portolan-charts/"
NSCAN = sum(1 for _ in open(f"{DATA}/readings_pisana_scan.csv", encoding="utf-8")) - 1
assert R["places"]["catalan"]["worst"][0]["name"] == "Dunnet Head"
assert fp["basins"]["Atlantic"]["global_median_km"] > 3 * fp["basins"]["W Med"]["global_median_km"]

readme = f"""# How accurate were portolan charts?

The two most famous early portolan charts, the Carta Pisana (about 1275) and the chart of the Catalan Atlas (1375), measured against the real coast: {C['all']} harbours, headlands, river mouths and islands read by eye on the public domain scans, fitted to their true positions on three projections, with the famous tilt of about {R['rot_mean']:.0f} degrees, the errors sea by sea, a distortion grid drawn over each chart, and a comparison with Ptolemy, al-Idrisi and the Hereford Mappa Mundi.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
Code and data: {REPO}

## Headline results

- Readings: {C['pisana']['n']} places on the Carta Pisana ({T['from_scan']} read on the scan, {T['from_facsimile']} on Jomard's facsimile and carried to the scan by a thin-plate spline, leave-one-out error {T['loo_median_px']} px, about {T['loo_median_km']} km) and {C['catalan']['n']} on the four chart panels of the Catalan Atlas.
- Whole chart: one scale, one rotation and one shift (Mercator) leave a median error of {fp['median_km']} km on the Pisana (90th percentile {fp['p90_km']} km) and {fc['median_km']} km on the Catalan Atlas ({fc['p90_km']} km).
- The tilt: both charts are turned anticlockwise against true north, by {fp['rot_deg']} and {fc['rot_deg']} degrees. Directions between pairs of places are turned anticlockwise in {fp['bearing']['neg_pct']:.0f}% of {fp['bearing']['pairs']:,} Pisana pairs (median {fp['bearing']['median_abs_deg']} degrees); turned back, the median direction error is {fp['bearing']['median_abs_corrected_deg']} degrees on the Pisana and {fc['bearing']['median_abs_corrected_deg']} on the Catalan Atlas.
- Sea by sea: the Pisana's western and eastern Mediterranean, fitted on their own, are a median {fp['basins']['W Med']['own_median_km']} and {fp['basins']['E Med']['own_median_km']} km out (rotations {fp['basins']['W Med']['rot_deg']} and {fp['basins']['E Med']['rot_deg']} degrees). Its Atlantic coasts are {fp['basins']['Atlantic']['global_median_km']} km out under the whole-chart fit ({fp['atl_vs_med']} times the Mediterranean) and drawn {A['pisana']['shrink_pct']}% too small; on the Catalan Atlas {fc['basins']['Atlantic']['global_median_km']} km and {A['catalan']['shrink_pct']}% too small, worst at Dunnet Head ({R['places']['catalan']['worst'][0]['res_km']} km).
- Locally: judged from its eight nearest neighbours, the median Pisana place is {fp['local_median_km']} km out, the median Catalan place {fc['local_median_km']} km.
- Projection: an equirectangular frame fits both charts at least as well as Mercator ({fp['proj']['equirect_sim']['median_km']} against {fp['proj']['mercator_sim']['median_km']} km on the Pisana); the difference is within the reading error.
- Against earlier maps measured the same way: Ptolemy's Geography {X['ptolemy_helmert_median_km']} km, al-Idrisi's map {X['idrisi_affine_median_km']} km (affine), the Hereford Mappa Mundi {X['hereford_median_km']} km.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page (built by `code/04_build_site.py`): a deep-zoom chart viewer with the distortion grid, a slider that morphs the true coast onto the chart, and a hand-inked modern map. The modern map is The Inked World engine, loaded from `../ink-map/` on the same site (maps.tristanhotham.com/ink-map/), so its scripts, data and fonts are not copied here. |
| `header.png` | Social card, 1200 x 630. |
| `img/tiles_pisana/`, `img/tiles_catalan/` | The chart scans as WebP tiles for the viewer. |
| `img/*.jpg` | Whole-chart images and figures for the page. |
| `data/readings_pisana_scan.csv` | Input: {NSCAN} points read directly on the Pisana scan (pixel x, y), with identification, true latitude and longitude, confidence and note. |
| `data/readings_pisana_jomard.csv` | Input: points read on Jomard's facsimile (pixel x, y on the facsimile). |
| `data/pisana_rhumb_nodes.csv` | Input: the {T['nodes']} compass-circle nodes on the facsimile and on the scan, used for the transfer. |
| `data/readings_catalan.csv` | Input: points read on the Catalan Atlas chart panels 5 to 8 (panel, pixel x, y on the half-size scans). |
| `data/points.csv` | One row per place used ({C['all']} rows): chart, identification, true position, sea, confidence, source, chart position, residuals (whole-chart fit, own-sea fit, local), the fitted position on the globe. |
| `data/fits.csv`, `data/basins.csv`, `data/fit.json` | Fits by projection and model; errors, rotation and scale by sea; fit parameters. |
| `data/images.json`, `data/site.json` | Page data (image geometry, grids, coast and morph lines). |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts, run in order, templates and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Readings: harbours where a written name or town sign fixes the point, headlands and river mouths read from the drawn coast, island centres and tips, on zoomed crops with a pixel grid. Each has a confidence flag (1 clear name and certain place, 2 probable, 3 place certain but exact point or reading doubtful). True positions typed by hand and checked against the Natural Earth 1:10m coastline (median {R['coast_check_median_km']} km from the coast).
- Pisana transfer: Jomard's facsimile is a tracing, not a geometric copy. Facsimile positions are carried to the scan by a smoothed thin-plate spline through {T['nodes']} nodes of the two compass circles (found automatically on the facsimile, read by eye on the scan) and {T['ties']} tie points read on both; places read on both images use the scan.
- Catalan panels: panels 5 to 8 are cropped to their vellum and laid west to east; the scan of panel 7 repeats the eastern strip of panel 6 (Corsica, Sardinia, Tabarka to Tunis), so panels 7 and 8 are shifted {fc['rose_gap_px']} px west, the offset measured on six coast points read on both. A free offset for every panel (sensitivity test) gives {fc['free']['median_km']} km, no better.
- Fits: similarity (scale, rotation, shift) and affine transformations from Mercator, equirectangular (38 degrees N) and azimuthal equidistant positions to chart pixels; errors measured on the globe after inverting the fit. Each sea with at least eight places is also fitted on its own. Local error: each place predicted from an affine fit to its eight nearest neighbours. Directions: every pair of places at least 100 km apart, chart against true rhumb-line bearing.
- Distortion grids: smoothed thin-plate splines from Mercator to the chart carry the 5 degree graticule and the coast onto each chart, drawn only near control points.
- Caveats: the places are those I could read and identify (big harbours and clear headlands; only {C['pisana']['basins']['Black Sea']} on the Pisana's Black Sea, few on the Catalan Atlantic coasts of Iberia and Ireland); my readings are unreviewed; the transfer adds about {T['loo_median_km']} km of noise to facsimile readings; the scans are photographs of shrunken, folded parchment, the Catalan ones at half size; the comparison maps use different places and fits.

## How to rerun

Needs Python 3 with numpy, scipy, pandas, shapely, pyproj, matplotlib and Pillow, xelatex and pdftotext; node with Playwright for `code/qa.js`. Step 1 reads the Commons scans (paths in `code/common.py`); step 2 reads the readings in `data/` and Natural Earth; the comparison numbers are read from the results of the Ptolemy, Hereford and al-Idrisi studies.

```
python3 code/01_image.py        # chart images, mosaic and tiles
python3 code/02_fit.py          # transfer, fits, residuals, grids, morph lines
python3 code/03_results.py      # results.json, tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # figures and header
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Carta Pisana (about 1275), Bibliothèque nationale de France, Cartes et plans GE B-1118: scan on Wikimedia Commons ({PISANA_URL}), public domain.
- E. F. Jomard, Les monuments de la géographie (1842 to 1862): facsimile of the Carta Pisana on Wikimedia Commons ({JOMARD_URL}), public domain; used only to read names.
- Catalan Atlas (1375), Bibliothèque nationale de France, Espagnol 30: panel scans on Wikimedia Commons ({CATALAN_URL}), public domain.
- Natural Earth (public domain): coastlines, land and countries.
- Comparisons: my studies of Ptolemy's Geography ({PTOLEMY_PAGE}), al-Idrisi's map ({IDRISI_PAGE}) and the Hereford Mappa Mundi ({HEREFORD_PAGE}).
- Modern map: The Inked World (https://maps.tristanhotham.com/ink-map/), OpenStreetMap vector tiles by OpenFreeMap (ODbL), AWS Terrain Tiles. Fonts: MedievalSharp, IM Fell (SIL OFL).
- My readings, the derived data, text and figures: CC BY 4.0. Code: MIT.

## Citation

Hotham, T. (2026) How accurate were portolan charts? The Carta Pisana and the Catalan Atlas measured against the real coast. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures, the paper, the collage, the readings and the derived data in data/: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/.

The chart images in img/ (and the tiles) are reproductions of the Carta Pisana and the Catalan Atlas (Bibliothèque nationale de France) from public domain scans on Wikimedia Commons, and are in the public domain. Natural Earth data are in the public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] I measured two medieval sea charts against the real coast. Both are turned about {R['rot_mean']:.0f}° off north, the Mediterranean is right to a few dozen km, and the Pisana's Atlantic coasts are a median {fp['basins']['Atlantic']['global_median_km']} km out

## Body

Portolan charts are the compass-line sea charts that appear in the Mediterranean in the late 13th century and look startlingly modern. I read {C['all']} harbours, headlands and islands by eye on the two most famous early ones, the Carta Pisana (about 1275, the oldest to survive) and the Catalan Atlas (1375), and fitted them to their true positions. With one scale, turn and shift, the median place is {fp['median_km']} km out on the Pisana and {fc['median_km']} km on the Catalan Atlas. Both are turned anticlockwise, by {fp['rot_deg']}° and {fc['rot_deg']}°, the tilt usually put down to compass courses and magnetic declination; {fp['bearing']['neg_pct']:.0f}% of directions between Pisana places lean the same way. Fit each sea on its own and the Pisana's western and eastern Mediterranean are {fp['basins']['W Med']['own_median_km']} and {fp['basins']['E Med']['own_median_km']} km out, while its Atlantic coasts are {fp['basins']['Atlantic']['global_median_km']} km out and drawn {A['pisana']['shrink_pct']}% too small. Measured the same way, Ptolemy misses by {X['ptolemy_helmert_median_km']} km and the Hereford Mappa Mundi by {X['hereford_median_km']} km. Caveats: positions read by me, by eye, on photographs of folded parchment; the faded Pisana was read partly via a 19th century facsimile; the Pisana's Black Sea is thin. Interactive version, with a slider that bends the real coast onto each chart: {PAGE}

## Source comment

Sources: Carta Pisana (Bibliothèque nationale de France, GE B-1118) and Catalan Atlas (BnF, Espagnol 30), public domain scans on Wikimedia Commons; Jomard's 19th century facsimile of the Pisana (public domain) to help read the names; Natural Earth coastlines. All positions read by eye by me.

Tools: Python (numpy, scipy, pandas, matplotlib, Pillow) for the fits, thin-plate spline grids and figures; MapLibre for the interactive page.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, lic, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("|---|---|", ""), bad
print("README", len(readme.split()), "words; post title", len(post.splitlines()[2]), "chars")
