"""Release auditing fails before a build on an incompatible requirement or tag."""
import json

import pytest

from release_pins import audit, optional_compatibility


def test_wrong_release_revision(monkeypatch, tmp_path):
    monkeypatch.setattr('release_pins.git', lambda *args: 'b' * 40)
    rows = audit({'core': tmp_path}, {'core': {'base_tag': 'v0.8.1', 'revision': 'a' * 40}})
    assert not all(row['passed'] for row in rows)


def test_incompatible_schema_requirement(monkeypatch, tmp_path):
    monkeypatch.setattr('release_pins.git', lambda *args: 'a' * 40)
    core = tmp_path / 'schemas/usdAeco/library.json'
    core.parent.mkdir(parents=True)
    core.write_text(json.dumps({'name': 'usdAeco', 'version': '0.8.1'}))
    manifest = tmp_path / 'schemas/usdAecoCctv/library.json'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'requires': {'usdAeco': '>=0.9'}}))
    rows = audit({'core': tmp_path}, {'core': {'base_tag': 'v0.8.1', 'revision': 'a' * 40}})
    assert rows[0]['passed'] and not rows[1]['passed']
    assert 'against schema 0.8.1' in rows[1]['detail']


def test_strict_declarations_detect_stale_pin(monkeypatch, tmp_path):
    monkeypatch.setattr('release_pins.git', lambda *args: 'a' * 40)
    (tmp_path / 'dependencies.json').write_text(json.dumps({'optional': {
        'usdAeco': {'ref': 'v0.8.0', 'revision': 'a' * 40}}}))
    pins = {'core': {'base_tag': 'v0.8.1', 'revision': 'a' * 40}}
    rows = audit({'core': tmp_path, 'sync': tmp_path}, pins, strict=True)
    assert rows[0]['passed'] and not rows[1]['passed']


def test_optional_source_identity_is_required_without_claiming_compatibility(monkeypatch, tmp_path):
    monkeypatch.setattr('release_pins.git', lambda *args: 'b' * 40)
    (tmp_path / 'library.json').write_text(json.dumps({'requires': {'usdAeco': '==0.8.1'}}))
    rows = audit({'cctv-exec': tmp_path},
                 {'cctv-exec': {'base_tag': 'v0.1.1', 'revision': 'a' * 40}}, optional={'cctv-exec'})
    assert len(rows) == 1 and not rows[0]['passed']


def test_requirements_use_schema_version_independently_of_release_tag(monkeypatch, tmp_path):
    monkeypatch.setattr('release_pins.git', lambda *args: 'a' * 40)
    for name, version, requires in [('usdAeco', '0.8.1', {}),
                                    ('usdAecoCctv', '0.4.4', {'usdAeco': '==0.8.1'})]:
        manifest = tmp_path / 'schemas' / name / 'library.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(dict(name=name, version=version, requires=requires)))
    rows = audit({'core': tmp_path}, {'core': {'base_tag': 'v0.8.2', 'revision': 'a' * 40}})
    assert len(rows) == 2 and all(row['passed'] for row in rows)


@pytest.mark.parametrize('core,cctv,status,offending', [
    ('v0.8.4', 'v0.4.8', 'PROVEN', None),
    ('v0.8.1', 'v0.4.5', 'PROVEN', None),
    ('v0.8.4', 'v0.4.4', 'NOT PROVEN', 'usdAecoCctv >=0.4.5,<0.5'),
    ('v0.9.0', 'v0.4.8', 'NOT PROVEN', 'usdAeco >=0.8.1,<0.9'),
    ('v0.8.4', 'v0.5.0', 'NOT PROVEN', 'usdAecoCctv >=0.4.5,<0.5'),
    ('v0.8.4', None, 'NOT PROVEN', 'usdAecoCctv >=0.4.5,<0.5'),
])
def test_optional_compatibility_uses_declared_ranges(tmp_path, core, cctv, status, offending):
    (tmp_path / 'library.json').write_text(json.dumps({'requires': {
        'usdAeco': '>=0.8.1,<0.9', 'usdAecoCctv': '>=0.4.5,<0.5'}}))
    result = optional_compatibility({'cctv-exec': tmp_path},
                                    {'core': {'base_tag': core}, 'cctv': {'base_tag': cctv}},
                                    optional={'cctv-exec'})['cctv-exec']
    assert result['status'] == status
    assert len(result['checks']) == 2
    assert all(check['passed'] for check in result['checks']) == (status == 'PROVEN')
    if offending:
        assert offending in result['reason']
    assert 'outside the runtime plugin set' in result['reason']


@pytest.mark.parametrize('manifest', [None, {}, {'requires': {}},
                                     {'requires': {'usdAeco': 'invalid'}}])
def test_optional_missing_or_invalid_declarations_are_not_proof(tmp_path, manifest):
    if manifest is not None:
        (tmp_path / 'library.json').write_text(json.dumps(manifest))
    result = optional_compatibility({'cctv-exec': tmp_path}, {'core': {'base_tag': 'v0.8.4'}},
                                    optional={'cctv-exec'})['cctv-exec']
    assert result['status'] == 'NOT PROVEN'
    assert str(tmp_path) not in result['reason']
