"""Exercise release provenance using local Git origins and seeded bad releases."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from usdaeco_scenarios import suite


def write(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value) + '\n')


def seal(root, tag='v0.3.0'):
    suite.git(root, 'add', '.')
    suite.git(root, 'commit', '--quiet', '--allow-empty', '-m', 'Record fixture release')
    suite.git(root, 'tag', '--force', '--annotate', tag, '-m', 'Fixture release')


def initialize(root):
    root.mkdir(parents=True)
    suite.git(root, 'init', '--quiet')
    suite.git(root, 'config', 'user.name', 'Release Fixture')
    suite.git(root, 'config', 'user.email', 'fixture@example.invalid')


@pytest.fixture
def release(tmp_path):
    mirror = tmp_path / 'mirror'
    root = mirror / 'usdaeco.git'
    initialize(root)
    suite.git(root, 'remote', 'add', 'origin', root.as_uri())
    entries, members, modules = [], [], []
    for name, path in [('usdaeco-datacentre', 'data/usdaeco-datacentre'),
                       ('usdaeco-wall', 'kind/usdaeco-wall')]:
        source = mirror / (name + '.git')
        initialize(source)
        write(source, 'library.json', dict(version='0.1.0'))
        seal(source, 'v0.1.0')
        entries.append(dict(name=name, kind='library', library=None, released='v0.1.0',
                            tag='v0.1.0', floor='v0.1.0', requires={}, example=None, enclave=None))
        members.append(dict(name=name, path=path, tag='v0.1.0'))
        modules.append(f'[submodule "{path}"]\npath = {path}\nurl = ../{name}.git\n')
        commit = suite.git(source, 'rev-parse', 'HEAD')
        (root / path).mkdir(parents=True)
        suite.git(root, 'update-index', '--add', '--cacheinfo', '160000,' + commit + ',' + path)
    (root / '.gitmodules').write_text('\n'.join(modules))
    write(root, 'library.json', dict(name='usdaeco', kind='suite', version='0.3.0'))
    write(root, 'suite.json', dict(train='aeco-0.8.1', repos=members))
    write(root, 'suite-overrides.json', {})
    integration = dict(source='tools/usdaeco_suite/refresh.py', sourceSha256='a' * 64, quantitiesRecomputed=2)
    write(root, 'stage/integration.json', integration)
    path = 'packages/arch/arch.usda'
    (root / 'stage/packages/arch').mkdir(parents=True)
    (root / 'stage' / path).write_text('#usda 1.0\n')
    files = {}
    for filename in ['integration.json', path]:
        data = (root / 'stage' / filename).read_bytes()
        files[filename] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    files[path].update(source='data/usdaeco-datacentre/dist/full/arch.ifc', tag='v0.1.0')
    write(root, 'stage/manifest.json', dict(facility='demo-datacentre-01',
          proofs={'vanilla': {'compositionErrors': 0}, 'validators': {'zeroErrors': False, 'rawErrorCount': 2}},
          files=files, packages={'arch': {'elements': 1}}, analyses={'wall': dict(
              source='kind/usdaeco-wall/examples/datacentre/run.py', tag='v0.1.0', run=False)}))
    seal(root)
    entries.append(dict(name='usdaeco', kind='suite', library=None, tag='v0.3.0', released='v0.3.0',
                        floor='v0.3.0', requires={e['name']: '>=0.1' for e in entries},
                        example=None, enclave=None))
    return root, dict(train='aeco-0.9.0', repos=entries)


def test_annotated_tags_and_recorded_failures_are_preserved(release):
    root, family = release
    result = suite.audit(root, family)
    assert len(result['pins']) == 2 and len(result['references']) == 2
    assert result['submodulesInitialized'] == 0
    assert result['baselineTrain'] == 'aeco-0.8.1'
    assert result['recordedProofs']['validators']['zeroErrors'] is False
    assert result['analyses']['wall']['run'] is False
    assert result['gitlinkMethod'] == 'git ls-tree against origin release tags'


def test_acquisition_is_shallow_and_never_initializes_submodules(release, tmp_path, monkeypatch):
    root, family = release
    monkeypatch.setenv('AECO_GIT_BASE', root.parent.as_uri())
    clone = suite.acquire(family, tmp_path / 'clone')
    assert suite.git(clone, 'rev-parse', '--is-shallow-repository') == 'true'
    assert suite.audit(clone, family)['submodulesInitialized'] == 0
    assert not (clone / '.git/modules').exists()


def test_checkout_command_also_keeps_suite_shallow(release, tmp_path):
    from usdaeco_scenarios.cli import checkout
    root, family = release
    selected = dict(family, repos=[family['repos'][-1]])
    destination = tmp_path / 'checkout'
    checkout(selected, destination, root.parent.as_uri())
    clone = destination / 'usdaeco'
    assert suite.git(clone, 'rev-parse', '--is-shallow-repository') == 'true'
    assert suite.audit(clone, family)['submodulesInitialized'] == 0


def test_released_override_is_reported(release):
    root, family = release
    family['repos'][0]['released'] = 'v0.0.9'
    write(root, 'suite-overrides.json', {'usdaeco-datacentre': dict(tag='v0.1.0', status='released')})
    seal(root)
    result = suite.audit(root, family)
    assert result['pins'][0]['override']
    assert result['overrides']['usdaeco-datacentre']['status'] == 'released'


@pytest.mark.parametrize('override', [{}, {'tag': 'v0.1.0', 'status': 'awaiting-tag'},
                                     {'tag': 'v0.2.0', 'status': 'released'}])
def test_unapproved_or_unreleased_override_fails(release, override):
    root, family = release
    family['repos'][0]['released'] = 'v0.0.9'
    write(root, 'suite-overrides.json', {'usdaeco-datacentre': override} if override else {})
    seal(root)
    with pytest.raises(ValueError, match='override'):
        suite.audit(root, family)


@pytest.mark.parametrize('defect', ['extra', 'missing', 'duplicate', 'path'])
def test_suite_inventory_mismatch_fails(release, defect):
    root, family = release
    document = suite.read(root, 'suite.json')
    if defect == 'missing':
        document['repos'].pop()
    elif defect == 'extra':
        document['repos'].append(dict(name='usdaeco-extra', path='kind/usdaeco-extra', tag='v0.1.0'))
    elif defect == 'duplicate':
        document['repos'].append(copy.deepcopy(document['repos'][0]))
    else:
        document['repos'][0]['path'] = '../outside'
    write(root, 'suite.json', document)
    seal(root)
    with pytest.raises(ValueError, match='members|path'):
        suite.audit(root, family)


@pytest.mark.parametrize('artifact', ['stage/manifest.json', 'stage/integration.json'])
def test_missing_evidence_fails(release, artifact):
    root, family = release
    (root / artifact).unlink()
    seal(root)
    with pytest.raises(OSError):
        suite.audit(root, family)


@pytest.mark.parametrize('defect', ['proofs', 'integration', 'analysis-tag', 'package-tag', 'inventory', 'owner'])
def test_invalid_stage_evidence_fails(release, defect):
    root, family = release
    document = suite.read(root, 'stage/manifest.json')
    if defect == 'proofs':
        document['proofs'] = {}
    elif defect == 'integration':
        write(root, 'stage/integration.json', {})
    elif defect == 'analysis-tag':
        document['analyses']['wall']['tag'] = 'v9.9.9'
    elif defect == 'package-tag':
        del document['files']['packages/arch/arch.usda']['tag']
    elif defect == 'owner':
        document['analyses']['wall']['source'] = 'unknown/run.py'
    else:
        (root / 'stage/packages/arch/arch.usda').write_text('# changed\n')
    write(root, 'stage/manifest.json', document)
    seal(root)
    with pytest.raises(ValueError):
        suite.audit(root, family)


@pytest.mark.parametrize('defect', ['wrong-commit', 'missing-tag', 'extra-gitlink', 'missing-module'])
def test_gitlinks_require_actual_origin_tags(release, defect):
    root, family = release
    if defect == 'wrong-commit':
        commit = suite.git(root, 'rev-parse', 'HEAD')
        suite.git(root, 'update-index', '--cacheinfo', '160000,' + commit + ',kind/usdaeco-wall')
    elif defect == 'missing-tag':
        suite.git(root.parent / 'usdaeco-wall.git', 'tag', '-d', 'v0.1.0')
    elif defect == 'extra-gitlink':
        commit = suite.git(root, 'rev-parse', 'HEAD')
        (root / 'kind/usdaeco-extra').mkdir()
        suite.git(root, 'update-index', '--add', '--cacheinfo', '160000,' + commit + ',kind/usdaeco-extra')
    else:
        (root / '.gitmodules').write_text('')
    seal(root)
    with pytest.raises(ValueError, match='gitlink'):
        suite.audit(root, family)


def test_dirty_checkout_cannot_supply_published_proofs(release):
    root, family = release
    write(root, 'stage/integration.json', {})
    with pytest.raises(ValueError, match='local changes'):
        suite.audit(root, family)


def test_pins_command_runs_when_gitlink_option_is_supported(release):
    root, family = release
    script = root / 'tools/usdaeco_suite/pins.py'
    script.parent.mkdir(parents=True)
    script.write_text("import sys\nif '--help' in sys.argv:\n    print('--from-gitlinks')\n"
                      "else:\n    assert sys.argv[1:] == ['--check', '--from-gitlinks']\n")
    seal(root)
    assert suite.audit(root, family)['gitlinkMethod'].startswith('pins.py --check --from-gitlinks')
    script.write_text(script.read_text().replace("assert sys.argv[1:]", "raise SystemExit(1)\n    assert sys.argv[1:]"))
    seal(root)
    with pytest.raises(ValueError, match='command failed'):
        suite.audit(root, family)


def test_suite_adapter_validates_train_requirements(release):
    from family_manifest import validate_family
    _, family = release
    assert validate_family(family)
    family['repos'][-1]['requires']['usdaeco-wall'] = '>=0.2'
    assert not validate_family(family)
