"""Nipigon 2020: would counting large regulated lakes as "reservoirs" (buffered 500 m) close the gap to 74.4%?

Mackey et al. (2024) list reservoirs and dams in their provincial disturbance layer, buffered 500 m.
Lake Nipigon and the Ogoki Reservoir are regulated. This finds the largest water bodies
(VLCE2 class 20, 8-connected) in the Nipigon study area and adds them, with a 500 m buffer,
to the v4 2020 disturbance one at a time, largest first.
"""
from pathlib import Path

import cv2
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import array_bounds, xy
from rasterio.windows import from_bounds
from scipy import ndimage

ROOT = next(c for c in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
            if (c / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').exists())
RAW, V4 = ROOT / 'data' / 'raw', ROOT / 'outputs_v4'
VLCE = '/vsizip/' + (RAW / 'landcover_2019' / 'CA_forest_VLCE2_2019.zip').as_posix() + '/CA_forest_VLCE2_2019.tif'
ARI_GDB = ROOT / 'data' / 'ARI_AnalysisReadyInventory2025' / 'ARI_AnalysisReadyInventory2025' / 'ARI_wFU.gdb'

ranges = gpd.read_file(ROOT / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').to_crs(3978).set_index('RANGE_NAME')
bnd = gpd.read_file(ARI_GDB, layer='_FMU_FN_PARK_Boundary_simp2m').to_crs(3978)
study_all = bnd.loc[bnd.TYPE == 'MU'].geometry.make_valid().union_all()

with rasterio.open(V4 / '02_disturbance' / 'nipigon_total_disturbance_2020.tif') as s:
    dist, tr = s.read(1), s.transform
valid = dist != 255
dist = dist == 1
study = rasterize([(study_all.intersection(ranges.loc['Nipigon'].geometry), 1)], out_shape=dist.shape, transform=tr,
                  fill=0, dtype='uint8').astype(bool) & valid
with rasterio.open(VLCE) as s:
    lc = s.read(1, window=from_bounds(*array_bounds(*dist.shape, tr), transform=s.transform).round_offsets().round_lengths())
water = (lc == 20) & valid
labels, n = ndimage.label(water, structure=np.ones((3, 3), bool))
sizes = np.bincount(labels.ravel())
sizes[0] = 0
order = np.argsort(sizes)[::-1][:6]
to_lonlat = gpd.GeoSeries

n_study = study.sum()
pct = lambda m: 100 * float((m & study).sum()) / n_study
print(f'v4 2020, study area: {pct(dist):.1f}%  (paper 74.4%)')
acc = dist.copy()
for rank, lab in enumerate(order, 1):
    lake = labels == lab
    rows, cols = np.nonzero(lake)
    cx, cy = xy(tr, int(rows.mean()), int(cols.mean()))
    lon, lat = gpd.GeoSeries(gpd.points_from_xy([cx], [cy]), crs=3978).to_crs(4326).iloc[0].coords[0]
    zone = cv2.distanceTransform((~lake).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE) * 30 <= 500
    acc |= zone
    print(f'{rank}. water body {sizes[lab] * 0.09:>9,.0f} ha near {lat:.2f}N {abs(lon):.2f}W, in study area '
          f'{float((lake & study).sum()) * 0.09:>9,.0f} ha -> cumulative disturbance {pct(acc):.1f}%', flush=True)
