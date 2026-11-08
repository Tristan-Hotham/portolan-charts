## Title

[OC] I measured two medieval sea charts against the real coast. Both are turned about 11° off north, the Mediterranean is right to a few dozen km, and the Pisana's Atlantic coasts are a median 312 km out

## Body

Portolan charts are the compass-line sea charts that appear in the Mediterranean in the late 13th century and look startlingly modern. I read 349 harbours, headlands and islands by eye on the two most famous early ones, the Carta Pisana (about 1275, the oldest to survive) and the Catalan Atlas (1375), and fitted them to their true positions. With one scale, turn and shift, the median place is 93 km out on the Pisana and 88 km on the Catalan Atlas. Both are turned anticlockwise, by 10.4° and 11.9°, the tilt usually put down to compass courses and magnetic declination; 94% of directions between Pisana places lean the same way. Fit each sea on its own and the Pisana's western and eastern Mediterranean are 36 and 43 km out, while its Atlantic coasts are 312 km out and drawn 18% too small. Measured the same way, Ptolemy misses by 144 km and the Hereford Mappa Mundi by 516 km. Caveats: positions read by me, by eye, on photographs of folded parchment; the faded Pisana was read partly via a 19th century facsimile; the Pisana's Black Sea is thin. Interactive version, with a slider that bends the real coast onto each chart: https://maps.tristanhotham.com/portolan-charts/

## Source comment

Sources: Carta Pisana (Bibliothèque nationale de France, GE B-1118) and Catalan Atlas (BnF, Espagnol 30), public domain scans on Wikimedia Commons; Jomard's 19th century facsimile of the Pisana (public domain) to help read the names; Natural Earth coastlines. All positions read by eye by me.

Tools: Python (numpy, scipy, pandas, matplotlib, Pillow) for the fits, thin-plate spline grids and figures; MapLibre for the interactive page.

Interactive version: https://maps.tristanhotham.com/portolan-charts/
Paper: https://doi.org/10.5281/zenodo.24044645
Blog post: https://blog.tristanhotham.com/2026/10/31/portolan-charts/
