#!/usr/bin/env python3
"""Consumer acceptance on released stages and the CCTV-owned example."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from family import ROOT, activate, repos


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def idempotent_studies(fixture, baseline, repeated):
    """Keep current hashes identical; compare findings across receipt versions."""
    def findings(reports):
        return {name: {key: value for key, value in report.items() if key != 'inputHash'}
                for name, report in reports.items()}
    return baseline == repeated and findings(fixture) == findings(baseline)


def compose(source, example, output):
    """Use the released hook and inputs; write only a consumer-owned root layer."""
    from pxr import Sdf, Usd
    from usdaeco_cctv.example import hook
    output.mkdir(parents=True)
    base = Usd.Stage.Open(str(source))
    layer = Sdf.Layer.CreateNew(str(output / 'example.usda'))
    layer.subLayerPaths = [os.path.relpath(p, output) for p in sorted((example / 'inputs').glob('*.usda'))] + [os.path.relpath(source, output)]
    stage = Usd.Stage.Open(layer)
    for key in ('defaultPrim', 'upAxis', 'metersPerUnit', 'fallbackPrimTypes', 'startTimeCode', 'endTimeCode', 'timeCodesPerSecond'):
        if base.HasAuthoredMetadata(key):
            stage.SetMetadata(key, base.GetMetadata(key))
    findings = hook(stage, output)
    layer.subLayerPaths = [os.path.relpath(p, output) if Path(p).is_absolute() else p for p in layer.subLayerPaths]
    layer.Save()
    (output / 'findings.json').write_text(json.dumps(findings, indent=2, sort_keys=True) + '\n')
    return stage, findings


def run_scenario(output, pluginset):
    from pxr import Plug
    for name, library in [('core','usdAeco'),('axis','usdAecoAxis')]:
        Plug.Registry().RegisterPlugins(str(repos()[name] / (library + 'Validators')))
    activate(pluginset)
    from pxr import Gf, Plug, Sdf, Usd, UsdGeom, UsdValidation
    from usdaeco_check.example import diff_findings
    from usdaeco_check.images import image_info, pixels
    import numpy as np
    from usdaeco_check.validation import run as validate
    from usdaeco_cctv import sensors_of
    from usdaeco_cctv.study import clear_caches, run_study
    from demo.datacentre import scenario_module
    from sanitization import scan
    import usdaeco_render
    dc = scenario_module()
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=False)
    paths = repos(); rows = []; started = time.monotonic()
    def record(gate, ok, detail, *, status=None, **evidence):
        rows.append(dict(gate=gate, status=status or ('PASS' if ok else 'FAIL'), result=detail, evidence=evidence))
        print(rows[-1]['status'], gate, detail, flush=True)
        (output / 'report.json').write_text(json.dumps(dict(rows=rows), indent=2) + '\n')
    source = paths['datacentre'] / 'dist/base/dc.usda'
    example = paths['cctv'] / 'examples/datacentre'
    watched = [p for p in source.parent.iterdir() if p.is_file()] + [p for p in example.rglob('*') if p.is_file() and 'out' not in p.relative_to(example).parts]
    before = {p: digest(p) for p in watched}
    manifest = json.loads(source.with_name('dc.manifest.json').read_text())
    stage = Usd.Stage.Open(str(source)); prims = list(stage.Traverse())
    record('datacentre build', False, 'consumer uses published stages; generator timing is in the data repository check', status='NOT RUN')
    record('DC-build', manifest['facility'] == 'demo-datacentre-01' and manifest['variant'] == 'base',
           'published dist/base; source mode pinned; generator not invoked')
    for name, info in manifest['layers'].items():
        path = source.parent / name
        record('DC-layer ' + name, digest(path) == info['sha256'] and path.stat().st_size == info['bytes'],
               f"{info['bytes']} bytes; manifest hash matches", sha256=info['sha256'])
    counts = dict(elements=sum(p.HasAPI('AecoElementAPI') for p in prims), levels=sum(p.GetTypeName() == 'AecoLevel' for p in prims),
                  spaces=sum(p.GetTypeName() == 'AecoSpace' for p in prims), meshes=sum(p.IsA(UsdGeom.Mesh) for p in prims),
                  ports=sum(p.GetTypeName() == 'AecoPort' for p in prims))
    elements = [p for p in prims if p.HasAPI('AecoElementAPI')]
    def parented(prim):
        parent = prim.GetParent()
        while parent and not parent.IsPseudoRoot():
            if parent.GetTypeName() in ('AecoSite','AecoFacility','AecoFacilityPart','AecoLevel','AecoSpace'):
                return True
            parent = parent.GetParent()
        return False
    counts['unparented'] = sum(not parented(p) for p in elements)
    counts['unclassified'] = sum((p.GetAttribute('aeco:class:ifc:code').Get() or '').split('.')[0]
                                 in ('','IfcBuildingElementProxy') for p in elements)
    for name, count in counts.items():
        record('DC-count ' + name, count == manifest['counts'][name], f"{count}/{manifest['counts'][name]}")
    elements = [p for p in prims if p.HasAPI('AecoElementAPI')]
    ids = [p.GetAttribute('aeco:id').Get() for p in elements]
    record('DC-identities', len(set(ids)) == len(ids) and all(ids), f'{len(set(ids))} unique element identities')
    phased = sum(p.GetAttribute('aeco:phase').Get() in ('existing','proposed','temporary','demolished') for p in elements)
    record('DC-phases', phased == len(elements), f'{phased}/{len(elements)} authored asset phases')
    raw = dc.validate_raw_conversion(source)
    record('DC-convert', not any(raw.values()), 'published conversion; no USD type or composition errors', **raw)
    for name in ('core','axis'):
        Plug.Registry().RegisterPlugins(str(paths[name] / (('usdAeco' if name == 'core' else 'usdAecoAxis') + 'Validators')))
    errors = validate(stage, ['UsdAecoValidators'])
    serious = [e for e in errors if e.GetType() == UsdValidation.ValidationErrorType.Error]
    record('DC-profile', not serious, f'{len(serious)} core errors; {len(errors)-len(serious)} non-errors')
    record('DC-vanilla-base', dc.vanilla([source]) > 0, 'published base composes with no family plugins')
    print('== stage: pinned CCTV hook', flush=True)
    composed, findings = compose(source, example, output / 'first')
    differences = diff_findings(findings, example / 'expected/findings.json')
    record('DC-example findings', not differences, 'CCTV committed expected findings match' if not differences else '; '.join(differences),
           sourceMode='pinned', datacentre=json.loads((paths['datacentre'] / 'library.json').read_text())['version'],
           exampleDatacentre=json.loads((example / 'manifest.json').read_text())['datacentre']['ref'],
           expectedSha256=digest(example / 'expected/findings.json'))
    by_name = {row['name']: row for row in findings}
    imported, derived = by_name['Import'], by_name['Derive']
    record('DC-import', imported['cameras'] == imported['sensors'] == 45 and imported['types'] == 3 and imported['presets'] == 7 and imported['unmatched'] == 0,
           '45 cameras; 45 sensors; 3 types; 7 presets', **imported)
    record('DC-derive', derived['sensors'] == derived['sectors'] == 45 and derived['tours'] == 3 and not derived['skipped'],
           '45 sensors; 45 sectors; 3 tours', **derived)
    studies = {}
    for name, gate in [('CriticalDoors', 'DC-critical-doors'), ('Privacy', 'DC-privacy-baseline')]:
        data = json.loads((output / 'first' / (name + '.json')).read_text()); studies[name] = data
        expected = next(r for r in json.loads((example / 'expected/findings.json').read_text()) if r['name'] == name)
        actual = by_name[name]
        ok = not diff_findings(actual, expected)
        covered = sum(r['fixedCoverage'] for r in data['results'].values())
        record(gate, ok, f"{covered}/{len(data['results'])} fixed targets; {len(data['exclusionsCovered'])} exclusions covered; expected findings match", **dict(views=data['views']))
    initial_hash = dc.semantic_digest(composed)
    repeat_root = Sdf.Layer.CreateAnonymous('repeat.usda')
    repeat_root.subLayerPaths = [str(output / 'first/studies.usda')]
    repeat_stage = Usd.Stage.Open(repeat_root)
    for key in ('defaultPrim','upAxis','metersPerUnit','fallbackPrimTypes','timeCodesPerSecond','startTimeCode','endTimeCode'):
        if composed.HasAuthoredMetadata(key): repeat_stage.SetMetadata(key, composed.GetMetadata(key))
    # A portable example can retain an older fixture receipt. Establish the
    # current evaluator's result before testing its persistent cache reuse.
    baseline = {name: run_study(repeat_stage, '/SecurityStudies/' + name, output / 'first' / (name + '.usda'), kernel='auto') for name in studies}
    baseline_computed = sum(len(r['viewsComputed']) for r in baseline.values())
    repeat_stage = Usd.Stage.Open(repeat_root)
    repeats = {name: run_study(repeat_stage, '/SecurityStudies/' + name, output / 'first' / (name + '.usda'), kernel='auto') for name in studies}
    views = sum(r['views'] for r in repeats.values()); reused = sum(len(r['viewsReused']) for r in repeats.values())
    record('DC-idempotence', views == reused and idempotent_studies(
               dc.stable_reports(studies), dc.stable_reports(baseline), dc.stable_reports(repeats)),
           f'{reused}/{views} views reused on a reopened stage; {baseline_computed} views computed to establish the current evaluator baseline; stable results',
           baselineComputed=baseline_computed, reused=reused, views=views)
    clear_caches()
    second, second_findings = compose(source, example, output / 'second')
    second_studies = {name: json.loads((output / 'second' / (name + '.json')).read_text()) for name in studies}
    second_hash = dc.semantic_digest(second)
    record('DC-determinism', initial_hash == second_hash and not diff_findings(findings, second_findings)
           and dc.stable_reports(studies) == dc.stable_reports(second_studies),
           'two independent compositions; normalized stage, findings and study results', first=initial_hash, second=second_hash)
    # Exercise stale and incomplete result guards against the published example.
    from usdaeco_cctv import validators
    fresh = Usd.Stage.Open(str(output / 'first/example.usda'))
    with Usd.EditContext(fresh, fresh.GetSessionLayer()):
        camera = next(p for p in fresh.Traverse() if p.HasAPI('AecoCctvCameraAPI') and
                      p.GetAttribute('aeco:props:DC_Identity:Id').Get() == 'sec.cam.door.hall.a.w')
        sensor = sensors_of(camera)[0]
        sensor.GetAttribute('aeco:cctvSensor:pan').Set(sensor.GetAttribute('aeco:cctvSensor:pan').Get() + 20.)
    issues = validators._stale(fresh.GetPrimAtPath('/SecurityStudies/CriticalDoors'), None)
    record('DC-stale', any(e.GetName() == 'cctvStudyStale' for e in issues), 'driver edit invalidates prior study')
    fresh = Usd.Stage.Open(str(output / 'first/example.usda'))
    with Usd.EditContext(fresh, fresh.GetSessionLayer()):
        result = next(iter(fresh.GetPrimAtPath('/SecurityStudies/CriticalDoors/Results').GetChildren()))
        result.SetActive(False)
    issues = validators._incomplete(fresh.GetPrimAtPath('/SecurityStudies/CriticalDoors'), None)
    record('DC-results-incomplete', any(e.GetName() == 'cctvStudyIncomplete' for e in issues), 'removed result is diagnosed')
    # The third view is another source sensor on the same released example.
    # All presentation opinions are kept in a separate transient layer.
    render_layer = Sdf.Layer.CreateNew(str(output / 'views.usda'))
    render_layer.subLayerPaths = ['first/example.usda']; render_layer.Save()
    render_stage = Usd.Stage.Open(render_layer)
    for key in ('defaultPrim','upAxis','metersPerUnit','fallbackPrimTypes','timeCodesPerSecond','startTimeCode','endTimeCode'):
        if composed.HasAuthoredMetadata(key): render_stage.SetMetadata(key, composed.GetMetadata(key))
    with Usd.EditContext(render_stage, render_layer):
        camera = next(p for p in render_stage.Traverse() if p.HasAPI('AecoCctvCameraAPI') and
                      p.GetAttribute('aeco:props:DC_Identity:Id').Get() == 'sec.cam.lobby')
        sensor = UsdGeom.Camera(sensors_of(camera)[0]); view = UsdGeom.Camera.Define(render_stage, '/Renders/lobby')
        for getter in ('GetFocalLengthAttr','GetHorizontalApertureAttr','GetVerticalApertureAttr','GetClippingRangeAttr'):
            getattr(view,getter)().Set(getattr(sensor,getter)().Get())
        view.AddTransformOp().Set(UsdGeom.Xformable(sensor).ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
        hidden = 0
        for prim in render_stage.Traverse():
            if prim.GetAttribute('aeco:derived:role').Get() == 'extent':
                UsdGeom.Imageable(prim).MakeInvisible(); hidden += 1
    render_layer.Save()
    # Fixed diagnostic camera lighting retains the previous content/exposure
    # floor. These settings make no claim about facility illumination.
    os.environ.update(HDEMBREE_USE_LIGHTING='0', HDEMBREE_CAMERA_LIGHT_INTENSITY='160',
                      HDEMBREE_SAMPLES_TO_CONVERGENCE='8')
    records = usdaeco_render.render(output / 'views.usda', output=output / 'renders', size=(576,360), purposes='guide,proxy,render')
    content = {}
    for image in records:
        name = Path(image['path']).stem
        array = pixels(output / image['path'])
        luminance = array @ np.array([.2126,.7152,.0722])
        mean, std = float(luminance.mean()), float(luminance.std())
        coloured = (((array[:,:,0]>array[:,:,1]*1.35)&(array[:,:,2]>array[:,:,1]*1.2)&(array[:,:,0]>.25)) |
                    ((array[:,:,1]>array[:,:,0]*1.4)&(array[:,:,2]>array[:,:,0]*1.4)&(array[:,:,1]>.3)))
        content[name] = dict(meanLuminance=mean, stdLuminance=std, overlayColourPixels=int(coloured.sum()))
        record('DC-render ' + name, .15 <= mean <= .85 and std > .02 and
               image == dict(path=image['path'], **image_info(output / image['path'])),
               f"{image['width']}x{image['height']}; {image['bytes']} bytes; mean {mean:.6f}; standard deviation {std:.6f}",
               **image, **content[name])
    record('DC-render', len(records) == 3 and hidden == 33 and content['overview']['overlayColourPixels'] > 10,
           f'{len(records)}/3 views; {hidden} extent guides hidden; diagnostic camera light 160%', renders=records, content=content)
    record('DC-vanilla', dc.vanilla([output / 'first/example.usda',output / 'second/example.usda',output / 'views.usda']) > 0,
           '3 consumer stages compose with no family plugins')
    record('DC-source unchanged', before == {p: digest(p) for p in watched}, f'{len(watched)} published source and CCTV input/artifact files unchanged')
    for gate in ('DC-system','DC-external','DC-corridors','DC-yard-day','DC-yard-night','DC-lobby','DC-revit-parity',
                 'DC-column','DC-tray','DC-temporary','DC-privacy','DC-hall-rule','DC-noc-turn','DC-ptz-duty','DC-night-override'):
        record(gate, False, 'released CCTV example does not supply this historical study or policy case', status='NOT RUN')
    record('DC-sync-ifc', False, 'published USD has no editable native document; integration data-centre cases run separately', status='NOT RUN')
    record('DC-sync-bonsai', False, 'published USD has no editable native document; integration data-centre cases run separately', status='NOT RUN')
    record('DC-revit-reference', False, 'historical evidence does not match the current released artifacts', status='NOT RUN')
    record('DC-revit', False, 'live Revit execution outside this gate', status='NOT RUN')
    for path in output.rglob('*.json'):
        if path.name != 'report.json':
            path.write_text(json.dumps(dc.portable(json.loads(path.read_text()),output),indent=2,sort_keys=True)+'\n')
    sanitation = scan([p for p in output.rglob('*') if p.suffix in ('.json','.usda','.usdc') and p.name != 'report.json'])
    record('datacentre sanitization', sanitation['passed'], f"{sanitation['files']} text/stage assets; {len(sanitation['violations'])} violations", **sanitation)
    elapsed = time.monotonic() - started
    record('DC-budget', elapsed <= 240, f'{elapsed:.3f}s; 240s budget')
    return int(any(r['status'] == 'FAIL' for r in rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--pluginset', required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(run_scenario(args.output, args.pluginset))
