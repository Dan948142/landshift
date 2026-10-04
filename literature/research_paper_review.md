# Research Paper Analysis and Relevance to our Study

Review of the studies from various research papers

## 1. Overview

| Paper | Data | Area / period | Classes | Method | Reported accuracy |
|---|---|---|---|---|---|
| Tikuye et al. (2023) | Landsat 4-5 TM, 7 ETM+, 8 OLI | Upper Blue Nile Basin, Ethiopia; 1983, 2003, 2022 | 7 | Random Forest, post-classification comparison | OA 91 / 93 / 96 %, kappa 83 / 85 / 91 % |
| Abdi (2020) | Sentinel-2, 4 scenes (one per season) | Uppsala county, Sweden (10 × 12 km); 2017-18 | 8 | SVM, Random Forest, XGBoost, deep learning compared | OA: SVM 75.8, XGBoost 75.1, RF 73.9, DL 73.3 % |
| Alonso et al. (2021) | Sentinel-2 Level-2A, 12 monthly images | Galicia, Spain; 2019 | 8 | Random Forest per image, plurality voting, one common model, 20 m | OA 91.6 %, kappa 0.90 |
| Rynkiewicz et al. (2023), conference abstract | Sentinel-2 annual data, on Google Earth Engine | Łódź (Poland) and Viken (Norway); 2018-2021 | 3 change classes | Spectral signatures, then Random Forest | OA ≥ 0.97, kappa > 0.95 |
| Jagannathan et al. (2025) | Sentinel-2A/B, 10 m | Katpadi, Vellore (Tamil Nadu); 2017-2024 | 8 | IRUNet deep learning (InceptionResNetV2 + U-Net) with test-time augmentation | Pixel accuracy 98.21 %, F1 91.85 %, kappa 0.872 (as reported) |

The Rynkiewicz entry is based on the abstract only. The other four were reviewed from the full text.

**Common points across the studies**
- Random Forest is the most used classifier. It is simple, robust and needs little tuning.
- Sentinel-2 at 10-20 m with the red-edge and SWIR bands gives the best land cover separation.
- Built-up areas and bare or open land are the weakest classes in every study.
- Accuracy values are not comparable across studies: the classes, scale and validation method differ.
- Most studies work at regional or city scale. Few map a single campus at two dates.

---

## 2. Paper summaries

### 2.1 Tikuye et al. (2023): Land use and land cover change detection using Random Forest, Upper Blue Nile Basin, Ethiopia

**What they did.** Mapped the basin (about 176,000 km²) for 1983, 2003 and 2022 using Landsat and Random Forest, then compared the class areas between years.

| Item | Detail |
|---|---|
| Images | Jan-Mar dry season, cloud cover under 5 %, surface reflectance, median composites |
| Inputs | Blue, green, red, NIR, SWIR1, SWIR2, NDVI, NDWI, elevation and slope |
| Classes | Cultivated land, shrubland, grazing land, forest, built-up, bare land, water |
| Validation | 200 random points per year from Google Earth |
| Change method | Post-classification comparison (net area change per class) |

**Key results**
- Cultivated land grew from 75,634 to 123,175 km² (+47,541 km², +63 %).
- Built-up area grew from 618 to 2,395 km² (+1,777 km², +288 %).
- Shrubland fell from 68,080 to 36,419 km² (about -31,660 km²).
- Water bodies grew by 662 km² because of dams.
- Authors attribute the change to population growth and food demand.

**Relevance to our project:** same dry-season, low-cloud image choice, median composites, Random Forest with spectral indices, post-classification comparison and Google Earth validation. We differ in scale (10 m Sentinel-2, 469 ha campus, two dates) and in reporting a from-to table.

**Limitations**
- In 2022, 137 of the 200 points are cultivated land. Water, built-up and bare land have only about 3 points each, so their accuracies are unreliable.
- Google Earth reference imagery for 1983 is questionable.
- Net changes do not show which class turned into which (no from-to matrix).
- Small inconsistency: the discussion gives kappa 81 % for 1983, the abstract and table give 83 %.
- Classes mix land use and land cover.

---

### 2.2 Abdi (2020): Classification performance of ML algorithms in a boreal landscape using Sentinel-2

**What they did.** Compared SVM, Random Forest, XGBoost and deep learning on the same data. The question is which classifier works best, not how land changed.

| Item | Detail |
|---|---|
| Images | 4 Sentinel-2 scenes: 4 May, 6 July, 13 Nov 2017 and 27 Jan 2018, little or no cloud |
| Preprocessing | Sen2Cor to surface reflectance; 20 m bands resampled to 10 m (bilinear) |
| Inputs | 10 bands plus NDVI, MNDWI, NDBI (13 layers per scene, 52 in total) |
| Classes | Deciduous forest, coniferous forest, water, artificial, wetland, agriculture, clear cut, open land |
| Samples | 1,477 per class (11,816 total), 70 % training / 30 % evaluation, labels from aerial photos and the national land cover map |
| Accuracy method | Area-adjusted estimates with 95 % confidence intervals (Olofsson et al.) |

**Key results**
- Overall accuracy: SVM 0.758, XGBoost 0.751, Random Forest 0.739, deep learning 0.733. The gaps are small and only some pairs differ significantly.
- Weakest classes: open land and artificial surfaces (producer's accuracy about 0.36-0.49), because of mixed pixels and similarity to clear cuts.
- Red-edge (25 %) and SWIR (23 %) bands were the most important. May and July scenes dominated.
- The indices (NDVI, MNDWI, NDBI) ranked low, because the red-edge bands already carry that information.
- Accuracy stopped improving after about six layers, so one well-timed scene may match a multi-date stack.

**Relevance to our project:** supports our 10 bands, bilinear 20 m to 10 m resampling and the choice of Random Forest (within about 2 points of the best, and statistically equal to deep learning). The built-up problem in small towns is the same one we face on a campus.

**Limitations**
- Not a change-detection study.
- Labels are partly derived from an existing map.
- Random pixel split can make accuracy look better than it is.
- Limited tuning, so the ranking of classifiers is not final.
- One small area and only four scenes.

---

### 2.3 Alonso et al. (2021): Forest land cover mapping at regional scale, multi-temporal Sentinel-2 and RF

**What they did.** Built a 2019 land cover map of Galicia (about 29,500 km²) and tested three design choices.

| Item | Detail |
|---|---|
| Images | Sentinel-2 Level-2A, one image per month (12), up to 50 % cloud allowed, clouds masked with the Level-2A mask |
| Bands | B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 |
| Classes | Eucalyptus, conifers, broadleaves, shrubs, crops and pastures, bare soil, anthropogenic areas, water |
| Training | Polygons from 0.25 m aerial photos, about 243,000 pixels |
| Classifier | Random Forest (500 trees, default settings) on each monthly image, then combined by plurality voting |
| Validation | 1,628 separate photo-interpreted points |

**Design choices tested**

| Question | Finding | Chosen |
|---|---|---|
| How to combine the monthly maps? | Plurality voting and the probability method gave the same accuracy (91.8 vs 92.1 %); the probability method took about 3 times longer | Plurality voting |
| One model per tile or one common model? | Common model 91.55 % vs 89.73 %, and consistent maps where tiles overlap | One common model |
| 10 m or 20 m pixels? | Same overall accuracy (91.6 %). Vegetation slightly better at 20 m; built-up and bare soil better at 10 m | 20 m (forest focus) |

**Result:** overall accuracy 91.6 %, kappa 0.90, no class below F1 0.84. Built-up and bare soil were weakest.

**Relevance to our project:** same bands, Level-2A data and cloud masking; supports Random Forest; shows that a smaller area justifies a stricter cloud limit (they used 50 % for a large cloudy region, another study used 10 % for a small one); and shows 10 m helps built-up areas and roads, which dominate our campus.

**Limitations**
- Single year, no change detection.
- Validation points exist only where photo-interpretation was possible, so accuracy may be biased upward.
- Many bare-soil points were confused with built-up (31 of 189).
- Merged classes (crops, pastures, vineyards) inflate comparison with other studies.
- The 20 m choice suits forests, not a built-up-heavy site.

---

### 2.4 Jagannathan et al. (2025): Multi-year Sentinel-2 land use classification with a deep learning ensemble network

**What they did.** Classified Katpadi (Vellore, Tamil Nadu, around the VIT campus) for every year 2017-2024 with a deep learning model called IRUNet, then described the change between years.

| Item | Detail |
|---|---|
| Data | Sentinel-2A/B 10 m, March-May images, Sen2Cor correction, cut into 256 × 256-pixel patches |
| Labels | Manual annotation in QGIS, checked by field surveys; about 26,000 labelled patches |
| Split | 80 % training, 10 % validation, 10 % testing |
| Model | InceptionResNetV2 (pretrained) feeding a U-Net, plus test-time augmentation (flipped copies averaged) |
| Input | 3-channel images, so red-edge and SWIR bands are not used by the network |
| Classes | 8: urban, vegetation, water body, agriculture, barren, forest, road, others |

**Key results**
- IRUNet + TTA: accuracy 98.21 %, DSC 88.96 %, precision 94.71 %, recall 89.19 %, kappa 0.872.
- Better than U-Net (93.92 %) and ResUNet (94.62 %).
- Urban area expanded between 2019 and 2024 at the expense of agricultural land. Water and vegetation stayed roughly stable.

**Relevance to our project:** similar setting (10 m Sentinel-2, Indian institute campus and surroundings, multi-year urban expansion). Different method: deep learning needs thousands of labelled patches, while we use Random Forest on a small labelled set. One 256 × 256 patch at 10 m is about 6.5 km², larger than our whole campus (469 ha, about 4.7 km²).

**Reliability problems (present the numbers as "as reported")**
- The text and Table 3 give different values for the same metrics (for example DSC 84.60 % vs 88.96 %), and Table 3 lists IoU equal to DSC.
- Training details conflict between the text, Table 2 and Fig. 6 (optimizer, loss and number of epochs).
- The class list in the Methods differs from the categories shown in the results.
- The final layer is described as a single sigmoid output, which suits a two-class mask rather than eight classes.
- Some wording appears carried over from another field (for example "polyp area segmentation").
- No spatial separation between training and test patches is described, so 98 % may be optimistic.
- 98.21 % is pixel accuracy, dominated by large classes. It is not comparable to the overall accuracy of the Random Forest studies.

---

## 3. How our project differs

| Aspect | Reviewed studies | Our project |
|---|---|---|
| Scale | Region, basin, city | Single campus (469.2 ha) |
| Imagery | Landsat or Sentinel-2, 10-30 m | Sentinel-2, 10 m |
| Dates | One date, one year, or several years | Two dates (winter 2019-20 and 2024-25) |
| Change output | Net area per class, or a description | From-to table in hectares |
| Training labels | Hand-drawn polygons or existing maps | Dynamic World labels |
| Validation | Random split or points from the same source | Independent hand-labelled points |

---

## 4. Glossary of keywords

### 4.1 Land cover and data terms

| Term | Meaning |
|---|---|
| Land cover | What physically covers the ground (trees, buildings, water). |
| Land use | What people do with the land (farming, housing, grazing). Cannot be read from the image alone. |
| LULC | Land use and land cover. |
| Multi-temporal | Using several dates of the same area. |
| Mono-temporal | Using a single date. |
| Phenology | The yearly cycle of plants (green-up, peak, dry-down). |
| Tile | A fixed square of Sentinel-2 data (100 km × 100 km). |
| Level-2A / BOA reflectance | Sentinel-2 product already corrected for the atmosphere (surface reflectance). |
| Surface reflectance | How much light the ground itself reflects, after removing atmospheric effects. |
| Atmospheric correction | Removing the effect of air, haze and aerosols so images from different dates can be compared. Sen2Cor is the tool for Sentinel-2. |
| Cloud mask | Marking pixels with cloud or cloud shadow so they are ignored. |
| NoData | Pixels left empty, for example under cloud. |
| Median composite | One image made by taking the median value of each pixel across many images, which removes clouds and noise. |
| Resampling | Changing pixel size, for example 20 m bands to 10 m. Bilinear interpolation averages the nearest pixels; nearest-neighbour copies the closest one. |
| Red edge | The steep rise in leaf reflectance between red and near-infrared, sensitive to chlorophyll. Sentinel-2 has three red-edge bands. |
| SWIR | Short-wave infrared bands, useful for built-up surfaces, bare soil and moisture. |
| Mixed pixel | A pixel that covers more than one class (for example a building next to trees). |
| Patch | A small square cut from a large image so a neural network can process it. |
| Photo-interpretation | Labelling points or polygons by looking at a high-resolution image. |

### 4.2 Spectral indices

| Term | Formula | Highlights |
|---|---|---|
| NDVI | (NIR - Red) / (NIR + Red) | Vegetation (healthy leaves reflect NIR and absorb red) |
| NDWI | (Green - NIR) / (Green + NIR) | Open water (water reflects green, absorbs NIR) |
| MNDWI | (Green - SWIR) / (Green + SWIR) | Water, with less confusion from built-up surfaces |
| NDBI | (SWIR1 - NIR) / (SWIR1 + NIR) | Built-up surfaces (concrete and asphalt reflect SWIR strongly) |

All indices range from -1 to +1.

### 4.3 Classifiers and machine learning

| Term | Meaning |
|---|---|
| Supervised classification | The classifier learns from labelled examples and then labels all other pixels. |
| Random Forest (RF) | Many decision trees, each trained on a random subset of samples and bands. Each tree votes and the majority class wins. |
| Non-parametric | Makes no assumption about the shape (for example normal distribution) of the data. |
| Variable importance | A ranking of which bands or features helped the classifier most. |
| Black box | A model whose reason for a given decision is hard to explain. |
| SVM (support vector machine) | Separates classes with the widest possible boundary; a kernel (for example RBF) lets the boundary be curved. |
| XGBoost | Builds many small trees one after another, each correcting the errors of the previous ones. |
| Deep learning / CNN | Neural networks with many layers. A convolutional neural network (CNN) learns visual patterns such as edges and textures from images. |
| U-Net | A CNN with an encoder (shrinks the image to learn features) and a decoder (expands back to a pixel map), joined by skip connections. |
| Semantic segmentation | Labelling every pixel of an image. |
| Pretrained / transfer learning | Starting from a model already trained on a large general image set, then adjusting it. |
| Test-time augmentation (TTA) | Classifying flipped or rotated copies of an image at prediction time and averaging the results. |
| Ablation study | Removing or adding one component at a time to see what it contributes. |
| Epoch / batch | One full pass over the training data / the number of samples processed at once. |
| Hyperparameter tuning | Trying different model settings and scoring each one. |
| Cross-validation | Repeatedly splitting the training data, training on part and testing on the rest. |
| Plurality voting | Each pixel takes the class it was given most often across all dates. |

### 4.4 Sampling and validation

| Term | Meaning |
|---|---|
| Training samples | Labelled points or polygons used to teach the classifier. |
| Validation (reference) points | Labelled points kept aside and used only to test the map. Also called ground truth. |
| Stratified random sampling | Random sampling with a fair share for every class. |
| Class imbalance | Some classes have far more samples than others, so the classifier favours the large ones. |
| Spatial autocorrelation | Nearby points look alike, so a random split can give test points that are almost duplicates of training points and inflate accuracy. |

### 4.5 Accuracy measures

| Term | Meaning |
|---|---|
| Confusion (error) matrix | Table comparing the map class with the true class at each reference point. The diagonal counts correct points. |
| Overall accuracy (OA) | Correct points divided by all points. |
| User's accuracy | Of the points the map labels as a class, the share that really are that class (can I trust the label). |
| Producer's accuracy | Of the true points of a class, the share the map found (did the map catch everything). |
| Kappa | Agreement beyond what chance would give: (observed - chance) / (1 - chance). Lower than OA when classes are unbalanced. |
| Precision / recall | Precision = TP / (TP + FP) (like user's accuracy); recall = TP / (TP + FN) (like producer's accuracy). |
| F1 score | Combines precision and recall into one number per class. 1.0 is perfect. |
| Dice (DSC) and IoU | Overlap scores between predicted and true areas. For segmentation, Dice and F1 are the same measure. |
| Pixel accuracy | Share of all pixels correctly labelled. Dominated by large classes. |
| McNemar's test / Z-test | Statistical tests of whether two classifiers differ more than chance would explain. |
| Area-adjusted (unbiased) estimate | Class areas corrected using the error matrix, with confidence intervals. Counting mapped pixels alone gives biased areas. |

### 4.6 Change detection

| Term | Meaning |
|---|---|
| Change detection | Comparing two or more dates to find what changed and by how much. |
| Post-classification comparison | Classify each date separately, then compare the maps. |
| Net change | Increase or decrease of each class's total area. Does not show where the change came from. |
| From-to matrix | Table of how much area moved from each class to each other class (for example vegetation to built-up, in hectares). It answers "from what to what". |
| Index differencing | Subtracting an index such as NDVI between dates to find change. |
| Time-series analysis | Tracking trends over many dates. |

