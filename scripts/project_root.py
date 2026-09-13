"""Locate the project root without hard-coding a drive letter.

The notebooks already find the root by walking up from the working directory
looking for a marker file; this mirrors that for the scripts, so the same
checkout runs unchanged on Windows, macOS and Linux.

Resolution order:
  1. $CARIBOU_PROJECT_ROOT, if set
  2. the nearest ancestor of this file containing data/Caribou_range_boundary/
  3. the nearest such ancestor of the current working directory
"""
import os
from pathlib import Path

MARKER = Path('data') / 'Caribou_range_boundary' / 'Caribou_range_boundary.shp'


def find_project_root(start=None):
    env = os.environ.get('CARIBOU_PROJECT_ROOT')
    if env:
        root = Path(env).expanduser().resolve()
        if not (root / MARKER).exists():
            raise SystemExit(
                'CARIBOU_PROJECT_ROOT=%s does not contain %s' % (root, MARKER))
        return root

    for base in [Path(start or __file__).resolve().parent, Path.cwd().resolve()]:
        for candidate in [base] + list(base.parents):
            if (candidate / MARKER).exists():
                return candidate

    raise SystemExit(
        'Could not locate the project root.\n'
        'Expected an ancestor directory containing %s.\n'
        'Set CARIBOU_PROJECT_ROOT to the checkout, e.g.\n'
        '  export CARIBOU_PROJECT_ROOT=~/forest_data_curation/caribou_habitat/Reproduce_brenden'
        % MARKER)


def outputs_dir(version='outputs_v3'):
    """Output tree; override with $CARIBOU_OUTPUTS for a scratch location."""
    env = os.environ.get('CARIBOU_OUTPUTS')
    return Path(env).expanduser().resolve() if env else find_project_root() / version
