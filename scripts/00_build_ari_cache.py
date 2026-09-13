"""Build the per-range depletion caches the 2015-2025 notebook reads.

ontario_caribou_core_habitat_2015_2025.ipynb loads Ontario inventory depletions from
data/interim/ari_events_gdb/<range>_ari_events.gpkg. Without these files it silently
falls back to ontario_ar_master_dataset_forestonly.shp, which covers only 0.6-50.6% of
the seven ranges and gives much lower disturbance. Run this script first.

ARI_wFU.gdb covers 86-100% of each range through 39 FMU + 8 Far North + 7 Park +
2 Islands layers sharing the POLYTYPE / YRDEP / DEPTYPE schema. Only layers whose
boundary polygon intersects a range are read (INV_NAME maps 1:1 to the layer name).

    python scripts/00_build_ari_cache.py        # ~35 min for all seven ranges
"""
import time
import warnings

import geopandas as gpd
import pandas as pd
import pyogrio

from project_root import find_project_root

warnings.filterwarnings('ignore')

ROOT = find_project_root()
GDB = ROOT / 'data' / 'ARI_AnalysisReadyInventory2025' / 'ARI_AnalysisReadyInventory2025' / 'ARI_wFU.gdb'
OUTDIR = ROOT / 'data' / 'interim' / 'ari_events_gdb'
RANGES = ROOT / 'data' / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp'

KEEP = ['HARVEST', 'FIRE', 'BLOWDOWN', 'DROUGHT', 'UNKNOWN']
COLS = ['ARI_ID', 'POLYTYPE', 'YRDEP', 'DEPTYPE', 'YRORG', 'AGE']
PAPER_RANGES = ['Berens', 'Brightsand', 'Churchill', 'Kesagami', 'Nipigon', 'Pagwachuan', 'Sydney']


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    available = {n for n, _ in pyogrio.list_layers(GDB)}
    bnd = gpd.read_file(GDB, layer='_FMU_FN_PARK_Boundary_simp2m')
    if not bnd.geometry.is_valid.all():
        bnd.geometry = bnd.geometry.make_valid()

    rng = gpd.read_file(RANGES)
    rng = rng[rng.RANGE_NAME.isin(PAPER_RANGES)].to_crs(3161)   # the geodatabase CRS

    summary = []
    t0 = time.time()
    for r in rng.itertuples():
        hits = bnd[bnd.intersects(r.geometry)]
        layers = [n for n in hits.INV_NAME.dropna().unique() if n in available]
        print('[%5.0fs] %s: %d inventory layers' % (time.time() - t0, r.RANGE_NAME, len(layers)), flush=True)

        parts = []
        for lyr in layers:
            try:
                g = pyogrio.read_dataframe(GDB, layer=lyr, columns=COLS, bbox=r.geometry.bounds)
            except Exception as e:
                print('    %-22s READ FAILED %s' % (lyr, e), flush=True)
                continue
            g = g[g.POLYTYPE.eq('FOR') & g.DEPTYPE.isin(KEEP)].copy()
            g['YRDEP'] = pd.to_numeric(g['YRDEP'], errors='coerce')
            g = g[g.YRDEP.between(1900, 2025)]
            if not len(g):
                continue
            # Spatial-index prefilter rather than gpd.clip: cheaper, and whole polygons are
            # kept on purpose, since a cutblock just outside the range still projects its
            # 500 m buffer inward. The notebook masks rasterisation to the range.
            idx = list(g.sindex.query(r.geometry, predicate='intersects'))
            if idx:
                parts.append(g.iloc[idx])
                print('    %-22s %7d depletion polygons' % (lyr, len(idx)), flush=True)

        if not parts:
            print('    nothing found for', r.RANGE_NAME, flush=True)
            continue
        ev = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry='geometry', crs=3161).to_crs(3978)
        ev['ha'] = ev.geometry.area / 1e4
        out = OUTDIR / (r.RANGE_NAME.lower() + '_ari_events.gpkg')
        ev.to_file(out, driver='GPKG')
        window = ev[ev.YRDEP.between(1976, 2025)]
        summary.append(dict(range=r.RANGE_NAME, polygons=len(ev),
                            harvest_ha=round(window[window.DEPTYPE.eq('HARVEST')].ha.sum()),
                            fire_ha=round(window[window.DEPTYPE.eq('FIRE')].ha.sum())))
        print('    -> %s' % out, flush=True)

    print()
    print(pd.DataFrame(summary).to_string(index=False))
    print('\ntotal %.0f s' % (time.time() - t0))


if __name__ == '__main__':
    main()
