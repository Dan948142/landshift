"""Draw the stratified random validation sample from the class maps in results/.

Usage: python scripts/sample_validation_points.py [repo_dir] [out.csv]

Strata are the map classes in results/lulc_<year>.png (EPSG:4326 thumbnails of the 3x3-filtered maps).
Built-up, vegetation, open land: 40 random points each, at least 40 m apart and 20 m inside the fence.
Water: every map-water location at least 12 m apart, because the map has only about 0.9 ha of it.
Order is shuffled so the map class cannot be guessed while labelling. The labelled result is validation/points.csv.
"""
import csv
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else REPO / 'validation' / 'candidates.csv')
SEED = 20201003
TARGET = {0: 40, 1: 40, 2: 40}
SPACING = {0: 40.0, 1: 40.0, 2: 40.0, 3: 12.0}
PAL = {0: (0xd7, 0x30, 0x27), 1: (0x1a, 0x98, 0x50), 2: (0xe6, 0xd9, 0x8a), 3: (0x2c, 0x7f, 0xb8)}
M_LAT = 110_757.0
M_LON = 111_320.0 * math.cos(math.radians(22.3145)) * 1.0033

# Same polygon as the pipeline: OSM way 52435606 rounded to 5 decimals.
ring = [(round(x, 5), round(y, 5)) for x, y in
        json.load(open(REPO / 'data' / 'iitkgp_campus_osm.geojson'))['coordinates'][0]]
LON0, LON1 = min(p[0] for p in ring), max(p[0] for p in ring)
LAT0, LAT1 = min(p[1] for p in ring), max(p[1] for p in ring)
edges = list(zip(ring, ring[1:] + ring[:1]))


def inside(lon, lat):
    hit = False
    for (x1, y1), (x2, y2) in edges:
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def to_fence_m(lon, lat):
    px, py, best = lon * M_LON, lat * M_LAT, 1e18
    for (x1, y1), (x2, y2) in edges:
        ax, ay, dx, dy = x1 * M_LON, y1 * M_LAT, (x2 - x1) * M_LON, (y2 - y1) * M_LAT
        t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def dist_m(p, q):
    return float(np.hypot((p[0] - q[0]) * M_LON, (p[1] - q[1]) * M_LAT))


def class_map(year):
    """Class per thumbnail pixel (-1 for outline, outside and blended edge pixels)."""
    a = np.asarray(Image.open(REPO / 'results' / f'lulc_{year}.png').convert('RGBA'), float)
    d = np.stack([np.linalg.norm(a[..., :3] - np.array(PAL[c]), axis=-1) for c in range(4)])
    cls = d.argmin(0)
    cls[(d.min(0) >= 40) | (a[..., 3] <= 200)] = -1
    return cls


maps = {y: class_map(y) for y in ('2020', '2025')}
H, W = maps['2020'].shape


def map_class(year, lon, lat):
    i, j = int((lon - LON0) / (LON1 - LON0) * W), int((LAT1 - lat) / (LAT1 - LAT0) * H)
    return int(maps[year][j, i]) if 0 <= i < W and 0 <= j < H else -1


rng = random.Random(SEED)
cands = []
while len(cands) < 30000:
    lon, lat = rng.uniform(LON0, LON1), rng.uniform(LAT0, LAT1)
    if inside(lon, lat) and to_fence_m(lon, lat) >= 20:
        cands.append((lon, lat))

rows = []
for year in ('2020', '2025'):
    chosen, counts = [], {0: 0, 1: 0, 2: 0}
    for lon, lat in cands:
        c = map_class(year, lon, lat)
        if c in TARGET and counts[c] < TARGET[c] and all(dist_m((lon, lat), q) >= SPACING[c] for q in chosen):
            chosen.append((lon, lat, c))
            counts[c] += 1
    jj, ii = np.nonzero(maps[year] == 3)
    water_px = [(LON0 + (i + 0.5) / W * (LON1 - LON0), LAT1 - (j + 0.5) / H * (LAT1 - LAT0)) for j, i in zip(jj, ii)]
    rng.shuffle(water_px)
    water = []
    for lon, lat in water_px:
        if inside(lon, lat) and to_fence_m(lon, lat) >= 20 and all(dist_m((lon, lat), q) >= SPACING[3] for q in water):
            water.append((lon, lat, 3))
    pts = chosen + water
    rng.shuffle(pts)
    print(year, 'per map class', counts, 'water', len(water))
    for k, (lon, lat, c) in enumerate(pts, 1):
        rows.append({'id': f'P{year[2:]}-{k:03d}', 'year': year, 'lon': f'{lon:.6f}', 'lat': f'{lat:.6f}', 'map_class': c})

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print('wrote', len(rows), 'points to', OUT)
