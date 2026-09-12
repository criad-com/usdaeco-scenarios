"""Index-only kits are read from released tags even without suite checkouts."""
import json

import pytest

from family import ROOT
from publish import git
from usdaeco_scenarios.index import collect, released_sources


@pytest.fixture
def hub_release(tmp_path, monkeypatch):
    inventory = json.loads((ROOT / 'family.json').read_text())
    entries = [e for e in inventory['repos'] if e['name'] in
               ('aeco-toolchain', 'usdaeco-scenarios')]
    hub = next(e for e in entries if e['name'] == 'aeco-toolchain')
    mirror = tmp_path / 'mirror'
    release = mirror / (hub['name'] + '.git')
    release.mkdir(parents=True)
    git('init', '--quiet', release)
    (release / 'README.md').write_text('# Build kit — Tagged build tools\n')
    git('add', '.', cwd=release)
    git('commit', '--quiet', '-m', 'Seed release source', cwd=release)
    git('tag', hub['released'], cwd=release)
    revision = git('rev-parse', 'HEAD', cwd=release).decode().strip()
    (release / 'README.md').write_text('# Build kit — Unreleased checkout text\n')
    manifest = tmp_path / 'family.json'
    manifest.write_text(json.dumps(dict(inventory, repos=entries)))
    sources = tmp_path / 'sources'
    sources.mkdir()
    monkeypatch.setenv('AECO_GIT_BASE', str(mirror))
    return manifest, sources, release, revision


@pytest.mark.parametrize('present', [False, True])
def test_hub_card_uses_tag_without_requiring_a_suite(hub_release, present):
    manifest, sources, release, revision = hub_release
    checkout = sources / 'aeco-toolchain'
    if present:
        checkout.symlink_to(release, target_is_directory=True)
    snapshot = collect(manifest, sources)
    card = next(c for c in snapshot['cards'] if c['name'] == 'aeco-toolchain')
    assert card == dict(name='aeco-toolchain', available=False, commit=revision,
                        purpose='Tagged build tools', reason='Tagged library manifest missing')
    assert checkout.exists() == present
    assert 'Unreleased checkout text' in (release / 'README.md').read_text()


def test_missing_hub_tag_fails_instead_of_reusing_a_card(hub_release):
    manifest, sources, release, _ = hub_release
    hub = next(e for e in json.loads(manifest.read_text())['repos']
               if e['name'] == 'aeco-toolchain')
    git('tag', '-d', hub['released'], cwd=release)
    with pytest.raises(ValueError, match='git clone failed'):
        collect(manifest, sources)


def test_hub_tag_is_available_for_drift_then_removed(hub_release):
    from usdaeco_scenarios.drift import revision
    manifest, sources, _, expected = hub_release
    entries = json.loads(manifest.read_text())['repos']
    hub = next(e for e in entries if e['name'] == 'aeco-toolchain')
    with released_sources(entries, sources) as prepared:
        assert revision(prepared / hub['name'], hub['released']) == expected
    assert not prepared.exists()
    assert not (sources / hub['name']).exists()
