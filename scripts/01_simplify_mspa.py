"""Collapse the 19-class MSPA rasters to the 5 ecological classes.

Reads  outputs_v3/05_mspa/{range}_core_patch_size_class_{year}.tif
Writes outputs_v3/05_mspa_simplified/{range}_core_class5_{year}.tif
       outputs_v3/05_mspa_simplified/class_areas_2015_2025.csv

Grid, CRS and NoData are preserved exactly; only the pixel values change.
Output carries internal tiling and an overview pyramid so it draws fast.
"""
import csv
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

sys.path.insert(0, str(Path(__file__).parent))
from mspa_classes import CLASSES, NODATA, PIXEL_HA, build_lut

from project_root import outputs_dir  # noqa: E402

OUT_ROOT = outputs_dir('outputs_v3')
SRC = OUT_ROOT / '05_mspa'
DST = OUT_ROOT / '05_mspa_simplified'
RANGES = ['berens', 'brightsand', 'churchill', 'kesagami', 'nipigon', 'pagwachuan', 'sydney']
YEARS = range(2015, 2026)

DST.mkdir(parents=True, exist_ok=True)
lut = build_lut()
rows = []
t0 = time.time()

for name in RANGES:
    for year in YEARS:
        src_path = SRC / f'{name}_core_patch_size_class_{year}.tif'
        dst_path = DST / f'{name}_core_class5_{year}.tif'
        with rasterio.open(src_path) as ds:
            raw = ds.read(1)
            profile = ds.profile.copy()

        simplified = lut[raw]

        profile.update(compress='LZW', predictor=2, tiled=True,
                       blockxsize=512, blockysize=512, nodata=NODATA)
        with rasterio.open(dst_path, 'w', **profile) as dst:
            dst.write(simplified, 1)
            dst.build_overviews([2, 4, 8, 16, 32, 64], Resampling.mode)
            dst.update_tags(ns='rio_overview', resampling='mode')

        counts = np.bincount(simplified.ravel(), minlength=256)
        row = {'RANGE_NAME': name, 'YEAR': year,
               'core_total_ha': round(float(counts[1:6].sum()) * PIXEL_HA, 2)}
        for new, _, lo, hi, label in CLASSES:
            row[f'class{new}_ha'] = round(float(counts[new]) * PIXEL_HA, 2)
        rows.append(row)
        by_class = '  '.join(format(row['class%d_ha' % c], '>10,.0f') for c, *_ in CLASSES)
        print(f'{name:11} {year}  core={row["core_total_ha"]:12,.0f} ha  [{by_class}]', flush=True)

csv_path = DST / 'class_areas_2015_2025.csv'
with open(csv_path, 'w', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f'\n{len(rows)} rasters -> {DST}')
print(f'areas -> {csv_path}')
print(f'elapsed {time.time() - t0:.0f}s')
