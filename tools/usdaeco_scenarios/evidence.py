"""Measure published variants and consume fresh repository example findings."""
import hashlib
import json
from pathlib import Path

VARIANTS = ('base', 'floors', 'pod', 'clash', 'iris')


def committed_rows(paths):
    """Fast checks inspect publication inventories and relocated stock stages."""
    from usdaeco_check.structure import check_structure
    rows = []
    for name in ('plan', 'compliance', 'repeat', 'clash', 'solid'):
        checks = check_structure(paths[name], only=['S20', 'S21', 'S22', 'S23', 'S25', 'S27'])
        rows.append(dict(gate=name + ' committed publication',
                         passed=len(checks) == 6 and all(checks),
                         result=f'{sum(bool(c) for c in checks)}/6 source, inventory and relocated stock USD checks; no reproduction',
                         evidence=[dict(rule=c.name, passed=bool(c), detail=c.detail) for c in checks]))
    rows.append(dict(gate='new use-case PASS coverage', passed=all(r['passed'] for r in rows),
                     result=f"{sum(r['passed'] for r in rows)}/5 repositories have a measured committed-publication PASS row"))
    return rows


def variant_rows(root):
    from pxr import Usd, UsdGeom
    rows = []
    for variant in VARIANTS:
        directory = Path(root) / 'dist' / variant
        try:
            manifest = json.loads((directory / 'dc.manifest.json').read_text())
            stage = Usd.Stage.Open(str(directory / 'dc.usda'))
            prims = list(stage.Traverse())
            elements = [p for p in prims if p.HasAPI('AecoElementAPI')]

            def parented(prim):
                parent = prim.GetParent()
                while parent and not parent.IsPseudoRoot():
                    if parent.GetTypeName() in ('AecoSite','AecoFacility','AecoFacilityPart','AecoLevel','AecoSpace'):
                        return True
                    parent = parent.GetParent()
                return False

            counts = dict(elements=len(elements), levels=sum(p.GetTypeName() == 'AecoLevel' for p in prims),
                          spaces=sum(p.GetTypeName() == 'AecoSpace' for p in prims),
                          meshes=sum(p.IsA(UsdGeom.Mesh) for p in prims), ports=sum(p.GetTypeName() == 'AecoPort' for p in prims),
                          unparented=sum(not parented(p) for p in elements),
                          unclassified=sum((p.GetAttribute('aeco:class:ifc:code').Get() or '').split('.')[0]
                                           in ('', 'IfcBuildingElementProxy') for p in elements))
            hashes = all((directory / name).stat().st_size == item['bytes'] and
                         hashlib.sha256((directory / name).read_bytes()).hexdigest() == item['sha256']
                         for name, item in manifest['layers'].items())
            ok = (counts == manifest['counts'] and hashes and not stage.GetCompositionErrors()
                  and manifest['facility'] == 'demo-datacentre-01' and manifest['variant'] == variant)
            rows.append(dict(gate='published variant ' + variant, passed=ok,
                             result='; '.join(f'{k}={v}' for k, v in counts.items()) + '; manifest counts and layer hashes',
                             evidence=dict(actual=counts, expected=manifest['counts'], layerHashesMatch=hashes)))
        except Exception as exc:
            # USD parse/composition errors have their own exception classes.
            # A malformed publication must still produce its explicit FAIL row.
            rows.append(dict(gate='published variant ' + variant, passed=False, result='Missing or invalid published variant: ' + type(exc).__name__))
    return rows


def acceptance(name, findings):
    """Assert the specific demonstration defects, beyond a suite's exit status."""
    by_name = {r.get('name', r.get('kind')): r for r in findings}
    if name == 'plan':
        evidence = [r for r in findings if r.get('name') == 'ProgrammeEvidence']
        a = {r['name']: r['occurrences'] for r in findings if r.get('programme') == 'A' and 'severity' in r}
        b = [r for r in findings if r.get('programme') == 'B' and 'severity' in r]
        ok = (a == {'AccessAfterEnclosure': 4, 'WorkspaceOccupied': 1, 'EnclosureBeforeInspection': 2}
              and not b and {r['programme'] for r in evidence} == {'A', 'B'} and all(r['normalizedEqual'] for r in evidence))
        return ok, f'Programme A: {a}; B: {len(b)} findings; XER/MSPDI agree'
    if name == 'compliance':
        item = by_name['summary']
        ok = item['pass'] == 10 and item['fail'] == 1 and item['readers'] == 11 and item['clause_failures'] == 2
        return ok, f"{item['pass']} pass / {item['fail']} fail readers; {item['clause_failures']} clause failures"
    if name == 'repeat':
        item = by_name['FloorDrift']
        schedule = by_name['ScheduleDelta']
        ok = (item['all_changes'] == {'changed': 1, 'extra': 1} and item['extra_doors'] == 1
              and abs(schedule['partition_length_m'] - 3.2) <= 1e-6 and schedule['doors'] == 1)
        return ok, f"{item['all_changes']} floor differences; {schedule['partition_length_m']:.1f} m / {schedule['doors']:g} door delta"
    if name == 'clash':
        cases = {r['case']: r for r in findings if r.get('name') == 'RouteComparison'}
        ok = (len(cases) == 3 and cases['through-wall']['exact']['volume'] > 0
              and abs(cases['over-tray']['exact']['distance'] - .005) <= 1e-6
              and cases['over-tray']['decided_by'] == 'exact'
              and cases['tangent']['exact']['verdict'] == 'touching')
        return ok, f'{len(cases)} mesh/exact pairs; 5 mm gap and exact touching resolved'
    if name == 'solid':
        item, measures = by_name['ExactOfficeBodies'], by_name['Measurements']
        ok = (item['selected'] == item['exact'] == measures['twins'] == measures['twinsWithinTolerance'] > 0
              and item['failed'] == 0 and sum(v['exact'] for v in item['perClass'].values()) == item['exact'])
        return ok, f"{item['exact']}/{item['selected']} exact bodies; {measures['twinsWithinTolerance']} twins within tolerance; {measures['walls']} walls / {measures['pipes']} pipes measured"
    raise ValueError('Unknown example: ' + name)


def example_rows(paths, suites):
    from usdaeco_check.example import diff_findings
    rows = []
    for name in ('plan', 'compliance', 'repeat', 'clash', 'solid'):
        example = paths[name] / 'examples/datacentre'
        try:
            findings = json.loads((example / 'out/findings.json').read_text())
            ok, detail = acceptance(name, findings)
            suite_ok = suites.get(name, {}).get('passed', False)
            differences = diff_findings(findings, example / 'expected/findings.json')
            ok = ok and suite_ok and not differences
            if not suite_ok:
                detail += '; repository suite failed; full example acceptance not proven'
            if differences:
                detail += '; expected findings differ'
            rows.append(dict(gate=name + ' fresh example findings', passed=ok, result=detail,
                             evidence=dict(findings=findings, source=json.loads((example / 'out/manifest.json').read_text())['datacentre'])))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            rows.append(dict(gate=name + ' fresh example findings', passed=False,
                             result='Fresh suite findings unavailable or malformed; committed expectations alone are not execution evidence'))
    # Preserve independently measured publication proof even if a later,
    # separately reported example/render check fails or times out.
    try:
        data = json.loads((paths['solid'] / '.work/check.json').read_text())
        copies = data.get('doublePublication', [])
        fields = ('normalizedSha256', 'normalizedBytes', 'primCount')
        ok = (len(copies) == 2 and all(copies[0][k] == copies[1][k] for k in fields)
              and copies[0]['primCount'] > 0 and copies[0]['normalizedBytes'] > 0
              and len(copies[0]['normalizedSha256']) == 64)
        rows.append(dict(gate='solid publication determinism', passed=ok,
                         result=f'{len(copies)} temporary roots; fresh publication and authored-layer reflattening; normalized hashes, bytes and prim counts compared',
                         evidence=copies))
    except (OSError, ValueError, KeyError, TypeError):
        rows.append(dict(gate='solid publication determinism', passed=False,
                         result='Independent publication evidence unavailable'))
    coverage = {name: bool(suites.get(name, {}).get('passed')) or
                any(r['passed'] and r['gate'].startswith(name + ' ') for r in rows)
                for name in ('plan', 'compliance', 'repeat', 'clash', 'solid')}
    rows.append(dict(gate='new use-case PASS coverage', passed=all(coverage.values()),
                     result=f"{sum(coverage.values())}/{len(coverage)} repositories have at least one measured PASS row",
                     evidence=coverage))
    return rows
