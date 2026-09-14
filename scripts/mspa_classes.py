"""Shared definitions for the simplified MSPA core-habitat product.

The 05_mspa rasters carry 19 patch-size classes produced by
core_size_classes() in ontario_caribou_core_habitat_2015_2025.ipynb, which
digitizes patch area against these bin edges (ha):

    0 .25 .5 1 2 3 4 5 10 25 50 100 250 500 1000 10000 50000 250000 500000 inf

so raw class c covers areas [bins[c-1], bins[c]). Classes 1-11 are all under
100 ha; roughly 60,000 of the ~50,000-88,000 patches per range fall in 1-7
(< 5 ha), which is erosion speckle rather than usable caribou habitat.

This module collapses those 19 into 5 ordered classes at caribou
functional-habitat thresholds.
"""
import numpy as np

RES_M = 30
PIXEL_HA = (RES_M * RES_M) / 10_000.0   # 0.09
NODATA = 255

# new class -> (raw classes, lower ha, upper ha, label)
CLASSES = [
    (1, range(1, 12),  0,      100,    'Sub-functional (<100 ha)'),
    (2, range(12, 14), 100,    500,    'Small (100-500 ha)'),
    (3, range(14, 15), 500,    1_000,  'Moderate (500-1,000 ha)'),
    (4, range(15, 16), 1_000,  10_000, 'Large (1,000-10,000 ha)'),
    (5, range(16, 20), 10_000, None,   'Very large / intact (>10,000 ha)'),
]

LABELS = {0: 'Not core', **{c: lab for c, _, _, _, lab in CLASSES}}

# Sequential single-hue green ramp, light -> dark, validated as an ordinal ramp
# against a light basemap surface (#f2f0eb) with the dataviz validator:
# monotone lightness, adjacent dL >= 0.06, light end 2.14:1 (>= 2:1 floor),
# hue spread 4 deg. Optimised for light basemaps (Positron / ESRI Light Gray /
# OSM); the dark steps do not clear 3:1 on a dark basemap.
COLORS = {
    0: ('#9e9e94', 40),    # not core, but inside the analysed range: faint grey
    1: ('#5cb96b', 235),
    2: ('#31a354', 235),
    3: ('#1a7539', 240),
    4: ('#0b5227', 245),
    5: ('#00330f', 250),
}


def build_lut():
    """255-entry uint8 lookup table: raw class -> simplified class."""
    lut = np.zeros(256, dtype='uint8')
    for new, raws, _, _, _ in CLASSES:
        for raw in raws:
            lut[raw] = new
    lut[NODATA] = NODATA
    return lut


def rgba_lut():
    """(256, 4) uint8 RGBA lookup; everything unmapped is fully transparent."""
    lut = np.zeros((256, 4), dtype='uint8')
    for value, (hex_color, alpha) in COLORS.items():
        h = hex_color.lstrip('#')
        lut[value] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)
    return lut
