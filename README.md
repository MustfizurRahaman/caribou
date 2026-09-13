# Caribou core habitat, Ontario 2015–2025

Annual 30 m core-habitat maps for seven Ontario woodland caribou ranges (Berens, Brightsand, Churchill, Kesagami, Nipigon, Pagwachuan, Sydney), following Mackey et al. (2024), *Land* 13, 6.

- **Story page:** https://mustfizurrahaman.github.io/caribou/
- **Notebook:** [`notebooks/ontario_caribou_core_habitat_2015_2025.ipynb`](notebooks/ontario_caribou_core_habitat_2015_2025.ipynb)
- **ForestTRACE web map:** https://foresttrace.vercel.app

## Data

Not included. Download each dataset and place it under `data/`:

| Dataset | Source | Place at |
|---|---|---|
| Caribou range boundaries | [Ontario GeoHub](https://geohub.lio.gov.on.ca/datasets/lio::caribou-range-boundary/about) | `data/Caribou_range_boundary/Caribou_range_boundary.shp` |
| Forest land cover 2019 (VLCE2) | [NFIS](https://opendata.nfis.org/downloads/forest_change/CA_forest_VLCE2_2019.zip) | `data/raw/landcover_2019/CA_forest_VLCE2_2019.zip` |
| Forest harvest 1985–2022 | [NFIS](https://opendata.nfis.org/downloads/forest_change/CA_Forest_Harvest_1985-2022.zip) | `data/raw/national_harvest/CA_Forest_Harvest_1985-2022.zip` |
| ECCC 2020 disturbance footprint | [Open Government](https://open.canada.ca/data/en/dataset/63e1cda6-debe-4b9b-b075-3666443e30b4) | `data/raw/disturbance_2020/eccc_2020_total_disturbance_<NN>_<Range>.geojson` |
| Analysis Ready Inventory 2025 | Ontario | `data/ARI_AnalysisReadyInventory2025/ARI_AnalysisReadyInventory2025/ARI_wFU.gdb` |
| Forest-only annual report master | Ontario | `data/ontario_ar_forest_only/ontario_ar_master_dataset_forestonly.shp` |

## Run

```bash
python scripts/00_build_ari_cache.py   # per-range inventory depletions, ~35 min
jupyter lab notebooks/ontario_caribou_core_habitat_2015_2025.ipynb
```

Requires geopandas, pyogrio, rasterio, scipy, opencv-python, numpy, pandas, matplotlib.
