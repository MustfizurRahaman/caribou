"""Nipigon 2020: how far is the v4 figure (study area) from the published 74.4%, and what could close it?

Tests, each added on top of the v4 2020 disturbance raster:
  a. ARI harvest of any year (not only 1976+), buffered 500 m
  b. ARI fire of any year (not only the 40-year window)
  c. both
Also reports the same for Sydney, where v4 is above the paper, as a consistency check.
"""
from pathlib import Path

import cv2
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize

ROOT = next(c for c in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
            if (c / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').exists())
V4 = ROOT / 'outputs_v4'
ARI_GDB = ROOT / 'data' / 'ARI_AnalysisReadyInventory2025' / 'ARI_AnalysisReadyInventory2025' / 'ARI_wFU.gdb'
PAPER = {'Nipigon': 74.4, 'Sydney': 50.0}

ranges = gpd.read_file(ROOT / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').to_crs(3978).set_index('RANGE_NAME')
bnd = gpd.read_file(ARI_GDB, layer='_FMU_FN_PARK_Boundary_simp2m').to_crs(3978)
study_all = bnd.loc[bnd.TYPE == 'MU'].geometry.make_valid().union_all()

rows = []
for name, paper in PAPER.items():
    key = name.lower()
    with rasterio.open(V4 / '02_disturbance' / f'{key}_total_disturbance_2020.tif') as s:
        dist, prof = s.read(1), s.profile
    valid = dist != 255
    dist = dist == 1
    shape, tr = dist.shape, prof['transform']
    study = rasterize([(study_all.intersection(ranges.loc[name].geometry), 1)], out_shape=shape, transform=tr,
                      fill=0, dtype='uint8').astype(bool) & valid
    ev = pyogrio.read_dataframe(ROOT / 'data' / 'interim' / 'ari_events_gdb' / f'{key}_ari_events.gpkg', columns=['YRDEP', 'DEPTYPE'])
    ev['YRDEP'] = pd.to_numeric(ev.YRDEP, errors='coerce')

    def burn(df):
        g = [(x, 1) for x in df.geometry if x is not None and not x.is_empty]
        return rasterize(g, out_shape=shape, transform=tr, fill=0, dtype='uint8').astype(bool) if g else np.zeros(shape, bool)

    harvest_all = burn(ev[(ev.DEPTYPE == 'HARVEST') & (ev.YRDEP <= 2020)])
    harvest_buf = cv2.distanceTransform((~harvest_all).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE) * 30 <= 500
    fire_all = burn(ev[(ev.DEPTYPE == 'FIRE') & (ev.YRDEP <= 2020)])
    pct = lambda m: round(100 * float((m & study).sum()) / study.sum(), 1)
    rows.append(dict(range=name, paper=paper, v4=pct(dist),
                     all_years_harvest=pct(dist | harvest_buf), all_years_fire=pct(dist | fire_all),
                     both=pct(dist | harvest_buf | fire_all),
                     pre1976_harvest_zone_only=pct(harvest_buf & ~dist)))
    print(rows[-1], flush=True)

df = pd.DataFrame(rows).set_index('range')
df.to_csv(ROOT / 'outputs_mackey_rebuild' / 'stats' / 'nipigon_sydney_gap_tests_2020.csv')
print(df)
