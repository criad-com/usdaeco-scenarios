#!/usr/bin/env python3
"""Family entry point using Report and check_structure: N checks, M failed."""
import os
from pathlib import Path
import sys


def structure():
    root = Path(__file__).resolve().parent
    kit = Path(os.environ.get('TOOLCHAIN_DIR', root.parent / 'usdaeco-toolchain'))
    sys.path.insert(0, str(kit / 'tools'))
    from usdaeco_check import Report
    from usdaeco_check.structure import check_structure
    report = Report()
    for result in check_structure(root):
        report.add(result)
    return report.finish()


if __name__ == '__main__':
    if '--structure-only' in sys.argv:
        raise SystemExit(structure())
    from check_all import main
    raise SystemExit(main())
