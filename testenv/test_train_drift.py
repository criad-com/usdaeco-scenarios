"""Seed train drift without altering any tagged repository."""
import json

import pytest

from usdaeco_scenarios.drift import audit, HEADINGS


@pytest.fixture
def release(tmp_path):
    family = {'repos': [dict(name='usdaeco-core', library='usdAeco', released='v0.9.3', floor='v0.9.2', kind='library'),
                        dict(name='usdaeco-example', library='usdAecoExample', released='v0.1.0', floor='v0.1.0', kind='usecase')]}
    root = tmp_path / 'usdaeco-example'
    root.mkdir()
    (root / 'library.json').write_text(json.dumps({'requires': {'usdAeco': '>=0.9,<1.0'}}))
    (root / 'dependencies.json').write_text(json.dumps({'repos': {'core': {'repo': 'usdaeco-core', 'library': 'usdAeco', 'ref': 'v0.9.2'}}}))
    (root / 'docs').mkdir()
    (root / 'docs/usecase.md').write_text('\n'.join('## ' + h for h in HEADINGS))
    result = root / 'examples/datacentre/result'
    result.mkdir(parents=True)
    for name in ('example.usdc', 'README.md', 'vanilla.png'):
        (result / name).touch()
    (result / 'layers').mkdir()
    return family, root


def test_strict_drift_accepts_matching_pin_and_both_ranges(release):
    family, root = release
    result = audit(family, {'usdaeco-example': root})
    assert all(r['passed'] for key in ('pins','ranges','stories') for r in result[key])


@pytest.mark.parametrize('ref,passed', [('v0.9.1', False), ('v0.9.2', True),
                                     ('v0.9.3', True), ('v0.9.4', False)])
def test_inclusive_train_boundaries(release, ref, passed):
    family, root = release
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core']['ref'] = ref
    path.write_text(json.dumps(data))
    assert audit(family, {'usdaeco-example': root})['pins'][0]['passed'] is passed


def test_in_range_pin_can_still_violate_its_own_requirement(release):
    family, root = release
    (root / 'library.json').write_text(json.dumps({'requires': {'usdAeco': '>=0.9.3,<1.0'}}))
    report = audit(family, {'usdaeco-example': root})
    assert not report['pins'][0]['passed']
    assert not report['ranges'][0]['passed']


def test_floor_revision_is_checked_against_floor_tag_not_released(release, monkeypatch):
    family, root = release
    monkeypatch.setattr('usdaeco_scenarios.drift.revision',
                        lambda root, tag: {'v0.9.2': 'a' * 40, 'v0.9.3': 'b' * 40}[tag])
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core']['revision'] = 'a' * 40
    path.write_text(json.dumps(data))
    assert audit(family, {'usdaeco-example': root})['pins'][0]['passed']
    data['repos']['core']['revision'] = 'b' * 40
    path.write_text(json.dumps(data))
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']


@pytest.mark.parametrize('ref,version', [('v0.9.1', '0.9.2'), ('a' * 40, '0.9.2')])
def test_version_label_cannot_disguise_out_of_train_source(release, monkeypatch, ref, version):
    family, root = release
    monkeypatch.setattr('usdaeco_scenarios.drift.revision', lambda *args: 'b' * 40)
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core'].update(ref=ref, version=version)
    path.write_text(json.dumps(data))
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']


@pytest.mark.parametrize('floor,released', [(None, 'v0.9.3'), ('v0.9.4', 'v0.9.3'),
                                         ('v0.9.2', None)])
def test_invalid_train_bounds_fail(release, floor, released):
    family, root = release
    family['repos'][0].update(floor=floor, released=released)
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']


@pytest.mark.parametrize('repo,ref,rule', [('usdaeco-core','v0.9.1','pins'),
                                        ('usdaeco-unknown','v0.9.2','pins'),
                                        ('usdaeco-core','v0.8.4','ranges')])
def test_seeded_pin_drift(release, repo, ref, rule):
    family, root = release
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core'].update(repo=repo, ref=ref)
    path.write_text(json.dumps(data))
    result = audit(family, {'usdaeco-example': root})
    assert any(not r['passed'] for r in result[rule])


def test_train_version_must_also_satisfy_range(release):
    family, root = release
    family['repos'][0]['released'] = 'v1.0.0'
    assert not audit(family, {'usdaeco-example': root})['ranges'][0]['passed']


@pytest.mark.parametrize('defect', ['missing-doc', 'section-order', 'missing-result'])
def test_seeded_story_defects(release, defect):
    family, root = release
    document = root / 'docs/usecase.md'
    if defect == 'missing-doc':
        document.unlink()
    elif defect == 'section-order':
        document.write_text('\n'.join('## ' + h for h in reversed(HEADINGS)))
    else:
        (root / 'examples/datacentre/result/example.usdc').unlink()
    assert any(not r['passed'] for r in audit(family, {'usdaeco-example': root})['stories'])


def test_missing_dependency_manifest_is_failure(release):
    family, root = release
    (root / 'dependencies.json').unlink()
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']


def test_matching_tag_cannot_hide_wrong_revision(release, monkeypatch):
    family, root = release
    monkeypatch.setattr('usdaeco_scenarios.drift.revision', lambda *args: 'a' * 40)
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core']['revision'] = 'b' * 40
    path.write_text(json.dumps(data))
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']
    data['repos']['core']['revision'] = 'a' * 40
    path.write_text(json.dumps(data))
    assert audit(family, {'usdaeco-example': root})['pins'][0]['passed']


def test_build_kit_is_subject_to_public_floor(release):
    family, root = release
    family['repos'].append(dict(name='aeco-toolchain', library=None, kind='kit',
                                floor='v0.4.0', released='v0.4.0'))
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['build'] = dict(repo='aeco-toolchain', ref='v0.3.0')
    path.write_text(json.dumps(data))
    result = audit(family, {'usdaeco-example': root})
    assert not result['external']
    assert any(r.get('dependency') == 'aeco-toolchain' and not r['passed'] for r in result['pins'])


def test_public_commit_evidence_is_checked_without_changing_tag_bounds(release, monkeypatch):
    family, root = release
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core'].update(revision='a' * 40, publicRevision='b' * 40)
    path.write_text(json.dumps(data))
    monkeypatch.setattr('usdaeco_scenarios.drift.revision', lambda *args: 'b' * 40)
    assert audit(family, {'usdaeco-example': root})['pins'][0]['passed']
    monkeypatch.setattr('usdaeco_scenarios.drift.revision', lambda *args: 'c' * 40)
    assert not audit(family, {'usdaeco-example': root})['pins'][0]['passed']


def test_fixtures_do_not_become_direct_pins_or_satisfy_requirements(release):
    family, root = release
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['fixtures'] = {'old-core': dict(data['repos']['core'], ref='v0.8.4')}
    path.write_text(json.dumps(data))
    report = audit(family, {'usdaeco-example': root})
    assert len(report['pins']) == 1 and report['pins'][0]['passed']
    assert report['ranges'][0]['passed']
    assert report['fixtures'][0]['declaration']['ref'] == 'v0.8.4'
    data['repos'] = {}
    path.write_text(json.dumps(data))
    assert not audit(family, {'usdaeco-example': root})['ranges'][0]['passed']


def test_fixture_declaration_cannot_waive_a_direct_mismatch(release):
    family, root = release
    path = root / 'dependencies.json'
    data = json.loads(path.read_text())
    data['repos']['core']['ref'] = 'v0.9.1'
    data['fixtures'] = {'core': data['repos']['core']}
    path.write_text(json.dumps(data))
    row = audit(family, {'usdaeco-example': root})['pins'][0]
    assert not row['passed']
    assert (row['dependency'], row['ref'], row['floor']) == ('usdaeco-core', 'v0.9.1', 'v0.9.2')
