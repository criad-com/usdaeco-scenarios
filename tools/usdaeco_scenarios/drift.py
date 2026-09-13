"""Direct pins must lie inside the train; historical fixtures stay separate."""
import json
import re
from pathlib import Path
import subprocess

from packaging.specifiers import SpecifierSet
from packaging.version import Version

HEADINGS = ['1 The problem', '2 The data as it arrives', '3 The model in USD',
            '4 Workflow', '5 Validation', '6 The example on the demo data centre',
            '7 Trade-offs and alternatives', '8 Out of scope and open questions', '9 Status']
UPSTREAM = {'OpenUSD'}


def revision(root, tag):
    if root is None or not tag:
        return None
    result = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', tag + '^{commit}'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def audit(family, sources, *, tag_sources=None):
    """Check inclusive floor/released intervals and declared requirement ranges."""
    entries = {e['name']: e for e in family['repos']}
    libraries = {e['library']: e for e in family['repos'] if e['library']}
    pins, ranges, stories, external, fixtures = [], [], [], [], []
    revisions = {}
    tag_sources = sources | (tag_sources or {})

    def row(rows, repo, check, passed, detail):
        rows.append(dict(repo=repo, check=check, passed=bool(passed), detail=detail))

    for name, root in sorted(sources.items()):
        root = Path(root)
        try:
            metadata = json.loads((root / 'library.json').read_text())
            dependencies = json.loads((root / 'dependencies.json').read_text())
            declared = (dependencies['repos'] | dependencies.get('nativeKits', {})
                        | dependencies.get('optionalRepos', {}))
            historical = dependencies.get('fixtures', {})
            if not isinstance(historical, dict):
                raise ValueError('fixtures must be a mapping')
        except (OSError, ValueError, KeyError, TypeError):
            row(pins, name, 'manifest', False, 'Missing or invalid library/dependency manifest')
            continue
        for key, fixture in historical.items():
            fixtures.append(dict(repo=name, fixture=key, declaration=fixture))
        for key, pin in declared.items():
            repo, ref = pin.get('repo'), pin.get('ref')
            if repo in UPSTREAM:
                external.append(dict(repo=name, dependency=repo, ref=ref,
                                     reason='External build input, outside the semantic release train'))
                continue
            entry = entries.get(repo)
            floor = entry.get('floor') if entry else None
            released = entry.get('released') if entry else None
            sha_ref = isinstance(ref, str) and re.fullmatch(r'[0-9a-f]{40}', ref)
            tag = 'v' + str(pin.get('version', '')).removeprefix('v') if sha_ref else ref
            reasons = []
            version = None
            try:
                if not all(isinstance(v, str) and re.fullmatch(r'v\d+\.\d+\.\d+', v)
                           for v in (floor, released, tag)):
                    raise ValueError('Missing or invalid train bounds or version tag')
                version = Version(tag[1:])
                if Version(floor[1:]) > Version(released[1:]):
                    reasons.append('inverted train interval')
                elif not Version(floor[1:]) <= version <= Version(released[1:]):
                    reasons.append('outside train interval')
                if 'version' in pin and Version(str(pin['version']).removeprefix('v')) != version:
                    reasons.append('version differs from ref')
            except (ValueError, TypeError) as exc:
                reasons.append(str(exc))
            if pin.get('revision') or sha_ref:
                cache_key = (repo, tag)
                if cache_key not in revisions:
                    revisions[cache_key] = revision(tag_sources.get(repo, root.parent / repo), tag)
                commit = revisions[cache_key]
                recorded = {pin.get('revision'), pin.get('publicRevision')} - {None}
                if commit is None or (sha_ref and ref != commit) or (recorded and commit not in recorded):
                    reasons.append('declared ref revision mismatch or unavailable')
            requirement = metadata.get('requires', {}).get(repo)
            if entry and entry.get('library'):
                requirement = metadata.get('requires', {}).get(entry['library'], requirement)
            if requirement is not None:
                try:
                    if version is None or version not in SpecifierSet(requirement):
                        reasons.append('outside declared requirement ' + requirement)
                except (ValueError, TypeError):
                    reasons.append('invalid declared requirement')
            row(pins, name, 'pin ' + key, not reasons,
                f'{repo} declared {ref}; train [{floor or "MISSING"}, {released or "MISSING"}]' +
                ('; ' + '; '.join(reasons) if reasons else '; inside train'))
            pins[-1].update(dependency=repo, ref=ref, floor=floor, released=released,
                            reasons=reasons, version=str(version) if version is not None else None)
        for library, requirement in metadata.get('requires', {}).items():
            entry = libraries.get(library) or entries.get(library)
            matches = [p for p in pins if p['repo'] == name and entry
                       and p.get('dependency') == entry['name']]
            try:
                spec = SpecifierSet(requirement)
                train_version = entry['released'].removeprefix('v') if entry and entry['released'] else ''
                versions = [p['version'] for p in matches]
                ok = bool(versions) and bool(train_version) and train_version in spec and all(v in spec for v in versions)
            except (ValueError, TypeError):
                ok, versions, train_version = False, [], ''
            row(ranges, name, 'requires ' + library, ok,
                f'{requirement}; declared versions {versions}; train {train_version or "MISSING"}')
        entry = entries.get(name, {})
        if entry.get('kind') in ('usecase', 'integration'):
            document = root / 'docs/usecase.md'
            headings = re.findall(r'^## (.+)$', document.read_text(), re.M) if document.is_file() else []
            row(stories, name, 'nine sections', headings == HEADINGS,
                f'{len(headings)}/9 sections in the required order')
            example = root / 'examples' / ('roundtrip' if entry['kind'] == 'integration' else 'datacentre')
            required = ['example.usdc', 'README.md', 'vanilla.png', 'layers']
            missing = [p for p in required if not (example / 'result' / p).exists()]
            row(stories, name, 'published result', not missing,
                'Missing: ' + ', '.join(missing) if missing else 'Crate, own layers, README and vanilla render present')
    return dict(pins=pins, ranges=ranges, stories=stories, external=external, fixtures=fixtures)
