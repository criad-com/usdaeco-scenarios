"""Shared published-stage checks and historical profile regression helpers."""
import hashlib
import json
import os
from pathlib import Path
import sys
from family import ROOT, environment, repos, run

def validate_raw_conversion(core_path):
    """Refuse invalid raw USD before any kind importer can mask a type error."""
    from pxr import Usd, UsdValidation
    stage = Usd.Stage.Open(str(core_path))
    registry = UsdValidation.ValidationRegistry()
    names = [m.name for m in registry.GetValidatorMetadataForKeyword('UsdCoreValidators')]
    if not names:
        raise RuntimeError('Raw conversion: built-in USD validators are unavailable')
    issues = UsdValidation.ValidationContext(registry.GetOrLoadValidatorsByName(names)).Validate(stage)
    errors = [e for e in issues if e.GetType() == UsdValidation.ValidationErrorType.Error]
    evidence = dict(builtinErrors=len(errors),
                    builtinTypeErrors=sum(e.GetName() == 'AttributeTypeMismatch' for e in errors),
                    compositionErrors=len(stage.GetCompositionErrors()))
    if errors or evidence['compositionErrors']:
        raise RuntimeError('Raw conversion failed validation: ' + json.dumps(evidence)
                           + '; ' + '; '.join(e.GetMessage() for e in errors[:5]))
    return evidence


def door_points(door):
    """Approach face, 0.25 m samples, inset 0.1 m from the opening edges."""
    import numpy as np
    normal = {'N': (0, 1, 0), 'S': (0, -1, 0), 'E': (1, 0, 0), 'W': (-1, 0, 0),
              '+x': (1, 0, 0), '-x': (-1, 0, 0), '+y': (0, 1, 0), '-y': (0, -1, 0)}[door['approach_normal'].lower() if door['approach_normal'].startswith(('+','-')) else door['approach_normal']]
    n = np.asarray(normal)
    across = np.array([-n[1], n[0], 0])
    centre = np.asarray(door['centre'], dtype=float)
    centre[2] -= 1.6  # generator's threshold_height is the target datum
    return [list(centre + n * .15 + across * x + np.array([0, 0, z]))
            for x in np.arange(-door['width']/2 + .1, door['width']/2, .25)
            for z in np.arange(.3, min(door['height'], 2.1), .25)]


def grid_points(polygon, spacing=.5, inset=0.):
    import numpy as np
    lo, hi = np.min(polygon, axis=0), np.max(polygon, axis=0)
    return [[float(x), float(y), float(lo[2]+1.5)]
            for x in np.arange(lo[0]+spacing/2+inset, hi[0]-inset, spacing)
            for y in np.arange(lo[1]+spacing/2+inset, hi[1]-inset, spacing)]


def spatial_tiles(points, width=4.):
    """Partition samples without removing or moving any point."""
    import math
    groups = {}
    for point in points:
        cell=(math.floor(point[0]/width),math.floor(point[1]/width))
        groups.setdefault(cell,[]).append(point)
    return [groups[key] for key in sorted(groups)]


def normalize_stage(stage):
    """Sort declaration order; retain authored ordering, data and relationships."""
    from pxr import Usd
    layer = stage.Flatten()
    original_orders = {}
    def order(prim):
        if prim.HasInfo('primOrder'):
            original_orders[str(prim.path)] = prim.GetInfo('primOrder')
        children = list(prim.nameChildren.values())
        if children:
            prim.nameChildrenOrder = sorted(p.name for p in children)
        for child in children:
            order(child)
    order(layer.pseudoRoot)
    # A second flatten emits definitions in the canonical traversal order.
    layer = Usd.Stage.Open(layer).Flatten()
    def restore(prim):
        if str(prim.path) in original_orders:
            prim.SetInfo('primOrder', original_orders[str(prim.path)])
        else:
            prim.ClearInfo('primOrder')
        for child in prim.nameChildren.values():
            restore(child)
    restore(layer.pseudoRoot)
    layer.documentation = ''
    layer.customLayerData = {k:v for k,v in layer.customLayerData.items() if k not in ('aeco:cctv:time',)}
    return layer.ExportToString()


def semantic_digest(stage):
    return hashlib.sha256(normalize_stage(stage).encode()).hexdigest()


def stable_reports(reports):
    return {name: {k:r[k] for k in ('inputHash','results','exclusionsCovered','unphasedInView','unclassifiedInView','views')}
            for name,r in sorted(reports.items())}


def portable(value, directory):
    """Reports refer to artifact-relative files, including diagnostic layer sites."""
    if isinstance(value, dict):
        return {str(k):portable(v,directory) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [portable(v,directory) for v in value]
    if isinstance(value,str):
        for base in sorted({str(Path(directory).resolve()),str(ROOT),*[str(p) for p in repos().values()]},key=len,reverse=True):
            value=value.replace(base+'/', '')
        return value
    return value


def vanilla(paths):
    script = '''import sys
from pxr import Plug, Usd
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
count=0
for path in sys.argv[1:]:
    s=Usd.Stage.Open(path); assert s and not s.GetCompositionErrors()
    f=s.GetMetadata('fallbackPrimTypes')
    assert all(p.GetTypeName() in f for p in s.Traverse() if p.GetTypeName().startswith('Aeco'))
    assert s.Flatten()
    count+=sum(1 for p in s.Traverse())
print(count)
'''
    env=environment()
    env.pop('PXR_PLUGINPATH_NAME',None)
    return int(run([sys.executable,'-c',script,*paths],env=env).strip())


def bonsai_available():
    return Path(os.environ.get('AECO_BLENDER','/Applications/Blender.app/Contents/MacOS/Blender')).is_file()


def column_exception(studies, manifest_path):
    """Match the released redundant-sightline exception without hiding new defects."""
    def signature(results):
        return {target: dict(
            blockers=sorted(b for b in result['blockers'] if Path(b).name.startswith('col_')),
            views=sorted(note for note in result['viewNotes'] if ' blocked by col_' in note),
            **{key: result[key] for key in ('fixedCoverage', 'fraction', 'required',
                                          'sampleCount', 'enclosedSamples', 'evaluatedSamples')})
            for target, result in results.items()
            if any(Path(b).name.startswith('col_') for b in result['blockers'])}

    actual = {name: signature(report['results']) for name, report in studies.items()}
    actual = {name: results for name, results in actual.items() if results}
    evidence = dict(manifest='artifacts/column-view-exception.json', matched=False)
    try:
        content = Path(manifest_path).read_bytes()
        manifest = json.loads(content)
        original = manifest['originalResults']
        expected = signature(original)
        dedicated = manifest['results']
        # The released proof uses only the four assigned corridor cameras.
        proof = (manifest['passed'] is True and bool(expected)
                 and set(expected) == set(original) == set(dedicated)
                 and len(manifest['selectedCameras']) == len(set(manifest['selectedCameras'])) == 4
                 and all(result['fixedCoverage'] is True and result['fraction'] == 1.
                         and result['sampleCount'] == result['evaluatedSamples'] > 0
                         and result['enclosedSamples'] == 0 and result['views']
                         and not result['blockers'] for result in dedicated.values()))
        matched = (proof and actual == {'Corridors': expected}
                   and all(r['fixedCoverage'] is True and r['fraction'] == 1.
                           for r in expected.values()))
        evidence.update(matched=bool(matched), sha256=hashlib.sha256(content).hexdigest(),
                        documentedTargets=len(expected))
        evidence['note'] = ('Documented redundant corridor sightlines match exactly; all affected samples retain fixed coverage.'
                            if matched else 'Column blockers or coverage differ from the documented exception.')
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        evidence['note'] = 'The generator column exception manifest is missing or invalid.'
    return evidence
