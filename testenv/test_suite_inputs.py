"""Released fixture declarations cannot replace direct runtime dependencies."""
import json

from usdaeco_scenarios.suite_inputs import declarations, harness_source, example_environment


def test_explicit_flake_and_byte_qualified_fixtures_become_executable_inputs(tmp_path):
    direct = {'core': dict(repo='usdaeco-core', ref='v0.9.3')}
    fixture = dict(repo='usdaeco-core', ref='v0.8.4', runtime_paths=['tools'], runtime_sha256='a' * 64)
    legacy = dict(repo='usdaeco-core', ref='v0.8.4', flakeInput=True,
                  reason='Legacy template compatibility tests')
    data = dict(repos=direct, fixtures={
        'generator': fixture,
        'legacy': legacy,
        'disabled': dict(legacy, flakeInput=False),
        'rejection': dict(repo='usdaeco-core', ref='v0.6.0', path='test.py'),
        'recorded': dict(path='expected.json', reason='Historical evidence')})
    (tmp_path / 'dependencies.json').write_text(json.dumps(data))
    pins, fixtures = declarations(tmp_path)
    assert pins == direct
    assert fixtures == {'generator': fixture, 'legacy': legacy}


def test_declared_toolchain_is_not_replaced_by_train_harness(tmp_path):
    pin = dict(repo='usdaeco-toolchain', ref='v0.3.5',
               runtime_paths=['tools', 'library.json'], runtime_sha256='a' * 64)
    declared, train = tmp_path / 'declared', tmp_path / 'train'
    source = tmp_path / 'dependencies.json'
    source.write_text(json.dumps(dict(repos={'toolchain': pin})))
    assert harness_source(tmp_path, {'toolchain': declared}, train) == declared
    pin.pop('runtime_sha256')
    pin.pop('runtime_paths')
    source.write_text(json.dumps(dict(repos={'toolchain': pin})))
    assert harness_source(tmp_path, {'toolchain': declared}, train) == declared
    source.write_text(json.dumps(dict(repos={})))
    assert harness_source(tmp_path, {'toolchain': declared}, train) == train


def test_section_publication_keeps_its_declared_facility(tmp_path):
    path = tmp_path / 'dependencies.json'
    env = {'AECO_DATACENTRE_ROOT': 'selected-release', 'TOOLCHAIN_DIR': 'selected-kit'}
    path.write_text(json.dumps(dict(repos={'datacentre': dict(repo='usdaeco-datacentre', ref='v0.4.8')})))
    assert example_environment(tmp_path, env) == env
    path.write_text(json.dumps(dict(repos={})))
    assert example_environment(tmp_path, env) == {'TOOLCHAIN_DIR': 'selected-kit'}
    assert env['AECO_DATACENTRE_ROOT'] == 'selected-release'
