#!/usr/bin/env python3
"""Verify release tag identities and every sibling schema requirement, offline.

--strict-declarations additionally requires runtime candidate manifests to
name this release matrix exactly. Historical release commits are immutable;
the ordinary gate checks their compatible plugin manifest versions. Optional
sources have a separate declared-range compatibility report, outside the
runtime requirement closure; no native plugin is built or loaded.
"""
import argparse
import json
from pathlib import Path
import subprocess

from packaging.specifiers import SpecifierSet

ROOT = Path(__file__).resolve().parent
ALIASES = {'usdAeco': 'core', 'usdAecoCctv': 'cctv', 'usdAecoSync': 'sync',
           'usdAecoAxis': 'axis', 'usdAecoBuildUp': 'buildup', 'usdAecoWall': 'wall', 'usdAecoPipe': 'pipe'}


def git(root, ref):
    return subprocess.check_output(['git', '-C', str(root), 'rev-parse', ref + '^{commit}'],
                                   text=True, stderr=subprocess.PIPE).strip()


def declarations(data):
    """Walk the different dependency-manifest shapes without assuming depth."""
    if not isinstance(data, dict):
        return
    for key, value in data.items():
        if key in ('fixtures', 'compatibilityFixtures'):
            continue
        if isinstance(value, dict):
            name = ALIASES.get(key, key.removeprefix('usdaeco-'))
            if 'ref' in value and 'revision' in value:
                yield name, value
            yield from declarations(value)


def optional_compatibility(paths, pins, *, optional=()):
    """Compare companion declarations with pinned releases, without loading USD."""
    results = {}
    for name in optional:
        checks = []
        try:
            manifest = json.loads((paths[name] / 'library.json').read_text())
            requires = manifest.get('requires')
            if not isinstance(requires, dict) or not requires:
                raise ValueError('library.json requires must be a nonempty mapping')
            for dependency, requirement in sorted(requires.items()):
                pin = pins.get(ALIASES.get(dependency), {})
                version = (pin.get('base_tag') or '').removeprefix('v')
                detail = f'{dependency} {requirement} against released {version or "MISSING"}'
                try:
                    ok = bool(version) and version in SpecifierSet(requirement)
                except (ValueError, TypeError):
                    ok = False
                    detail += ' (invalid range or release version)'
                checks.append(dict(dependency=dependency, requirement=requirement,
                                   version=version, passed=bool(ok), detail=detail))
            failed = [check['detail'] for check in checks if not check['passed']]
            proven = not failed
            reason = ('Declared ranges satisfied: ' if proven else 'Unsatisfied requirements: ')
            reason += '; '.join(failed or [check['detail'] for check in checks])
        except (OSError, ValueError, KeyError, AttributeError) as exc:
            proven = False
            # Do not copy local file paths from IO errors into portable evidence.
            reason = ('library.json unavailable' if isinstance(exc, (OSError, KeyError))
                      else 'Invalid library.json requirements')
        results[name] = dict(status='PROVEN' if proven else 'NOT PROVEN',
                             reason=reason + '; outside the runtime plugin set; native execution not tested',
                             checks=checks)
    return results


def audit(paths, pins, *, strict=False, optional=()):
    rows = []
    manifests = {}
    versions = {}
    for name, root in paths.items():
        if name in pins:
            versions["usdaeco-" + name] = pins[name]["base_tag"].removeprefix("v")
        files = sorted((root / 'schemas').glob('*/library.json'))
        if (root / 'library.json').exists():
            files.append(root / 'library.json')
        manifests[name] = [json.loads(p.read_text()) for p in files]
        if name not in optional:
            for data in manifests[name]:
                if data.get('name') and data.get('version'):
                    versions[data['name']] = data['version']
    def record(name, ok, detail):
        rows.append(dict(name=name, passed=bool(ok), detail=detail))
    for name, pin in pins.items():
        try:
            actual = git(paths[name], pin['base_tag'])
            record(name + ' tag', actual == pin['revision'], pin['base_tag'])
        except (KeyError, subprocess.CalledProcessError):
            record(name + ' tag', False, 'pinned tag/revision unavailable locally')
    for name, root in paths.items():
        # Optional native exec is pinned for provenance, outside the runtime
        # closure. Declared ranges are reported by optional_compatibility.
        if name in optional:
            continue
        for data in manifests[name]:
            for dependency, requirement in data.get('requires', {}).items():
                # A repository release and its schema version have independent
                # clocks: requires is evaluated by the plugin registry.
                version = versions.get(dependency, '')
                ok = bool(version) and version in SpecifierSet(requirement)
                record(name + ' requires ' + dependency, ok,
                       requirement + ' against schema ' + (version or 'MISSING'))
        if strict and name in ('cctv', 'sync', 'datacentre', 'cctv-exec'):
            manifest = root / 'dependencies.json'
            if not manifest.exists():
                record(name + ' dependency manifest', False, 'missing')
                continue
            for target, declared in declarations(json.loads(manifest.read_text())):
                if target not in pins:
                    continue
                expected = pins[target]
                record(name + ' pins ' + target,
                       declared == {'ref': expected['base_tag'], 'revision': expected['revision']},
                       declared['ref'])
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family-root', type=Path, default=ROOT.parent)
    parser.add_argument('--strict-declarations', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT / 'dependencies.json').read_text())
    optional = data.get('optional_repositories', {})
    from family import release_pins
    pins = release_pins()
    paths = {n: args.family_root / ('usdaeco-' + n) for n in pins}
    rows = audit(paths, pins, strict=args.strict_declarations, optional=optional)
    for row in rows:
        print(('PASS' if row['passed'] else 'FAIL') + ' ' + row['name'] + ': ' + row['detail'])
    failed = sum(not row['passed'] for row in rows)
    compatibility = optional_compatibility(paths, pins, optional=optional)
    for name, result in compatibility.items():
        print(f"{result['status']} optional {name}: {result['reason']}")
    if args.report:
        args.report.write_text(json.dumps({'checks': rows, 'failed': failed,
                                          'optionalCompatibility': compatibility}, indent=2) + '\n')
    print(f'{len(rows)} checks, {failed} failed')
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
