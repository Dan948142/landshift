# Literature

Papers reviewed for the LULC mapping and change detection of the IIT Kharagpur campus (Group 8).
This is the same table as slide 4 of the mid-semester deck.

| Paper | Data | Classes | Method | Accuracy |
| ----- | ---- | ------- | ------ | -------- |
| Tikuye et al. (2023) | Landsat, 1983, 2003, 2022; Upper Blue Nile Basin | 7 | Random Forest, change detection | Kappa 83 / 85 / 91 % |
| Abdi (2020) | Sentinel-2, multi-temporal; south-central Sweden | 8 | SVM, RF, XGBoost, deep learning compared | OA: SVM 75.8, XGBoost 75.1, RF 73.9, DL 73.3 % |
| Alonso et al. (2021) | Sentinel-2, 12 monthly images of 2019; Galicia, Spain | 8 | One common Random Forest, 20 m | OA 91.6 %, kappa 0.90 |
| Rynkiewicz et al. (2023), conference abstract | Sentinel-2 annual data, 2018-2021; Lodz (Poland) and Viken (Norway), on Google Earth Engine | 3 (change classes) | Spectral signatures, then Random Forest | OA >= 0.97, kappa > 0.95 |
| Jagannathan et al. (2025) | Sentinel-2A/B, 2017-2024; Katpadi, Tamil Nadu | 8 | IRUNet deep learning with test-time augmentation | Pixel accuracy 98.21 %, F1 91.85 %, kappa 0.872 |

Reported accuracies are not directly comparable across studies: the class schemes, scales and validation methods differ.

Also read: Zhang et al. (2021), single-date urban land cover classification in Beijing with Random Forest (OA 98.3 %, kappa 0.975).

## References

- Tikuye, B. G., Rusnak, M., Manjunatha, B. R., & Jose, J. (2023). Land Use and Land Cover Change Detection Using the Random Forest Approach: The Case of the Upper Blue Nile River Basin, Ethiopia. *Global Challenges*, 7(10). https://doi.org/10.1002/gch2.202300155
- Abdi, A. M. (2020). Land cover and land use classification performance of machine learning algorithms in a boreal landscape using Sentinel-2 data. *GIScience & Remote Sensing*. https://doi.org/10.1080/15481603.2019.1650447
- Alonso, L., Picos, J., & Armesto, J. (2021). Forest Land Cover Mapping at a Regional Scale Using Multi-Temporal Sentinel-2 Imagery and RF Models. *Remote Sensing*, 13(12), 2237. https://doi.org/10.3390/rs13122237
- Rynkiewicz, A., Hoscilo, A., Chmielewska, M., Lewandowska, A., Aune-Lundberg, L., & Nilsen, A. (2023). Detection of land cover changes based on the Sentinel-2 multitemporal data on the GEE platform. EGU General Assembly 2023, EGU23-17586. https://doi.org/10.5194/egusphere-egu23-17586
- Jagannathan, J., Thanjai Vadivel, M., & Divya, C. (2025). Land use classification using multi-year Sentinel-2 images with deep learning ensemble network. *Scientific Reports*, 15, 29047. https://doi.org/10.1038/s41598-025-12512-7
- Zhang, T., Su, J., Xu, Z., Luo, Y., & Li, J. (2021). Sentinel-2 Satellite Imagery for Urban Land Cover Classification by Optimized Random Forest Classifier. *Applied Sciences*, 11(2), 543. https://doi.org/10.3390/app11020543

## PDFs

PDFs are included only for papers published under an open-access licence that allows redistribution. For all others, use the DOI link above.
