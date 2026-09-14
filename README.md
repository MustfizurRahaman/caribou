# Caribou core habitat, Ontario 2015–2025

Annual 30 m core-habitat maps for seven Ontario woodland caribou ranges (Berens, Brightsand, Churchill, Kesagami, Nipigon, Pagwachuan, Sydney), following Mackey et al. (2024), *Land* 13, 6.

- **Story page:** https://mustfizurrahaman.github.io/caribou/
- **Notebook (current, v4):** [`notebooks/ontario_caribou_core_habitat_2015_2025_v4.ipynb`](notebooks/ontario_caribou_core_habitat_2015_2025_v4.ipynb)
- **ForestTRACE web map:** https://foresttrace.vercel.app

## Versions

| Notebook | Disturbance inputs |
|---|---|
| `ontario_caribou_core_habitat_2015_2025.ipynb` (v3) | ARI harvest, fire and other depletions; national harvest 1985–2022; ECCC 2020 footprint (roads and infrastructure from ECCC only). Also builds potential habitat, which v4 reuses. |
| `ontario_caribou_core_habitat_2015_2025_v4.ipynb` (v4) | v3 plus MNRF Road Segments by construction year, National Road Network, Ontario Land Cover Compilation v2 (classes 25, 27, 28), FRI unclassified polygons and the National Fire Database. Reports disturbance by type and the comparison with Mackey et al. (2024). |
| `mackey_inputs_disturbance_rebuild_2020.ipynb` | One-date (2020) rebuild with every road, used to test the gaps against the published figures. |

Diagnostics: `notebooks/diagnose_mackey_gaps_2020.py` (water and fire-window tests), `notebooks/check_roads_effect_on_core_2020.py`, `notebooks/check_road_year_sources.py`.

## Data

Not included. Download each dataset and place it under `data/`:

| Dataset | Source | Place at |
|---|---|---|
| Caribou range boundaries | [Ontario GeoHub](https://geohub.lio.gov.on.ca/datasets/lio::caribou-range-boundary/about) | `data/Caribou_range_boundary/Caribou_range_boundary.shp` |
| Forest land cover 2019 (VLCE2) | [NFIS](https://opendata.nfis.org/downloads/forest_change/CA_forest_VLCE2_2019.zip) | `data/raw/landcover_2019/CA_forest_VLCE2_2019.zip` |
| Forest harvest 1985–2022 | [NFIS](https://opendata.nfis.org/downloads/forest_change/CA_Forest_Harvest_1985-2022.zip) | `data/raw/national_harvest/CA_Forest_Harvest_1985-2022.zip` |
| ECCC 2020 disturbance footprint | [Open Government](https://open.canada.ca/data/en/dataset/63e1cda6-debe-4b9b-b075-3666443e30b4) | `data/raw/disturbance_2020/eccc_2020_total_disturbance_<NN>_<Range>.geojson` |
| ECCC 2020 anthropogenic 500 m footprint, per range (v4) | ECCC `DisturbanceFootprintUpdatedFor2020` MapServer, layer 2, filtered by `HERD` | `data/raw/disturbance_2020/eccc_2020_anthro500m_<Range>.geojson` |
| Analysis Ready Inventory 2025 | Ontario | `data/ARI_AnalysisReadyInventory2025/ARI_AnalysisReadyInventory2025/ARI_wFU.gdb` |
| Forest-only annual report master | Ontario | `data/ontario_ar_forest_only/ontario_ar_master_dataset_forestonly.shp` |
| MNRF Road Segments (v4) | [Land Information Ontario](https://geohub.lio.gov.on.ca/) (`MNRRDSEG.zip`) | `data/raw/paper_inputs/mnrf_roads/Non_Sensitive.gdb` |
| National Road Network, Ontario (v4) | [Statistics Canada](https://geo.statcan.gc.ca/nrn_rrn/on/nrn_rrn_on_GPKG.zip) | `data/raw/paper_inputs/nrn_ontario/NRN_RRN_ON_GPKG/NRN_ON_*_GPKG_en.gpkg` |
| Ontario Land Cover Compilation v2 (v4) | Land Information Ontario (`OntarioLandCoverComp-v2.zip`) | `data/raw/paper_inputs/olcc_v2/OntarioLandCoverComp-v2/OLCC_V2_TIFF/OLCC_V2_TIFF.tif` |
| National Fire Database polygons (v4) | [CWFIS](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly.zip) | `data/raw/paper_inputs/nfdb_fire/NFDB_poly_*.shp` |

## Run

```bash
python scripts/00_build_ari_cache.py   # per-range inventory depletions, ~35 min
jupyter lab notebooks/ontario_caribou_core_habitat_2015_2025.ipynb       # v3: potential habitat + v3 series
jupyter lab notebooks/ontario_caribou_core_habitat_2015_2025_v4.ipynb    # v4: ~25 min for all seven ranges
```

Set `CARIBOU_RANGES=Sydney` to run v4 on one range.

Requires geopandas, pyogrio, rasterio, scipy, opencv-python, numpy, pandas, matplotlib.

Collapse the 19 MSPA size bins to the 5 classes used on the story page and in the app: `CARIBOU_OUTPUTS=<project>/outputs_v4 python scripts/01_simplify_mspa.py`.
