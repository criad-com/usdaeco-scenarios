#!/usr/bin/env python3
"""Evaluate a sync session with the family roundtrip severity profile."""
import argparse
import json
from pathlib import Path
from family import ROOT, activate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("--pluginset", type=Path, default=ROOT / ".work/pluginset")
    parser.add_argument("--profile", type=Path, default=ROOT / "profiles/roundtrip.json")
    args = parser.parse_args()
    activate(args.pluginset)
    from pxr import Usd
    from roundtrip_validators import evaluate
    report = evaluate(Usd.Stage.Open(str(args.stage.resolve())), args.profile)
    print(json.dumps(report, indent=2))
    return int(report["errors"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
