"""How much would adding MNRF + NRN roads (500 m buffer) change 2020 core habitat?

Control: core habitat recomputed from the v3 2020 disturbance must match
outputs_v3/04_statistics (core_habitat_ha). Test: v3 disturbance plus buffered roads.
Core extraction is the same as the 2015-2025 notebook: 3x3 erosion, 8-connected
patches, 19 area bins, collapsed to the 5 classes used by the app.
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

ROOT = next(c for c in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
            if (c / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp').exists())
V3, OUT = ROOT / 'outputs_v3', ROOT / 'outputs_mackey_rebuild'
RANGES = ['Berens', 'Brightsand', 'Churchill', 'Kesagami', 'Nipigon', 'Pagwachuan', 'Sydney']
PIXEL_HA = 0.09
BINS = np.array([0, .25, .5, 1, 2, 3, 4, 5, 10, 25, 50, 100, 250, 500, 1000, 10000, 50000, 250000, 500000, np.inf])
# raw class (1-19) -> app class: 1 <100 ha, 2 100-500, 3 500-1,000, 4 1,000-10,000, 5 >10,000
TO5 = np.zeros(20, np.uint8)
TO5[1:12], TO5[12:14], TO5[14], TO5[15], TO5[16:20] = 1, 2, 3, 4, 5
BIT_ROADS = (1 << 1) | (1 << 2)      # roads_mnrf, roads_nrn
BIT_V3 = 1 << 7


def core_stats(undisturbed):
    core = ndimage.binary_erosion(undisturbed, structure=np.ones((3, 3), bool), border_value=0)
    labels, count = ndimage.label(core, structure=np.ones((3, 3), bool))
    px = np.bincount(labels.ravel())
    px[0] = 0
    cls5 = TO5[np.digitize(px * PIXEL_HA, BINS, right=False)]
    by_class = {c: float(px[cls5 == c].sum()) * PIXEL_HA for c in range(1, 6)}
    return dict(core_ha=float(px.sum()) * PIXEL_HA, patches=int(count), **{f'c{c}_ha': v for c, v in by_class.items()})


stats = pd.read_csv(V3 / '04_statistics' / 'annual_caribou_habitat_statistics_2015_2025.csv')
rows = []
t0 = time.time()
for name in RANGES:
    key = name.lower()
    with rasterio.open(next((V3 / '01_potential_habitat').glob(key + '_*.tif'))) as s:
        pot = s.read(1)
    valid = pot != 255
    habitat = (pot == 1) & valid
    flags = rasterio.open(OUT / 'rasters' / f'{key}_disturbance_components_2020.tif').read(1)
    v3_dist = (flags & BIT_V3) > 0
    roads = (flags & BIT_ROADS) > 0

    base = core_stats(habitat & ~v3_dist)
    test = core_stats(habitat & ~(v3_dist | roads))
    published = float(stats[(stats.RANGE_NAME == name) & (stats.YEAR == 2020)].core_habitat_ha.iloc[0])
    row = dict(range=name, published_core_ha=published, control_core_ha=base['core_ha'],
               control_matches=abs(base['core_ha'] - published) < 1,
               roads_core_ha=test['core_ha'],
               core_change_pct=100 * (test['core_ha'] / base['core_ha'] - 1),
               functional_ge100_change_pct=100 * ((test['core_ha'] - test['c1_ha']) / (base['core_ha'] - base['c1_ha']) - 1),
               large_ge1000_control_ha=base['c4_ha'] + base['c5_ha'], large_ge1000_roads_ha=test['c4_ha'] + test['c5_ha'],
               large_ge1000_change_pct=100 * ((test['c4_ha'] + test['c5_ha']) / max(1, base['c4_ha'] + base['c5_ha']) - 1),
               very_large_gt10000_change_pct=100 * (test['c5_ha'] / max(1, base['c5_ha']) - 1) if base['c5_ha'] else float('nan'),
               patches_control=base['patches'], patches_roads=test['patches'],
               extra_disturbed_pct_of_range=100 * (roads & ~v3_dist & valid).sum() / valid.sum())
    rows.append(row)
    print(f"[{time.time() - t0:5.0f}s] {name}: core {base['core_ha']:,.0f} -> {test['core_ha']:,.0f} ha ({row['core_change_pct']:+.1f}%), "
          f">=1,000 ha {row['large_ge1000_change_pct']:+.1f}%, control matches app stats: {row['control_matches']}", flush=True)
    del pot, flags, v3_dist, roads, valid, habitat

df = pd.DataFrame(rows).set_index('range')
df.to_csv(OUT / 'stats' / 'roads_effect_on_core_2020.csv')
pd.set_option('display.width', 250)
print(df.round(1))
tot_b, tot_t = df.control_core_ha.sum(), df.roads_core_ha.sum()
print('all ranges: core %.0f -> %.0f ha (%+.1f%%)' % (tot_b, tot_t, 100 * (tot_t / tot_b - 1)))
