# How accurate were portolan charts?

The two most famous early portolan charts, the Carta Pisana (about 1275) and the chart of the Catalan Atlas (1375), measured against the real coast: 248 harbours, headlands, river mouths and islands read by eye on the public domain scans, fitted to their true positions on three projections, with the famous tilt of about 11 degrees, the errors sea by sea, a distortion grid drawn over each chart, and a comparison with Ptolemy, al-Idrisi and the Hereford Mappa Mundi.

Interactive page: https://maps.tristanhotham.com/portolan-charts/
Paper: https://doi.org/10.5281/zenodo.24044645
Blog post: https://blog.tristanhotham.com/2026/10/31/portolan-charts/
Code and data: https://github.com/Tristan-Hotham/portolan-charts

## Headline results

- Readings: 148 places on the Carta Pisana (55 read on the scan, 93 on Jomard's facsimile and carried to the scan by a thin-plate spline, leave-one-out error 23.8 px, about 37 km) and 100 on the four chart panels of the Catalan Atlas.
- Whole chart: one scale, one rotation and one shift (Mercator) leave a median error of 93 km on the Pisana (90th percentile 191 km) and 119 km on the Catalan Atlas (302 km).
- The tilt: both charts are turned anticlockwise against true north, by 10.4 and 11.2 degrees. Directions between pairs of places are turned anticlockwise in 94% of 10,738 Pisana pairs (median 10.2 degrees); turned back, the median direction error is 2.1 degrees on the Pisana and 3.6 on the Catalan Atlas.
- Sea by sea: the Pisana's western and eastern Mediterranean, fitted on their own, are a median 36 and 43 km out (rotations 9.7 and 10.0 degrees). Its Atlantic coasts are 312 km out under the whole-chart fit (3.7 times the Mediterranean) and drawn 18% too small; on the Catalan Atlas 244 km and 24% too small, worst at Dunnet Head (537 km).
- Locally: judged from its eight nearest neighbours, the median Pisana place is 38 km out, the median Catalan place 55 km.
- Projection: an equirectangular frame fits both charts at least as well as Mercator (86 against 93 km on the Pisana); the difference is within the reading error.
- Against earlier maps measured the same way: Ptolemy's Geography 144 km, al-Idrisi's map 239 km (affine), the Hereford Mappa Mundi 516 km.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | The interactive page (built by `code/04_build_site.py`): a deep-zoom chart viewer with the distortion grid, a slider that morphs the true coast onto the chart, and a hand-inked modern map. The modern map is The Inked World engine, loaded from `../ink-map/` on the same site (maps.tristanhotham.com/ink-map/), so its scripts, data and fonts are not copied here. |
| `header.png` | Social card, 1200 x 630. |
| `img/tiles_pisana/`, `img/tiles_catalan/` | The chart scans as WebP tiles for the viewer. |
| `img/*.jpg` | Whole-chart images and figures for the page. |
| `data/readings_pisana_scan.csv` | Input: 55 points read directly on the Pisana scan (pixel x, y), with identification, true latitude and longitude, confidence and note. |
| `data/readings_pisana_jomard.csv` | Input: points read on Jomard's facsimile (pixel x, y on the facsimile). |
| `data/pisana_rhumb_nodes.csv` | Input: the 24 compass-circle nodes on the facsimile and on the scan, used for the transfer. |
| `data/readings_catalan.csv` | Input: points read on the Catalan Atlas chart panels 5 to 8 (panel, pixel x, y on the half-size scans). |
| `data/points.csv` | One row per place used (248 rows): chart, identification, true position, sea, confidence, source, chart position, residuals (whole-chart fit, own-sea fit, local), the fitted position on the globe. |
| `data/fits.csv`, `data/basins.csv`, `data/fit.json` | Fits by projection and model; errors, rotation and scale by sea; fit parameters. |
| `data/images.json`, `data/site.json` | Page data (image geometry, grids, coast and morph lines). |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts, run in order, templates and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Readings: harbours where a written name or town sign fixes the point, headlands and river mouths read from the drawn coast, island centres and tips, on zoomed crops with a pixel grid. Each has a confidence flag (1 clear name and certain place, 2 probable, 3 place certain but exact point or reading doubtful). True positions typed by hand and checked against the Natural Earth 1:10m coastline (median 0.7 km from the coast).
- Pisana transfer: Jomard's facsimile is a tracing, not a geometric copy. Facsimile positions are carried to the scan by a smoothed thin-plate spline through 24 nodes of the two compass circles (found automatically on the facsimile, read by eye on the scan) and 12 tie points read on both; places read on both images use the scan.
- Catalan panels: panels 5 to 8 are cropped to their vellum and laid west to east; panels 7 and 8 are shifted by the 102 px gap measured at a compass rose cut by the 6/7 fold. A free offset for every panel (sensitivity test) improves the median only to 108 km.
- Fits: similarity (scale, rotation, shift) and affine transformations from Mercator, equirectangular (38 degrees N) and azimuthal equidistant positions to chart pixels; errors measured on the globe after inverting the fit. Each sea with at least eight places is also fitted on its own. Local error: each place predicted from an affine fit to its eight nearest neighbours. Directions: every pair of places at least 100 km apart, chart against true rhumb-line bearing.
- Distortion grids: smoothed thin-plate splines from Mercator to the chart carry the 5 degree graticule and the coast onto each chart, drawn only near control points.
- Caveats: the places are those I could read and identify (big harbours and clear headlands; only 3 on the Pisana's Black Sea); my readings are unreviewed; the transfer adds about 37 km of noise to facsimile readings; the scans are photographs of shrunken, folded parchment, the Catalan ones at half size; the comparison maps use different places and fits.

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

- Carta Pisana (about 1275), Bibliothèque nationale de France, Cartes et plans GE B-1118: scan on Wikimedia Commons (https://commons.wikimedia.org/wiki/File:Carte_Pisane.jpg), public domain.
- E. F. Jomard, Les monuments de la géographie (1842 to 1862): facsimile of the Carta Pisana on Wikimedia Commons (https://commons.wikimedia.org/wiki/Category:Carta_Pisana), public domain; used only to read names.
- Catalan Atlas (1375), Bibliothèque nationale de France, Espagnol 30: panel scans on Wikimedia Commons (https://commons.wikimedia.org/wiki/Category:Catalan_Atlas), public domain.
- Natural Earth (public domain): coastlines, land and countries.
- Comparisons: my studies of Ptolemy's Geography (https://maps.tristanhotham.com/ptolemy/), al-Idrisi's map (https://maps.tristanhotham.com/idrisi/) and the Hereford Mappa Mundi (https://maps.tristanhotham.com/mappa-mundi/).
- Modern map: The Inked World (https://maps.tristanhotham.com/ink-map/), OpenStreetMap vector tiles by OpenFreeMap (ODbL), AWS Terrain Tiles. Fonts: MedievalSharp, IM Fell (SIL OFL).
- My readings, the derived data, text and figures: CC BY 4.0. Code: MIT.

## Citation

Hotham, T. (2026) How accurate were portolan charts? The Carta Pisana and the Catalan Atlas measured against the real coast. Zenodo. https://doi.org/10.5281/zenodo.24044645

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
