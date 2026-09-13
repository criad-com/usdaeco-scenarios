"""Public naming exceptions and current-candidate source cards stay narrow."""
from sanitization import scan


def test_public_org_exception_does_not_hide_adjacent_private_terms(tmp_path):
    path = tmp_path / 'links.md'
    path.write_text('github:criad-com/usdaeco-core?ref=v0.9.5')
    assert scan([path])['passed']
    path.write_text(path.read_text() + ' ' + bytes.fromhex('4372696164').decode())
    assert not scan([path])['passed']
    path.write_text('criad-com' + '-extra')
    assert not scan([path])['passed']


def test_candidate_index_never_claims_a_published_commit():
    import json
    from family import ROOT
    snapshot = json.loads((ROOT / 'docs/family/index.json').read_text())
    card = next(c for c in snapshot['cards'] if c['name'] == 'usdaeco-scenarios')
    assert card['candidate'] is True and card['commit'] is None
    assert 'does not establish tag publication' in card['status']


def test_checkout_uses_current_candidate_without_requesting_an_unpublished_tag(tmp_path, monkeypatch):
    import json
    from family import ROOT
    from usdaeco_scenarios.cli import checkout
    def forbid(*args, **kwargs):
        raise AssertionError('Candidate checkout must not fetch a release tag')
    monkeypatch.setattr('usdaeco_scenarios.cli.subprocess.run', forbid)
    inventory = json.loads((ROOT / 'family.json').read_text())
    family = dict(inventory, repos=[e for e in inventory['repos'] if e['name'] == 'usdaeco-scenarios'])
    result = checkout(family, tmp_path, 'https://github.com/criad-com')
    assert (tmp_path / 'usdaeco-scenarios').resolve() == ROOT
    assert result['sources'][0]['revision'] is None
    assert result['sources'][0]['status'] == 'current-candidate'
    assert result['sources'][0]['ref'] == family['repos'][0]['released']
    assert result['sources'][0]['candidate'] == 'v' + json.loads((ROOT / 'library.json').read_text())['version']
