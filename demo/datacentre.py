#!/usr/bin/env python3
"""Run the CCTV-owned example on the published base stage."""
import argparse
import importlib.util
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from family import ROOT


def scenario_module():
    spec = importlib.util.spec_from_file_location('aeco_facility_checks', ROOT / 'scenarios/datacentre.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pluginset', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('aeco_published_scenario', ROOT / 'scenarios/published.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    raise SystemExit(module.run_scenario(args.output, args.pluginset))
