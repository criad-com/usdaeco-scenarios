#!/usr/bin/env python3
"""Run scenarios commands directly from this checkout."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools'))
from usdaeco_scenarios.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
