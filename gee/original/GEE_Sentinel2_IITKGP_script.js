// =====================================================================
// LULC project - Sentinel-2 acquisition for IIT Kharagpur campus
// Paste into code.earthengine.google.com -> Run -> run the 2 export tasks
// =====================================================================

// ---------- 1. AREA OF INTEREST ----------
// PLACEHOLDER: ~1.5 km radius around the campus centre (approximate).
// Replace with your real campus boundary (draw a polygon named `aoi`
// or upload a shapefile) BEFORE using results in the report.
var aoi = ee.Geometry.Point([87.3105, 22.3149]).buffer(1500).bounds();

// ---------- 2. SETTINGS (edit as needed) ----------
var EPOCHS = [
  {label: 'Epoch1', start: '2019-11-01', end: '2020-02-29', name: 'S2_IITKGP_2020'},
  {label: 'Epoch2', start: '2024-11-01', end: '2025-02-28', name: 'S2_IITKGP_2025'}
];
var BANDS = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12'];
var CLOUD_AOI_MAX = 10;   // % cloud allowed inside AOI

// ---------- 3. FUNCTIONS ----------
function addAoiCloud(img) {
  var scl = img.select('SCL');
  var cloudy = scl.eq(3).or(scl.eq(8)).or(scl.eq(9)).or(scl.eq(10));
  var frac = cloudy.reduceRegion({
    reducer: ee.Reducer.mean(), geometry: aoi, scale: 20, maxPixels: 1e9
  }).get('SCL');
  return img.set('aoi_cloud_pct', ee.Number(frac).multiply(100));
}

function prep(img) {
  var scl = img.select('SCL');
  var good = scl.neq(1).and(scl.neq(3)).and(scl.neq(8))
                .and(scl.neq(9)).and(scl.neq(10));
  return img.select(BANDS)
            .resample('bilinear')
            .updateMask(good)
            .divide(10000)
            .copyProperties(img, ['system:time_start']);
}

function makeComposite(ep) {
  var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate(ep.start, ep.end)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
    .map(addAoiCloud)
    .filter(ee.Filter.lt('aoi_cloud_pct', CLOUD_AOI_MAX));

  print(ep.label + ': number of scenes', col.size());          // -> Table 2
  print(ep.label + ': scene details', ee.FeatureCollection(col.map(function (i) {
    return ee.Feature(null, {
      date: i.date().format('YYYY-MM-dd'),
      tile: i.get('MGRS_TILE'),
      tile_cloud_pct: i.get('CLOUDY_PIXEL_PERCENTAGE'),
      aoi_cloud_pct: i.get('aoi_cloud_pct')
    });
  })));
  return col.map(prep).median().clip(aoi);
}

// ---------- 4. BUILD, DISPLAY, EXPORT ----------
var trueColor  = {bands: ['B4','B3','B2'], min: 0.02, max: 0.25};
var falseColor = {bands: ['B8','B4','B3'], min: 0.02, max: 0.45};
Map.centerObject(aoi, 14);

EPOCHS.forEach(function (ep) {
  var comp = makeComposite(ep);
  Map.addLayer(comp, trueColor,  ep.label + ' true colour');
  Map.addLayer(comp, falseColor, ep.label + ' false colour', false);

  Export.image.toDrive({
    image: comp.toFloat(),
    description: ep.name,
    folder: 'GEE_LULC',
    fileNamePrefix: ep.name,
    region: aoi,
    scale: 10,
    crs: 'EPSG:32645',
    maxPixels: 1e9
  });
});
Map.addLayer(aoi, {color: 'red'}, 'AOI', true, 0.4);
