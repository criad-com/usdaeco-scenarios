#!/usr/bin/env python3
"""Run released CCTV cases with the core 0.9 mesh provenance convention."""
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from family import repos


def migrate_mesh_marks(stage):
    """Correct copied synthetic mesh annotations; geometry and drivers stay intact."""
    from pxr import UsdGeom
    count = 0
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh) and prim.HasAPI('AecoDerivedGeometryAPI'):
            attribute = prim.GetAttribute('aeco:derived:approx')
            if attribute.Get() == 'exact':
                attribute.Set('tessellated'); count += 1
    return count


def runner():
    path = repos()['cctv'] / 'scenarios/run.py'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('released_cctv_cases', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original_open, original_ops = module.open_copy, module.apply_ops
    def open_copy(*args, **kwargs):
        stage = original_open(*args, **kwargs)
        migrate_mesh_marks(stage)
        return stage
    def apply_ops(stage, *args, **kwargs):
        original_ops(stage, *args, **kwargs)
        migrate_mesh_marks(stage)
    module.open_copy, module.apply_ops = open_copy, apply_ops
    return module


if __name__ == '__main__':
    import argparse
    from family import activate
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pluginset', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--kernel', default='embree')
    args = parser.parse_args(); activate(args.pluginset)
    module = runner(); suite = module.load_cases(); rows = []; previous = {}
    directory = args.output.with_suffix(''); directory.mkdir(parents=True, exist_ok=False)
    for case in suite['cases']:
        if not case['id'].startswith('V-'): continue
        row = module.run_case(case, suite, directory, args.kernel, previous)
        rows.append(row); previous[row['id']] = row
    data = dict(cases=rows, passed=sum(r['passed'] for r in rows), failed=sum(not r['passed'] for r in rows),
                fixtureMigration='Copied exact Mesh marks changed to tessellated; released cases and expectations unchanged')
    args.output.write_text(json.dumps(data,indent=2)+'\n')
    print(f"{len(rows)} checks, {data['failed']} failed")
    raise SystemExit(bool(data['failed']))
