# LULC Mapping and Change Detection, IIT Kharagpur Campus (2020 vs 2025)

CS60111 Geographical Information System, Autumn 2026-27. Term project 3, Group 8.

Two-date land use / land cover map of the IIT Kharagpur campus from Sentinel-2,
and the change between them. Everything runs in Google Earth Engine from one script.

![Change 2020 to 2025](docs/img/04_change_2020_2025.png)

Magenta: pixels whose class changed between 2020 and 2025 and that belong to a changed patch at least 30 m wide.
The large block in the south-east is the construction compound that does not exist in the 2020 image.

## Study area

Campus boundary is OpenStreetMap way [52435606](https://www.openstreetmap.org/way/52435606)
("Indian Institute of Technology Kharagpur"), 184 vertices, 469.2 ha.
It is embedded in the script and also kept as `data/iitkgp_campus_osm.geojson`.
The OSM polygon covers the main fenced campus. Halls and quarters outside that fence are not in it.

## Data

| Item | Value |
|---|---|
| Imagery | Sentinel-2 L2A, `COPERNICUS/S2_SR_HARMONIZED`, 10 bands (B2-B8A, B11, B12), tile 45QWE |
| Epoch 1 | 1 Nov 2019 to 29 Feb 2020 (dry season), 11 scenes |
| Epoch 2 | 1 Nov 2024 to 28 Feb 2025 (same season, so phenology does not show up as change), 16 scenes |
| Scene filter | tile cloud < 40 %, then cloud inside the campus < 10 % (from the SCL band) |
| Training labels | Dynamic World V1 (`GOOGLE/DYNAMICWORLD/V1`), modal label over the same window |
| Projection for exports | UTM 45N, EPSG:32645, 10 m |

![Sentinel-2 composites](docs/img/01_sentinel2_composites.png)

## Classes

| Code | Class | What goes in it | Dynamic World labels mapped here |
|---|---|---|---|
| 0 | Built-up | Roofs, roads, paved courts, parking | built |
| 1 | Vegetation | Tree canopy, shrubs, flooded vegetation | trees, shrub and scrub, flooded vegetation |
| 2 | Open land | Lawns, playgrounds, bare soil, cleared plots | grass, crops, bare |
| 3 | Water | Ponds, tanks, open drains wide enough to fill a 10 m pixel | water |

Dynamic World almost never says "grass" on this campus (0.6 ha in 2020). It labels the lawns and
sports fields as crops, about 50 ha in 2020. There is no farmland inside the fence, so crops go to open land.
Putting them in vegetation would hide exactly the open-to-built conversions this project is looking for.

## Method

1. Median composite per epoch after masking cloud, cloud shadow, cirrus and saturated pixels (SCL 1, 3, 8, 9, 10).
2. Add NDVI, NDBI and NDWI to the 10 reflectance bands.
3. Reference labels: every Dynamic World scene is mapped to the four classes, then the mode is taken.
   A pixel is kept only where at least 60 % of the scenes agree with the mode, which drops pixels that flicker.
4. Stratified sample per epoch: 300 built-up, 700 vegetation, 150 open land, 40 water (water has only
   about 40 pixels on campus). These counts roughly follow the class shares. With equal counts per class the
   forest put 224 ha of the campus in built-up when Dynamic World itself says about 110.
5. One Random Forest (100 trees, seed 42) trained on the 70 % training split of both epochs together and applied
   to both composites. Two separately trained forests disagree on the same unchanged pixel, and that disagreement
   shows up as fake change. A first run done that way reported 91 ha of built-up turning into vegetation.
6. 3x3 majority filter on both class maps.
7. Accuracy, two ways:
   - Holdout agreement with Dynamic World (the other 30 %). Not independent, because the labels and the test pixels come from the same product.
   - Independent points (`gee/validation_points.js`): 181 for 2020 and 184 for 2025, at least 25 per class per year.
     A stratified random sample on the map classes, labelled on WorldView-2 imagery of 15 Mar 2020 and WorldView-3
     imagery of 13 Jan 2024 (Esri World Imagery Wayback). These are the numbers to quote in the report.
     Imagery, labelling rules and hard cases are in `validation/NOTES.md`.
8. Post-classification change: `code = 10 * class2020 + class2025`, so `12` is vegetation to open land.
   A changed pixel only counts if it survives a one-pixel erosion of the change mask (then dilated back),
   so changed strips narrower than about 30 m are dropped. Without this every roof gets a ring of change
   from the one-pixel boundary shift between the two composites.

## Results

All numbers come from `results/results.json`, written by `scripts/run_pipeline.py`.

![LULC 2020 and 2025](docs/img/02_lulc_maps.png)

### Area by class (ha)

| Class | 2020 | 2025 | Difference |
|---|---|---|---|
| Built-up | 99.7 | 100.8 | +1.1 |
| Vegetation | 335.2 | 344.1 | +8.9 |
| Open land | 32.1 | 22.2 | -9.9 |
| Water | 0.9 | 0.9 | 0.0 |

The classes add up to 467.9 ha against the 469.2 ha polygon; the rest is boundary pixels whose centre falls outside it.

### Change, 2020 to 2025 (ha)

48.6 ha changed (10.4 % of the campus); 80.3 ha before the 30 m filter.

| From | To | ha | What it is on the ground |
|---|---|---|---|
| Vegetation | Built-up | 15.8 | Mostly the south-east construction compound (11.3 ha in that quarter of the campus); median NDVI falls from 0.40 to 0.19 |
| Built-up | Vegetation | 15.0 | Pixels that really got greener (NDVI 0.31 to 0.45), but the 2020 "built-up" label there is largely canopy-over-roof and dry scrub in the east end. Read as greening, not demolition |
| Open land | Vegetation | 6.4 | Scrub regrowth in the east end, greener sports fields |
| Open land | Built-up | 6.2 | Cleared plots that got buildings |
| Vegetation | Open land | 3.1 | Clearing |
| Built-up | Open land | 2.0 | |
| Water | any | 0.1 | |

### Accuracy

Against the independent points (181 for 2020, 184 for 2025, `validation/`), on the filtered maps the areas come from.
The sample is stratified by map class, so every estimate is weighted by map-class area (Olofsson et al. 2014);
raw point counts would let water, 0.2 % of the campus and a third of the points, set the score.

| | 2020 | 2025 |
|---|---|---|
| Overall accuracy (95 % CI) | 0.61 (0.49-0.72) | 0.74 (0.65-0.84) |
| User's accuracy (built / veg / open / water) | 0.49 / 0.61 / 0.89 / 0.84 | 0.41 / 0.84 / 0.86 / 0.74 |
| Producer's accuracy (built / veg / open / water) | 0.49 / 0.92 / 0.22 / 0.15 | 0.76 / 0.91 / 0.18 / 0.89 |
| Open land, mapped / estimated (95 % CI), ha | 32 / 146 (98-194) | 22 / 96 (56-135) |

![Confusion matrices](docs/img/05_accuracy.png)

The map misses most open land. Lawns, sports fields and clearings among trees go to vegetation or built-up, so
open land is mapped at about a fifth of its estimated area and vegetation is overstated, most in 2020.
Built-up spreads onto lawns and courtyards next to buildings (user's accuracy 0.41-0.49).
Producer's accuracy for water rests on a handful of points in large strata and means little.

Holdout agreement with Dynamic World is 0.84 for both years (kappa 0.70 and 0.73, 707 holdout pixels).
That is agreement with the training source, and the gap to the numbers above is the point of the independent check.
The Code Editor prints the unweighted matrices on the unfiltered classification (OA 0.68 / 0.64, kappa 0.58 / 0.52);
`scripts/run_pipeline.py` writes both to `results.json`.
Most useful inputs (Random Forest importance): NDWI, B12, B11, B4, B8A.

## Running it

Earth Engine Code Editor:

1. Open <https://code.earthengine.google.com> (needs a registered noncommercial Cloud project).
2. Paste `gee/lulc_pipeline.js`, press **Run**. No drawing needed.
3. Console: scene tables, sample counts, confusion matrices, OA, kappa, PA, UA, areas, transitions.
4. Tasks tab: run the exports. Everything goes to `Drive/GEE_LULC/`.

![Pipeline in the Code Editor](docs/img/06_code_editor_map.jpg)

Class maps with the change layer (magenta) on top, after a run.

Python, same pipeline, writes `results/`:

```bash
pip install -r scripts/requirements.txt
earthengine authenticate
python scripts/run_pipeline.py <your-cloud-project>
python scripts/make_figures.py . docs/img
```

Independent validation: paste `gee/validation_points.js` above the pipeline in the same Code Editor script.
It defines the point layers `built20, veg20, open20, water20, built25, veg25, open25, water25`; the script
picks them up and prints the independent confusion matrices. See `validation/NOTES.md`.

## Outputs

| File | Content |
|---|---|
| `results/results.json` | Scene lists, sample counts, confusion matrices, OA, kappa, PA, UA, importance, areas, from-to table |
| `results/*.png` | True colour composites, class maps, change map |
| `docs/img/` | Figures with titles and legends built from `results/` (README, slides), Code Editor screenshots |
| `S2_composite_2020.tif`, `S2_composite_2025.tif` | 10-band reflectance composites (Drive export) |
| `LULC_2020.tif`, `LULC_2025.tif` | Class maps, values 0-3 (Drive export) |
| `LULC_transition_code.tif` | From-to code per pixel (Drive export) |
| `area_2020.csv`, `area_2025.csv`, `transitions_2020_2025.csv` | Hectares per class and per from-to pair (Drive export) |

## Known limits

- Open land is badly under-mapped (producer's accuracy about 0.2). The class-area changes of 1-10 ha in the table above are
  smaller than the area error, so the change results rest on the large, checked transitions such as the south-east compound.
- Change accuracy is not measured. Two maps at 0.61 and 0.74 give a change map well below either.
- 10 m pixels mix roof and canopy along tree-lined roads and in the residential quarters. Most of the built-up / vegetation confusion is there.
- The 30 m filter also drops real change narrower than 30 m, for example a single new building on a lawn.
- Per-map class areas and the from-to table do not reconcile exactly, because the class areas still include the sub-30 m edge flips that the change filter drops.
- Dry-season haze is not masked by SCL. The 10 % in-campus cloud filter helps, but it is not a haze filter.

## Repository layout

```
gee/lulc_pipeline.js      the pipeline (Code Editor)
gee/original/             my first drafts of the acquisition and classification scripts, kept for history
gee/validation_points.js  independent validation points as the Code Editor layers built20 ... water25
scripts/run_pipeline.py   same pipeline through the Python API, writes results/
scripts/make_figures.py   titled figures from results/ into docs/img/
scripts/sample_validation_points.py  draws the validation sample from results/
scripts/export_validation.py         validation/points.csv -> gee/validation_points.js and the location figure
validation/               the validation points with labels and notes (points.csv), labelling notes (NOTES.md)
results/                  numbers and figures from the last run
docs/img/                 figures and screenshots used in this README
data/                     campus boundary from OSM
TASKS.md                  who does what before the mid-term
```

## Team and contributions

| Member | Roll no. | Contribution so far |
|---|---|---|
| Ashutosh Sharma | 23CS10005 | Earth Engine pipeline, from my first drafts (`gee/original/`) to `gee/lulc_pipeline.js`: cloud-masked Sentinel-2 composites, Dynamic World training labels, Random Forest, post-classification change. Diagnosed the first run (224 ha built-up, 139 ha of change) and fixed it: proportional sampling, one forest for both years, crops to open land, 30 m change filter. Python runner that reproduces every Console number. Both epochs run: class maps, areas, from-to table, accuracy. Change checked against NDVI. Area-weighted independent accuracy and area estimates from the validation points (Olofsson / Stehman estimators). Figures, this README, the mid-term deck |
| Krishnkant Sahu | 23CS10035 | Independent validation set: 365 points (181 for 2020, 184 for 2025, at least 25 per class per year), a stratified random sample on the map classes labelled on dated high-resolution imagery (WorldView-2, 15 Mar 2020; WorldView-3, 13 Jan 2024) after correcting its offset to Sentinel-2 (`gee/validation_points.js`, `validation/points.csv`). Labelling notes: imagery dates, rules, hard cases (south-east compound, shadows of the new buildings, algae-covered ponds, dark roofs) and a first look at the map errors (`validation/NOTES.md`). Sampling and export scripts, location figure |
| Sanskar Sovitkar | 24CS10131 | |
