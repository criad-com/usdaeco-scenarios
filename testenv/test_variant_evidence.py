"""Published counts and hashes are both necessary evidence."""
import hashlib
import json

from pxr import Usd, UsdGeom
from usdaeco_scenarios.evidence import variant_rows, VARIANTS


def test_variant_manifest_cannot_hide_changed_stage(tmp_path):
    for variant in VARIANTS:
        root = tmp_path / 'dist' / variant
        root.mkdir(parents=True)
        stage = Usd.Stage.CreateNew(str(root / 'dc.usda'))
        UsdGeom.Xform.Define(stage, '/World')
        stage.GetRootLayer().Save()
        path = root / 'dc.usda'
        manifest = dict(facility='demo-datacentre-01', variant=variant,
                        counts=dict(elements=0, levels=0, spaces=0, meshes=0, ports=0, unparented=0, unclassified=0),
                        layers={'dc.usda': dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())})
        (root / 'dc.manifest.json').write_text(json.dumps(manifest))
    assert all(row['passed'] for row in variant_rows(tmp_path))
    path = tmp_path / 'dist/floors/dc.manifest.json'
    data = json.loads(path.read_text())
    data['counts']['elements'] = 1
    path.write_text(json.dumps(data))
    assert not next(r for r in variant_rows(tmp_path) if r['gate'].endswith('floors'))['passed']
    data['counts']['elements'] = 0
    data['layers']['dc.usda']['sha256'] = '0' * 64
    path.write_text(json.dumps(data))
    assert not next(r for r in variant_rows(tmp_path) if r['gate'].endswith('floors'))['passed']


def test_absent_variants_are_failures(tmp_path):
    rows = variant_rows(tmp_path)
    assert len(rows) == 5 and all(not row['passed'] for row in rows)


def test_independent_solid_publication_hash_difference_fails(tmp_path):
    from usdaeco_scenarios.evidence import example_rows
    paths = {name: tmp_path / name for name in ('plan','compliance','repeat','clash','solid')}
    path = paths['solid'] / '.work/check.json'
    path.parent.mkdir(parents=True)
    first = dict(normalizedSha256='a' * 64, normalizedBytes=100, primCount=2)
    path.write_text(json.dumps({'doublePublication': [first, first]}))
    assert next(r for r in example_rows(paths, {}) if r['gate'] == 'solid publication determinism')['passed']
    path.write_text(json.dumps({'doublePublication': [first, dict(first, normalizedSha256='b' * 64)]}))
    assert not next(r for r in example_rows(paths, {}) if r['gate'] == 'solid publication determinism')['passed']


def test_solid_reflatten_compares_content_and_retains_separate_timings(tmp_path):
    from usdaeco_scenarios.evidence import example_rows
    paths = {name: tmp_path / name for name in ('plan','compliance','repeat','clash','solid')}
    path = paths['solid'] / '.work/check.json'
    path.parent.mkdir(parents=True)
    content = dict(normalizedSha256='a' * 64, normalizedBytes=100, primCount=2)
    records = [dict(content, operation='freshPublication', seconds=100),
               dict(content, operation='reflattenOwnLayers', seconds=2)]
    path.write_text(json.dumps({'doublePublication': records}))
    row = next(r for r in example_rows(paths, {}) if r['gate'] == 'solid publication determinism')
    assert row['passed'] and row['evidence'] == records
    records[1]['primCount'] = 3
    path.write_text(json.dumps({'doublePublication': records}))
    assert not next(r for r in example_rows(paths, {}) if r['gate'] == 'solid publication determinism')['passed']


def test_fast_publication_checks_exclude_reproduction_and_keep_defects(monkeypatch, tmp_path):
    from usdaeco_check import Result
    from usdaeco_scenarios.evidence import committed_rows
    paths = {name: tmp_path / name for name in ('plan','compliance','repeat','clash','solid')}
    broken = []
    def structure(root, *, only):
        assert only == ['S20', 'S21', 'S22', 'S23', 'S25', 'S27']
        return [Result(rule, not (root.name in broken and rule == 'S27')) for rule in only]
    monkeypatch.setattr('usdaeco_check.structure.check_structure', structure)
    assert all(r['passed'] for r in committed_rows(paths))
    broken.append('solid')
    rows = committed_rows(paths)
    assert not next(r for r in rows if r['gate'] == 'solid committed publication')['passed']
    assert not rows[-1]['passed']
