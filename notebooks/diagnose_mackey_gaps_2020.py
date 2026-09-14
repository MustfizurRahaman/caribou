"""Test two explanations for the remaining gaps against Mackey et al. (2024), 2020, study-area boundary.

1. Water: is the gap explained if water (VLCE2 class 20) counts as disturbed, or is left out of the area total?
2. Fire window: how much does each fire year band contribute, and what if 1980 fires are excluded?

Uses the component flag rasters written by mackey_inputs_disturbance_rebuild_2020.ipynb.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from shapely.geometry import box

ROOT = next(c for c in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
            if (c / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').exists())
RAW, V3, OUT = ROOT / 'data' / 'raw', ROOT / 'outputs_v3', ROOT / 'outputs_mackey_rebuild'
VLCE = '/vsizip/' + (RAW / 'landcover_2019' / 'CA_forest_VLCE2_2019.zip').as_posix() + '/CA_forest_VLCE2_2019.tif'
NFDB = RAW / 'paper_inputs' / 'nfdb_fire' / 'NFDB_poly_1972to2020_20250630.shp'
ARI_GDB = ROOT / 'data' / 'ARI_AnalysisReadyInventory2025' / 'ARI_AnalysisReadyInventory2025' / 'ARI_wFU.gdb'
PAPER = {'Berens': 46.4, 'Brightsand': 65.6, 'Churchill': 49.0, 'Kesagami': 53.5, 'Nipigon': 74.4, 'Pagwachuan': 67.8, 'Sydney': 50.0}

ranges = gpd.read_file(ROOT / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').to_crs(3978).set_index('RANGE_NAME')
bnd = gpd.read_file(ARI_GDB, layer='_FMU_FN_PARK_Boundary_simp2m').to_crs(3978)
study_all = bnd.loc[bnd.TYPE == 'MU'].geometry.make_valid().union_all()

rows = []
for name, paper in PAPER.items():
    key = name.lower()
    with rasterio.open(next((V3 / '01_potential_habitat').glob(key + '_*.tif'))) as s:
        prof, valid = s.profile, s.read(1) != 255
    bounds = rasterio.transform.array_bounds(prof['height'], prof['width'], prof['transform'])
    study = rasterize([(study_all.intersection(ranges.loc[name].geometry), 1)], out_shape=valid.shape,
                      transform=prof['transform'], fill=0, dtype='uint8').astype(bool) & valid
    flags = rasterio.open(OUT / 'rasters' / f'{key}_disturbance_components_2020.tif').read(1)
    non_fire = (flags & 0b011111) > 0                      # harvest, MNRF roads, NRN roads, OLCC, FRI unclassified
    rebuild = (flags & 0b111111) > 0
    with rasterio.open(VLCE) as s:
        lc = s.read(1, window=from_bounds(*bounds, transform=s.transform).round_offsets().round_lengths())
    water = (lc == 20) & study

    fire = pyogrio.read_dataframe(NFDB, columns=['YEAR'],
                                  bbox=tuple(gpd.GeoSeries([box(*bounds)], crs=3978).to_crs(pyogrio.read_info(NFDB)['crs']).total_bounds))
    fire = fire.to_crs(3978)
    fire['YEAR'] = pd.to_numeric(fire.YEAR, errors='coerce')

    def burn(df):
        g = [(x.buffer(0), 1) for x in df.geometry if x is not None and not x.is_empty]
        return (rasterize(g, out_shape=valid.shape, transform=prof['transform'], fill=0, dtype='uint8').astype(bool)
                if g else np.zeros(valid.shape, bool))

    f1980 = burn(fire[fire.YEAR == 1980])
    f81_20 = burn(fire[fire.YEAR.between(1981, 2020)])
    n = study.sum()
    pct = lambda m: 100 * (m & study).sum() / n
    rows.append(dict(
        range=name, paper=paper, rebuild=pct(rebuild), water_share=pct(water),
        water_counted_disturbed=pct(rebuild | water),
        water_excluded_from_area=100 * (rebuild & study & ~water).sum() / max(1, (study & ~water).sum()),
        fire_1980_only_share=pct(f1980 & ~non_fire & ~f81_20),
        rebuild_fire_1981_2020=pct(non_fire | f81_20),
        rebuild_no_fire=pct(non_fire)))
    print(rows[-1], flush=True)

df = pd.DataFrame(rows).set_index('range').round(1)
df.to_csv(OUT / 'stats' / 'gap_diagnostics_2020.csv')
pd.set_option('display.width', 220)
print(df)
