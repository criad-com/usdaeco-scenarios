"""Train compatibility and migration preserve the reviewed consumer contract."""
import copy
import importlib.util
import json
from pathlib import Path

from pxr import Sdf, Usd, UsdGeom

from family import ROOT
from family_manifest import validate_family


def test_idempotence_checks_current_hashes_and_preserves_fixture_findings():
    spec = importlib.util.spec_from_file_location('published_consumer', ROOT / 'scenarios/published.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = {'Study': {'inputHash': 'older-evaluator', 'views': 2, 'results': {'covered': True}}}
    baseline = copy.deepcopy(fixture)
    baseline['Study']['inputHash'] = 'current-evaluator'
    repeated = copy.deepcopy(baseline)
    assert module.idempotent_studies(fixture, baseline, repeated)
    repeated['Study']['inputHash'] = 'changed-input'
    assert not module.idempotent_studies(fixture, baseline, repeated)
    baseline['Study']['results']['covered'] = False
    assert not module.idempotent_studies(fixture, baseline, copy.deepcopy(baseline))


def test_structure_report_uses_actual_counts_and_rejects_missing_results():
    from subprocess import CompletedProcess
    from check_all import structure_outcome
    passed, detail = structure_outcome(CompletedProcess([], 0, '29 checks, 0 failed'))
    assert passed and detail.startswith('29/29 structure checks')
    for code, output in [(0, ''), (0, '0 checks, 0 failed'),
                         (0, '29 checks, 1 failed'), (1, '29 checks, 0 failed')]:
        assert not structure_outcome(CompletedProcess([], code, output))[0]


def test_seeds_are_inventory_entries_and_released_subset_is_compatible():
    inventory = json.loads((ROOT / 'family.json').read_text())
    entries = {row['name']: row for row in inventory['repos']}
    assert len(entries) == 25
    assert entries['usdaeco']['kind'] == 'suite'
    assert set(entries['usdaeco']['requires']) == {
        name for name, entry in entries.items() if entry['released'] and name != 'usdaeco'}
    assert entries['usdaeco-meta']['tag'] is None
    for name, tag in {'plan':'v0.1.4','compliance':'v0.1.3','repeat':'v0.2.1',
                      'clash':'v0.2.3','solid':'v0.1.5'}.items():
        assert entries['usdaeco-' + name]['tag'] == tag
    assert validate_family(inventory, inventory=True)
    released = dict(inventory, repos=[r for r in inventory['repos'] if r['tag']])
    assert validate_family(released)
    broken = copy.deepcopy(released)
    next(r for r in broken['repos'] if r['name'] == 'usdaeco-ifc')['requires']['usdAeco'] = '>=0.8,<0.9'
    assert not validate_family(broken)


def test_inventory_tags_and_exact_dependency_refs_agree():
    entries = {row['name']: row for row in json.loads((ROOT / 'family.json').read_text())['repos']}
    from family import dependency_pins
    for pin in dependency_pins().values():
        assert entries[pin['repo']]['tag'] == entries[pin['repo']]['released'] == pin['ref']
        assert pin['ref'].startswith('v') and 'revision' not in pin


def test_train_bounds_and_legacy_tag_alias_are_checked():
    inventory = json.loads((ROOT / 'family.json').read_text())
    for change in ({'floor': 'v0.9.4'}, {'tag': 'v0.9.2'}, {'floor': None}):
        broken = copy.deepcopy(inventory)
        broken['repos'][0].update(change)
        assert not validate_family(broken, inventory=True)


def test_native_kit_projection_keeps_range_failures():
    inventory = json.loads((ROOT / 'family.json').read_text())
    released = dict(inventory, repos=[r for r in inventory['repos'] if r['tag']])
    next(r for r in released['repos'] if r['name'] == 'usdSolidOcct')['requires']['usdSolid'] = '>=0.2,<0.3'
    assert not validate_family(released)


def test_missing_wave_two_repository_is_not_a_present_placeholder(tmp_path):
    from family import placeholder_sources
    entries = [dict(name='usdaeco-plan', kind='usecase', tag=None)]
    result = placeholder_sources(tmp_path / 'missing', tmp_path / 'output', entries)
    assert result == {'usdaeco-plan': {'present': False}}


def test_missing_pinned_source_fails_before_building(monkeypatch, tmp_path):
    import family
    import pytest
    monkeypatch.setattr(family, 'repos', lambda **kwargs: {'core': tmp_path / 'missing'})
    with pytest.raises(RuntimeError, match='Pinned source unavailable: core'):
        family.audit_sources()


def test_publication_fixture_preserves_source_and_refuses_dirty_copy(tmp_path):
    import subprocess
    import pytest
    from family import publication_fixture
    source = tmp_path / 'source'
    source.mkdir()
    subprocess.run(['git', 'init', '-q', str(source)], check=True)
    (source / 'fixture.txt').write_text('tagged input\n')
    subprocess.run(['git', 'add', '.'], cwd=source, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'Fixture'], cwd=source, check=True)
    destination = tmp_path / 'example/out/pinned/data'
    assert publication_fixture(source, destination) == destination
    assert publication_fixture(source, destination) == destination
    (destination / 'fixture.txt').write_text('changed input\n')
    with pytest.raises(RuntimeError, match='differs from its audited source'):
        publication_fixture(source, destination)
    assert (source / 'fixture.txt').read_text() == 'tagged input\n'


def test_core_registry_probe_rejects_empty_metadata(monkeypatch):
    from family import require_core_validators
    from pxr import UsdValidation
    class EmptyRegistry:
        def GetValidatorMetadataForKeyword(self, keyword):
            return []
        def GetOrLoadValidatorsByName(self, names):
            return []
    monkeypatch.setattr(UsdValidation, 'ValidationRegistry', EmptyRegistry)
    import pytest
    with pytest.raises(RuntimeError, match='eight core validators'):
        require_core_validators()


def test_copied_mesh_migration_preserves_geometry_and_driver_values():
    spec = importlib.util.spec_from_file_location('consumer_cctv_test', ROOT / 'scenarios/cctv.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    stage = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(stage, '/Element/Body')
    mesh.CreatePointsAttr([(0,0,0),(1,0,0),(0,1,0)])
    mesh.CreateFaceVertexCountsAttr([3]); mesh.CreateFaceVertexIndicesAttr([0,1,2])
    prim = mesh.GetPrim(); prim.ApplyAPI('AecoDerivedGeometryAPI')
    prim.GetAttribute('aeco:derived:approx').Set('exact')
    root = stage.GetPrimAtPath('/Element')
    root.CreateAttribute('aeco:props:Fixture:driver',Sdf.ValueTypeNames.Double).Set(3.5)
    before = {p.GetPath(): p.Get() for p in (mesh.GetPointsAttr(),mesh.GetFaceVertexCountsAttr(),mesh.GetFaceVertexIndicesAttr(),root.GetAttribute('aeco:props:Fixture:driver'))}
    assert module.migrate_mesh_marks(stage) == 1
    assert prim.GetAttribute('aeco:derived:approx').Get() == 'tessellated'
    assert {path: stage.GetAttributeAtPath(path).Get() for path in before} == before
    assert module.migrate_mesh_marks(stage) == 0


def test_term_sweep_covers_both_private_address_families(tmp_path):
    from sanitization import scan
    artifact = tmp_path / 'metadata.json'
    for first in ('10','100'):
        artifact.write_text(json.dumps({'address': '.'.join([first,'64','1','2'])}))
        assert not scan([artifact])['passed']
    artifact.write_text(json.dumps({'facility':'demo-datacentre-01'}))
    assert scan([artifact])['passed']
