"""Unavailable optional sources skip execution; available sources retain pin checks."""
import json

import pytest

import family
from usdaeco_scenarios import suite


@pytest.fixture
def optional_source(tmp_path, monkeypatch):
    name, pin = next((n, p) for n, p in family.dependency_pins().items() if p.get('optional'))
    root = tmp_path / 'candidate'
    root.mkdir()
    source = tmp_path / pin['repo']
    monkeypatch.setattr(family, 'ROOT', root)
    monkeypatch.setattr(family, 'dependency_pins', lambda: {name: pin})
    monkeypatch.setenv('AECO_' + name.upper() + '_SOURCE', str(source))
    return name, pin, source, root


def test_missing_optional_source_is_not_fetched_or_resolved(optional_source, tmp_path, monkeypatch):
    name, _, _, _ = optional_source

    def forbid(*args, **kwargs):
        raise AssertionError('Unavailable optional sources must not invoke Git')

    monkeypatch.setattr(family, 'run', forbid)
    assert name in family.repos(include_optional=True)
    assert name not in family.repos()
    assert family.release_pins() == {}
    report = family.isolate_sources(tmp_path / 'gate')
    assert report[name] == dict(status='NOT RUN', reason=family.OPTIONAL_SOURCE_REASON)


def test_available_optional_source_is_isolated_and_dirty_source_fails(optional_source, tmp_path):
    name, pin, source, _ = optional_source
    suite.git(tmp_path, 'init', '--quiet', source)
    suite.git(source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
              'commit', '--quiet', '--allow-empty', '-m', 'Fixture release')
    suite.git(source, 'tag', pin['ref'])
    report = family.isolate_sources(tmp_path / 'gate')
    assert report[name]['revision'] == family.release_pins()[name]['revision']
    assert not report[name]['modified']
    (family.repos()[name] / 'changed.txt').write_text('changed\n')
    with pytest.raises(RuntimeError, match='Source pin audit failed'):
        family.audit_sources()


def test_checkout_and_suite_report_missing_optional_source(optional_source, tmp_path, monkeypatch):
    from usdaeco_scenarios.cli import checkout
    _, pin, _, _ = optional_source
    inventory = dict(train='example', repos=[dict(name=pin['repo'], released=pin['ref'])])

    def forbid(*args, **kwargs):
        raise AssertionError('Unavailable optional sources must not invoke Git')

    monkeypatch.setattr('usdaeco_scenarios.cli.subprocess.run', forbid)
    monkeypatch.setattr(suite, 'acquire', forbid)
    sources = checkout(inventory, tmp_path / 'checkout', 'https://example.invalid')['sources']
    assert sources[0]['status'] == 'NOT RUN' and sources[0]['reason']
    result = suite.gate(inventory, tmp_path / 'suite')
    assert result['status'] == 'NOT RUN' and not result['passed']
    assert result['evidence']['unavailable'] == [pin['repo']]


def test_index_checks_available_cards_when_optional_source_is_missing(tmp_path, monkeypatch):
    from usdaeco_scenarios.index import fresh_check, generate
    entries = json.loads((family.ROOT / 'family.json').read_text())['repos']
    optional = next(e for e in entries
                    if e['name'] in family.optional_repositories())
    candidate = next(e for e in entries
                     if e['name'] == 'usdaeco-scenarios')
    seed = next(e for e in entries if e['kind'] == 'meta')
    manifest = tmp_path / 'family.json'
    manifest.write_text(json.dumps(dict(train='example', repos=[candidate, optional, seed])))

    def forbid(*args, **kwargs):
        raise AssertionError('Unavailable optional index sources must not invoke Git')

    monkeypatch.setattr('publish.git', forbid)
    output = tmp_path / 'README.md'
    result = generate(manifest, tmp_path / 'sources', output)
    assert result.status == 'NOT RUN' and family.OPTIONAL_SOURCE_REASON in result.detail
    snapshot_path = output.with_name('index.json')
    snapshot = json.loads(snapshot_path.read_text())
    snapshot['cards'][0]['library']['version'] = '0.0.0'
    snapshot_path.write_text(json.dumps(snapshot))
    assert fresh_check(output, family=manifest, repos=tmp_path / 'sources').status == 'FAIL'
