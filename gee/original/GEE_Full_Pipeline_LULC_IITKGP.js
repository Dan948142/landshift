// =====================================================================
// LULC change detection - IIT Kharagpur campus (Sentinel-2)
// Steps: composites -> classify (Random Forest) -> accuracy -> change
//
// BEFORE RUNNING you need these imports (top of editor, from drawing):
//   FeatureCollections of POINTS, each with a property named  class
//   built20, veg20, open20, water20   (epoch 1, year 2020)
//   built25, veg25, open25, water25   (epoch 2, year 2025)
//   class values: built-up=0, vegetation=1, open land=2, water=3
// If you drew your own campus polygon and named it `aoi`, DELETE the
// "var aoi" line below.
// =====================================================================

var aoi = ee.Geometry.Point([87.3105, 22.3149]).buffer(1500).bounds(); // PLACEHOLDER

var EPOCHS = [
  {label: 'Epoch1_2020', start: '2019-11-01', end: '2020-02-29'},
  {label: 'Epoch2_2025', start: '2024-11-01', end: '2025-02-28'}
];
var BANDS = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12'];
var CLOUD_AOI_MAX = 10;

// ---------- Acquisition ----------
function addAoiCloud(img) {
  var scl = img.select('SCL');
  var cloudy = scl.eq(3).or(scl.eq(8)).or(scl.eq(9)).or(scl.eq(10));
  var frac = cloudy.reduceRegion({reducer: ee.Reducer.mean(), geometry: aoi, scale: 20, maxPixels: 1e9}).get('SCL');
  return img.set('aoi_cloud_pct', ee.Number(frac).multiply(100));
}
function prep(img) {
  var scl = img.select('SCL');
  var good = scl.neq(1).and(scl.neq(3)).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10));
  return img.select(BANDS).resample('bilinear').updateMask(good).divide(10000)
            .copyProperties(img, ['system:time_start']);
}
function makeComposite(ep) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi).filterDate(ep.start, ep.end)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .map(addAoiCloud)
    .filter(ee.Filter.lt('aoi_cloud_pct', CLOUD_AOI_MAX));
  print(ep.label + ': number of scenes', col.size());
  print(ep.label + ': scene details', ee.FeatureCollection(col.map(function (i) {
    return ee.Feature(null, {date: i.date().format('YYYY-MM-dd'), tile: i.get('MGRS_TILE'),
      tile_cloud_pct: i.get('CLOUDY_PIXEL_PERCENTAGE'), aoi_cloud_pct: i.get('aoi_cloud_pct')});
  })));
  return col.map(prep).median().clip(aoi);
}

// ---------- Classification ----------
function setClass(fc, v) { return ee.FeatureCollection(fc).map(function (f) { return f.set('class', v); }); }

function classify(comp, label, b, v, o, w) {
  var stack = comp
    .addBands(comp.normalizedDifference(['B8','B4']).rename('NDVI'))
    .addBands(comp.normalizedDifference(['B11','B8']).rename('NDBI'))
    .addBands(comp.normalizedDifference(['B3','B8']).rename('NDWI'));
  var bands = stack.bandNames();

  var pts = setClass(b, 0).merge(setClass(v, 1)).merge(setClass(o, 2)).merge(setClass(w, 3));
  var data = stack.sampleRegions({collection: pts, properties: ['class'], scale: 10, tileScale: 4})
                  .randomColumn('r', 42);
  var train = data.filter(ee.Filter.lt('r', 0.7));
  var test  = data.filter(ee.Filter.gte('r', 0.7));
  print(label + ': training / validation points', train.size(), test.size());

  var rf = ee.Classifier.smileRandomForest(100).train({
    features: train, classProperty: 'class', inputProperties: bands});
  var map = stack.classify(rf).rename('class');

  var cm = test.classify(rf).errorMatrix('class', 'classification');
  print(label + ': confusion matrix (rows=reference, cols=predicted; 0 built,1 veg,2 open,3 water)', cm);
  print(label + ': overall accuracy', cm.accuracy());
  print(label + ': kappa', cm.kappa());
  print(label + ': producer accuracy', cm.producersAccuracy());
  print(label + ': user accuracy', cm.consumersAccuracy());
  return map;
}

function areaByClass(img, label) {
  var r = ee.Image.pixelArea().divide(10000).addBands(img).reduceRegion({
    reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'class'}),
    geometry: aoi, scale: 10, maxPixels: 1e9});
  print(label, r);
}

// ---------- Run ----------
var comp1 = makeComposite(EPOCHS[0]);
var comp2 = makeComposite(EPOCHS[1]);
var map1 = classify(comp1, 'Epoch1_2020', built20, veg20, open20, water20);
var map2 = classify(comp2, 'Epoch2_2025', built25, veg25, open25, water25);

areaByClass(map1, 'Area (ha) by class, 2020');
areaByClass(map2, 'Area (ha) by class, 2025');

// Change: code = 10*class2020 + class2025  (e.g. 12 = vegetation(1) -> open(2)... read as "from"+"to")
var code = map1.multiply(10).add(map2).rename('code');
areaByClass(code, 'From-To change area (ha). code = [class2020][class2025]');
var changed = map1.neq(map2).rename('changed');
areaByClass(changed, 'Changed (1) vs unchanged (0) area, ha');

// ---------- Display ----------
var pal = ['d73027', '1a9850', 'e6d98a', '2c7fb8'];  // built, veg, open, water
Map.centerObject(aoi, 14);
Map.addLayer(comp1, {bands: ['B4','B3','B2'], min: 0.02, max: 0.25}, 'True colour 2020', false);
Map.addLayer(comp2, {bands: ['B4','B3','B2'], min: 0.02, max: 0.25}, 'True colour 2025', false);
Map.addLayer(map1, {min: 0, max: 3, palette: pal}, 'LULC 2020');
Map.addLayer(map2, {min: 0, max: 3, palette: pal}, 'LULC 2025');
Map.addLayer(changed.selfMask(), {palette: ['ff00ff']}, 'Changed pixels');

// ---------- Export (then press Run in Tasks tab) ----------
function exp(img, name) {
  Export.image.toDrive({image: img.toFloat(), description: name, folder: 'GEE_LULC',
    fileNamePrefix: name, region: aoi, scale: 10, crs: 'EPSG:32645', maxPixels: 1e9});
}
exp(comp1, 'S2_composite_2020'); exp(comp2, 'S2_composite_2025');
exp(map1, 'LULC_2020'); exp(map2, 'LULC_2025'); exp(changed, 'LULC_change_2020_2025');
