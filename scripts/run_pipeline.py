"""Python mirror of gee/lulc_pipeline.js. Writes every Console number to results.json, plus map PNGs.

Usage: python scripts/run_pipeline.py <cloud-project> [out_dir]
"""
import json
import sys
import urllib.request
from pathlib import Path

import ee

PROJECT = sys.argv[1]
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else 'results')
OUT.mkdir(parents=True, exist_ok=True)
ee.Initialize(project=PROJECT)

ring = json.load(open(Path(__file__).parent.parent / 'data' / 'iitkgp_campus_osm.geojson'))['coordinates'][0]
aoi = ee.Geometry.Polygon([[[round(x, 5), round(y, 5)] for x, y in ring]])

EPOCHS = [
    {'label': 'Epoch1_2020', 'start': '2019-11-01', 'end': '2020-03-01'},
    {'label': 'Epoch2_2025', 'start': '2024-11-01', 'end': '2025-03-01'},
]
BANDS = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
CLOUD_AOI_MAX = 10
NAMES = ['Built-up', 'Vegetation', 'Open land', 'Water']
ORDER = [0, 1, 2, 3]
DW_FROM = [0, 1, 2, 3, 4, 5, 6, 7]
DW_TO = [3, 1, 2, 1, 2, 1, 0, 2]
DW_MIN_AGREEMENT = 0.6
CLASS_POINTS = [300, 700, 150, 40]


def add_aoi_cloud(img):
    scl = img.select('SCL')
    cloudy = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10))
    frac = cloudy.reduceRegion(reducer=ee.Reducer.mean(), geometry=aoi, scale=20, maxPixels=1e9).get('SCL')
    return img.set('aoi_cloud_pct', ee.Number(frac).multiply(100))


def prep(img):
    scl = img.select('SCL')
    good = scl.neq(1).And(scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return ee.Image(img.select(BANDS).resample('bilinear').updateMask(good).divide(10000)
                    .copyProperties(img, ['system:time_start']))


def composite(ep, report):
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(aoi).filterDate(ep['start'], ep['end'])
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
           .map(add_aoi_cloud)
           .filter(ee.Filter.lt('aoi_cloud_pct', CLOUD_AOI_MAX)))
    scenes = ee.FeatureCollection(col.map(lambda i: ee.Feature(None, {
        'date': i.date().format('YYYY-MM-dd'), 'tile': i.get('MGRS_TILE'),
        'tile_cloud_pct': i.get('CLOUDY_PIXEL_PERCENTAGE'), 'aoi_cloud_pct': i.get('aoi_cloud_pct')})))
    report['scenes'] = [f['properties'] for f in scenes.getInfo()['features']]
    comp = col.map(prep).median().clip(aoi)
    return (comp.addBands(comp.normalizedDifference(['B8', 'B4']).rename('NDVI'))
                .addBands(comp.normalizedDifference(['B11', 'B8']).rename('NDBI'))
                .addBands(comp.normalizedDifference(['B3', 'B8']).rename('NDWI')))


def dw_reference(ep):
    dw = (ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
          .filterBounds(aoi).filterDate(ep['start'], ep['end']).select('label')
          .map(lambda i: i.remap(DW_FROM, DW_TO)))
    mode = dw.mode()
    agreement = dw.map(lambda i: i.eq(mode)).mean()
    return mode.int().rename('class').updateMask(agreement.gte(DW_MIN_AGREEMENT)).clip(aoi)


def accuracy(cm):
    return ee.Dictionary({
        'matrix': cm.array(), 'overall': cm.accuracy(), 'kappa': cm.kappa(),
        'producers': cm.producersAccuracy(), 'users': cm.consumersAccuracy()}).getInfo()


def labelled_samples(ep, year, report):
    stack = composite(ep, report)
    samples = stack.addBands(dw_reference(ep)).stratifiedSample(
        numPoints=0, classBand='class', classValues=ORDER, classPoints=CLASS_POINTS,
        region=aoi, scale=10, seed=42, geometries=True, tileScale=4
    ).randomColumn('r', 42).map(lambda f: f.set('year', year))
    report['samples_per_class'] = samples.aggregate_histogram('class').getInfo()
    return stack, samples


def area_table(img, field):
    groups = ee.List(ee.Image.pixelArea().divide(10000).addBands(img).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName=field),
        geometry=aoi, scale=10, maxPixels=1e9).get('groups'))
    return groups.getInfo()


def thumb(img, vis, name):
    url = img.getThumbURL({**vis, 'region': aoi, 'dimensions': 1400, 'format': 'png'})
    urllib.request.urlretrieve(url, OUT / f'{name}.png')


results = {'campus_ha': aoi.area(1).divide(10000).getInfo(), '2020': {}, '2025': {}}
s1, samp1 = labelled_samples(EPOCHS[0], 2020, results['2020'])
s2, samp2 = labelled_samples(EPOCHS[1], 2025, results['2025'])
pooled = samp1.merge(samp2)
train = pooled.filter(ee.Filter.lt('r', 0.7))
holdout = pooled.filter(ee.Filter.gte('r', 0.7))
results['train'], results['holdout'] = train.size().getInfo(), holdout.size().getInfo()
rf = ee.Classifier.smileRandomForest(numberOfTrees=100, seed=42).train(
    features=train, classProperty='class', inputProperties=s1.bandNames())
results['importance'] = ee.Dictionary(rf.explain().get('importance')).getInfo()
tested = holdout.classify(rf)
for year in (2020, 2025):
    results[str(year)]['dw_holdout_accuracy'] = accuracy(
        tested.filter(ee.Filter.eq('year', year)).errorMatrix('class', 'classification', ORDER))
results['dw_holdout_accuracy_pooled'] = accuracy(tested.errorMatrix('class', 'classification', ORDER))
# 3x3 majority filter removes isolated pixels before anything is measured.
m1 = s1.classify(rf).focalMode(1, 'square', 'pixels').rename('class')
m2 = s2.classify(rf).focalMode(1, 'square', 'pixels').rename('class')

results['2020']['area_ha'] = area_table(m1, 'class')
results['2025']['area_ha'] = area_table(m2, 'class')
# Change has to survive a 1-pixel erosion. Strips under 30 m wide are roof edges
# shifting between the two composites, not change.
raw_change = m1.neq(m2)
changed = raw_change.focalMin(1, 'square', 'pixels').focalMax(1, 'square', 'pixels').And(raw_change)
code = m1.multiply(10).add(m1.where(changed, m2)).rename('code')
results['transitions_ha'] = area_table(code, 'code')
results['changed_ha'] = area_table(changed.rename('changed'), 'changed')
results['changed_ha_before_mmu'] = area_table(raw_change.rename('changed'), 'changed')
json.dump(results, open(OUT / 'results.json', 'w'), indent=1)

pal = ['d73027', '1a9850', 'e6d98a', '2c7fb8']
outline = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(aoi)]), 1, 2).visualize(palette=['000000'])
for stack, year in ((s1, 2020), (s2, 2025)):
    tc = stack.visualize(bands=['B4', 'B3', 'B2'], min=0.02, max=0.25)
    thumb(tc.blend(outline), {}, f'true_colour_{year}')
lulc_vis = dict(min=0, max=3, palette=pal)
thumb(m1.visualize(**lulc_vis).blend(outline), {}, 'lulc_2020')
thumb(m2.visualize(**lulc_vis).blend(outline), {}, 'lulc_2025')
base = s2.visualize(bands=['B4', 'B3', 'B2'], min=0.02, max=0.25).multiply(0.5).uint8()
thumb(base.blend(changed.selfMask().visualize(palette=['ff00ff'])).blend(outline), {}, 'change_2020_2025')
print('wrote', OUT.resolve())
