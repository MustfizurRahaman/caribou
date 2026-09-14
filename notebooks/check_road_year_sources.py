"""Which road sources carry a usable year? (MNRF construction year, ECCC Year_added, NRN dates, annual report roads)"""
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
PI = RAW / 'paper_inputs'
ranges = gpd.read_file(ROOT / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp')
seven = ranges[ranges.RANGE_NAME.isin(['Berens', 'Brightsand', 'Churchill', 'Kesagami', 'Nipigon', 'Pagwachuan', 'Sydney'])]

# 1. MNRF road segments inside the seven ranges
mnrf = pyogrio.read_dataframe(PI / 'mnrf_roads' / 'Non_Sensitive.gdb', layer='MNRF_ROAD_SEGMENT',
                              columns=['YEAR_CONSTRUCTED', 'YEAR_CONSTRUCTED_MODIFIER', 'ROAD_CLOSED_YEAR', 'YEAR_DECOMMISSIONED'],
                              bbox=tuple(seven.to_crs(4269).total_bounds))
mnrf = mnrf.to_crs(3978)
outline = seven.to_crs(3978).geometry.simplify(1000).union_all()      # fast selection; segments are not cut
mnrf = mnrf[mnrf.intersects(outline)].copy()
mnrf['km'] = mnrf.geometry.length / 1000
yc = pd.to_numeric(mnrf.YEAR_CONSTRUCTED, errors='coerce')
valid = yc.between(1900, 2026)
print(f'MNRF segments in the 7 ranges: {len(mnrf):,} ({mnrf.km.sum():,.0f} km)')
print(f'  with a real construction year (1900-2026): {valid.mean() * 100:.1f}% of segments, {mnrf.km[valid].sum() / mnrf.km.sum() * 100:.1f}% of length')
print('  placeholder / other values:', yc[~valid].value_counts(dropna=False).head(6).to_dict())
print('  modifier values:', mnrf.YEAR_CONSTRUCTED_MODIFIER.value_counts(dropna=False).head(6).to_dict())
dec = pd.cut(yc[valid], [1899, 1969, 1979, 1989, 1999, 2009, 2014, 2019, 2026])
print('  km by construction period:', mnrf.km[valid].groupby(dec).sum().round(0).to_dict())

# 2. ECCC linear features carry Year_added (2010 / 2015 / 2020 imagery)
parts = []
for f in (RAW / 'disturbance_2020').glob('eccc_2020_lines_*.geojson'):
    g = gpd.read_file(f).set_crs(3978, allow_override=True)
    g['km'] = g.geometry.length / 1000
    parts.append(g[g.Class == 'Road'])
ec = pd.concat(parts)
print('\nECCC roads, km by Year_added:', ec.groupby('Year_added').km.sum().round(0).to_dict())

# 3. NRN date fields
info = pyogrio.read_info(next((PI / 'nrn_ontario').rglob('NRN_ON_*_GPKG_en.gpkg')), layer='NRN_ON_18_0_ROADSEG')
print('\nNRN ROADSEG date-like fields:', [c for c in info['fields'] if 'DATE' in c.upper() or 'YEAR' in c.upper()])

# 4. Ontario annual report package downloaded on 2026-08-26
ar = RAW / 'harvest' / 'AnalysisReadyAR_202605.zip'
if ar.exists():
    names = zipfile.ZipFile(ar).namelist()
    print(f'\nAnnual report zip: {len(names)} members; road-like entries:')
    print([n for n in names if any(k in n.upper() for k in ('ROAD', 'RDS', 'RDC', 'ROD'))][:30])
    print('top-level:', sorted({n.split('/')[0] for n in names})[:20])
