# LULC Mapping and Change Detection, IIT Kharagpur Campus (2020 vs 2025)

CS60111 Geographical Information System, Autumn 2026-27. Term project 3, Group 8.

Two-date land use / land cover map of the IIT Kharagpur campus from Sentinel-2,
and the change between them. Everything runs in Google Earth Engine from one script.

## Study area

Campus boundary is OpenStreetMap way [52435606](https://www.openstreetmap.org/way/52435606)
("Indian Institute of Technology Kharagpur"), 184 vertices, about 469 ha.
It is embedded in the script and also kept as `data/iitkgp_campus_osm.geojson`.
The OSM polygon covers the main fenced campus. Halls and quarters outside that fence are not in it.

## Data

| Item | Value |
|---|---|
| Imagery | Sentinel-2 L2A, `COPERNICUS/S2_SR_HARMONIZED`, 10 bands (B2-B8A, B11, B12) |
| Epoch 1 | 1 Nov 2019 to 29 Feb 2020 (dry season) |
| Epoch 2 | 1 Nov 2024 to 28 Feb 2025 (same season, so phenology does not show up as change) |
| Scene filter | tile cloud < 40 %, then cloud inside the campus < 10 % (from the SCL band) |
| Training labels | Dynamic World V1 (`GOOGLE/DYNAMICWORLD/V1`), modal label over the same window |
| Projection for exports | UTM 45N, EPSG:32645, 10 m |

## Classes

| Code | Class | What goes in it | Dynamic World labels mapped here |
|---|---|---|---|
| 0 | Built-up | Roofs, roads, paved courts, parking | built |
| 1 | Vegetation | Tree canopy, shrubs, crop or flooded vegetation | trees, shrub and scrub, crops, flooded vegetation |
| 2 | Open land | Bare soil, playgrounds, lawns, construction sites without a roof yet | grass, bare |
| 3 | Water | Ponds, tanks, open drains wide enough to fill a 10 m pixel | water |

Grass is counted as open land on purpose. On campus it is almost all lawns and sports
fields, and putting it in vegetation would make the tree-loss signal disappear.

## Method

1. Median composite per epoch after masking cloud, cloud shadow, cirrus and saturated pixels (SCL 1, 3, 8, 9, 10).
2. Add NDVI, NDBI and NDWI to the 10 reflectance bands.
3. Reference labels: Dynamic World mode over the epoch, kept only where at least 70 % of the
   Dynamic World scenes agree with the mode. This drops pixels that flicker between classes.
4. Stratified sample, up to 200 pixels per class, split 70 / 30.
5. Random Forest, 100 trees, seed 42, trained separately for each epoch.
6. Accuracy, two ways:
   - Holdout agreement with Dynamic World. Not independent, because the labels and the test pixels come from the same product and the same area.
   - Hand-labelled points (when imported): 25+ per class per year, read off Google Earth historical
     imagery for 2020 and current imagery for 2025. These are the numbers to quote in the report.
7. Post-classification change: `code = 10 * class2020 + class2025`, so `12` is vegetation to open land.
   Area per class, the full from-to table and changed vs unchanged area are printed and exported as CSV.

## Running it

1. Open <https://code.earthengine.google.com> (needs a registered noncommercial account).
2. Paste `gee/lulc_pipeline.js`, press **Run**. No drawing needed.
3. Console: scene tables, sample counts, confusion matrices, OA, kappa, PA, UA, areas, transitions.
4. Tasks tab: run the exports. Everything goes to `Drive/GEE_LULC/`.

Optional independent validation: in the same script, add point layers named
`built20, veg20, open20, water20, built25, veg25, open25, water25` (import as FeatureCollection).
The script picks them up automatically; no `class` property is needed.

## Outputs

| File | Content |
|---|---|
| `S2_composite_2020.tif`, `S2_composite_2025.tif` | 10-band reflectance composites |
| `LULC_2020.tif`, `LULC_2025.tif` | Class maps, values 0-3 |
| `LULC_transition_code.tif` | From-to code per pixel |
| `area_2020.csv`, `area_2025.csv` | Hectares per class |
| `transitions_2020_2025.csv` | Hectares per from-to pair |

## Known limits

- Change accuracy is not measured. Two maps at about 85 % each can give a change map near 72 %, so small
  transitions (a few hectares) are within error.
- 10 m pixels mix roof and canopy along tree-lined roads. Expect built-up / vegetation confusion there.
- Dry-season haze is not masked by SCL. The 10 % in-campus cloud filter helps, but it is not a haze filter.

## Repository layout

```
gee/lulc_pipeline.js      the pipeline (current)
gee/original/             first drafts of the acquisition and classification scripts, kept for history
data/                     campus boundary from OSM
```

## Team and contributions

| Member | Roll no. | Contribution so far |
|---|---|---|
| Ashutosh Sharma | 23CS10005 | Topic selection and group registration; revised pipeline (OSM boundary, Dynamic World training, independent validation hook, area and transition exports); repository and documentation |
| Krishnkant Sahu | 23CS10035 | |
| Sanskar Sovitkar | 24CS10131 | First drafts of the GEE scripts in `gee/original/`; initial task breakdown |
