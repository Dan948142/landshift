"""Validation points from validation/points.csv -> GEE point layers and a location figure.

Usage: python scripts/export_validation.py [repo_dir] [--bare]
Writes gee/validation_points.js (built20 ... water25, paste above gee/lulc_pipeline.js)
and docs/img/08_validation_points.png. Points labelled "excluded" are left out of the layers.
--bare drops the figure title and footer, as in make_figures.py.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO = Path(next((a for a in sys.argv[1:] if not a.startswith('--')), '.'))
BARE = '--bare' in sys.argv
rows = list(csv.DictReader(open(REPO / 'validation' / 'points.csv')))
CLASSES = ['built-up', 'vegetation', 'open land', 'water']
LAYER = ['built', 'veg', 'open', 'water']
GEE_COLOR = ['d73027', '1a9850', 'e6d98a', '2c7fb8']

lines = [
    '// Independent validation points for gee/lulc_pipeline.js (CS60111 GIS, Group 8).',
    '// Paste this whole file above the pipeline in one Code Editor script; the pipeline picks up these',
    '// eight layers and prints the "[hand-labelled, independent]" confusion matrices for both years.',
    '// 2020: labelled on WorldView-2, 15 Mar 2020. 2025: WorldView-3, 13 Jan 2024, checked against the',
    '// Sentinel-2 2024-25 composite. Imagery: Esri World Imagery Wayback. Notes: validation/NOTES.md.',
    '// Generated from validation/points.csv by scripts/export_validation.py; edit the CSV, not this file.',
    '',
]
for year in ('2020', '2025'):
    for k, cls in enumerate(CLASSES):
        pts = [r for r in rows if r['year'] == year and r['label'] == cls]
        feats = ',\n'.join(f"  ee.Feature(ee.Geometry.Point([{r['lon']}, {r['lat']}]), {{id: '{r['id']}'}})" for r in pts)
        lines.append(f'// {cls}, {year}: {len(pts)} points')
        lines.append(f'var {LAYER[k]}{year[2:]} = /* color: #{GEE_COLOR[k]} */ee.FeatureCollection([\n{feats}\n]);')
    lines.append('')
(REPO / 'gee' / 'validation_points.js').write_text('\n'.join(lines), encoding='utf-8')
for year in ('2020', '2025'):
    n = Counter(r['label'] for r in rows if r['year'] == year)
    print(year, {c: n[c] for c in CLASSES + ['excluded']})

# Location figure. Hues follow the class maps; lightness is adjusted so the four classes stay apart
# for colour-blind readers (checked with the dataviz palette validator), and each class has its own marker.
plt.rcParams.update({'font.family': ['Avenir', 'Avenir Next', 'DejaVu Sans'], 'font.size': 12, 'axes.titlesize': 14})
COLS = ['#e8553a', '#0d6332', '#c9b04f', '#2a78b5']
MARK = ['s', '^', 'o', 'D']
INK, MUTED, FILL = '#1f2a30', '#5b6770', '#eef0ee'
FOOT = 'CS60111 GIS  |  Group 8  |  github.com/ashuwhy/landshift'
SUB = {'2020': 'WorldView-2, 15 Mar 2020', '2025': 'WorldView-3, 13 Jan 2024 + Sentinel-2 2024-25'}
ring = json.load(open(REPO / 'data' / 'iitkgp_campus_osm.geojson'))['coordinates'][0]

fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
for ax, year in zip(axes, ('2020', '2025')):
    ax.fill([p[0] for p in ring], [p[1] for p in ring], color=FILL, zorder=0)
    ax.plot([p[0] for p in ring], [p[1] for p in ring], color=INK, lw=1, zorder=1)
    used = [r for r in rows if r['year'] == year and r['label'] != 'excluded']
    for k, cls in enumerate(CLASSES):
        pts = [r for r in used if r['label'] == cls]
        ax.scatter([float(r['lon']) for r in pts], [float(r['lat']) for r in pts], s=34, marker=MARK[k],
                   c=COLS[k], edgecolors=INK, linewidths=0.6, zorder=2 + k)
    out = [r for r in rows if r['year'] == year and r['label'] == 'excluded']
    if out:
        ax.scatter([float(r['lon']) for r in out], [float(r['lat']) for r in out], s=40, marker='x', c=MUTED,
                   linewidths=1.4, zorder=6)
    ax.set_title(f'{year}: {len(used)} points\n{SUB[year]}', color=INK, fontsize=13)
    ax.set_aspect(1)  # plain lon/lat, like the EPSG:4326 class maps in results/
    ax.axis('off')
handles = [Line2D([], [], ls='', marker=MARK[k], ms=8, mfc=COLS[k], mec=INK, mew=0.6, label=c.capitalize())
           for k, c in enumerate(CLASSES)]
handles.append(Line2D([], [], ls='', marker='x', ms=8, mec=MUTED, mew=1.4, label='Excluded (no imagery from the epoch)'))
fig.legend(handles=handles, loc='lower center', ncol=5, frameon=False, bbox_to_anchor=(0.5, 0.05))
fig.subplots_adjust(left=0.01, right=0.99, top=0.8, bottom=0.16, wspace=0.04)
if not BARE:
    fig.suptitle('Independent validation points, labelled on high-resolution imagery', x=0.02, ha='left',
                 fontsize=19, fontweight='heavy', color=INK)
    fig.text(0.02, 0.015, FOOT, fontsize=10, color=MUTED)
fig.savefig(REPO / 'docs' / 'img' / '08_validation_points.png', dpi=150, facecolor='white')
print('wrote gee/validation_points.js and docs/img/08_validation_points.png')
