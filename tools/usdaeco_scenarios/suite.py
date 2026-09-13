"""Audit a released suite without checking out or executing its submodules."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import configparser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
TAG = re.compile(r"v\d+\.\d+\.\d+\Z")


def command(args, root=ROOT):
    env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    env['GIT_TERMINAL_PROMPT'] = '0'
    try:
        result = subprocess.run(list(map(str, args)), cwd=root, env=env,
                                capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f'{Path(str(args[0])).name}: {type(exc).__name__}') from exc
    if result.returncode:
        # Command output can contain credentials or deployment addresses.
        raise ValueError(f'{Path(str(args[0])).name} command failed ({result.returncode})')
    return result.stdout.strip()


def git(root, *args):
    return command(['git', *args], root)


def read(root, path):
    return json.loads((root / path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative(path):
    require(isinstance(path, str) and bool(path), 'missing relative artifact path')
    parts = PurePosixPath(path)
    require(not parts.is_absolute() and '..' not in parts.parts and str(parts) == path,
            'invalid relative artifact path')
    return path


def remote_tags(origin):
    refs = {}
    for line in git(ROOT, 'ls-remote', '--tags', '--', origin).splitlines():
        revision, ref = line.split('\t')
        refs[ref.removeprefix('refs/tags/')] = revision
    return {tag: refs.get(tag + '^{}', revision) for tag, revision in refs.items()
            if TAG.fullmatch(tag)}


def resolve_module(origin, relative_url):
    require(relative_url.startswith(('../', './')), 'submodule URL must be relative')
    if '://' in origin:
        return urljoin(origin.rstrip('/') + '/', relative_url)
    if ':' in origin:  # Git's scp-style transport.
        import posixpath
        host, path = origin.split(':', 1)
        return host + ':' + posixpath.normpath(path + '/' + relative_url)
    return str((Path(origin) / relative_url).resolve())


def acquire(family, destination):
    """One shallow superproject, even when recursive cloning is configured."""
    entry = next(e for e in family['repos'] if e['name'] == 'usdaeco')
    tag = entry['released']
    require(isinstance(tag, str) and TAG.fullmatch(tag), 'suite needs a released tag')
    base = os.environ.get('AECO_GIT_BASE') or git(ROOT, 'remote', 'get-url', 'origin').rsplit('/', 1)[0]
    origin = base.rstrip('/') + '/usdaeco.git'
    destination = Path(destination).resolve()
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        git(ROOT, 'clone', '--quiet', '--depth', '1', '--branch', tag,
            '--no-recurse-submodules', '--', origin, destination)
    require(git(destination, 'remote', 'get-url', 'origin') == origin, 'suite origin differs')
    require(git(destination, 'rev-parse', '--is-shallow-repository') == 'true',
            'suite gate requires a shallow clone')
    return destination


def audit(root, family):
    """Prove pin provenance and record published measurements, without rerunning them."""
    root = Path(root)
    entries = {e['name']: e for e in family['repos']}
    suite_entry = entries['usdaeco']
    tag = suite_entry['released']
    origin = git(root, 'remote', 'get-url', 'origin')
    revision = git(root, 'rev-parse', 'HEAD')
    require(revision == git(root, 'rev-parse', 'refs/tags/' + tag + '^{commit}'),
            'suite HEAD differs from release tag')
    require(not git(root, 'status', '--porcelain', '--untracked-files=all'),
            'suite checkout has local changes')
    metadata = read(root, 'library.json')
    require(metadata['name'] == 'usdaeco' and metadata['version'] == tag[1:]
            and metadata['kind'] == 'suite', 'suite release metadata differs')
    document = read(root, 'suite.json')
    overrides_path = root / 'suite-overrides.json'
    overrides = read(root, 'suite-overrides.json') if overrides_path.exists() else {}
    members = document['repos']
    by_name = {m['name']: m for m in members}
    by_path = {relative(m['path']): m for m in members}
    expected = {name for name, e in entries.items() if e['released'] and name != 'usdaeco'}
    require(len(members) == len(by_name) == len(by_path) and set(by_name) == expected,
            'suite members differ from released train repositories')
    require(isinstance(overrides, dict) and set(overrides) <= expected, 'unknown suite override')
    require(isinstance(document['train'], str) and bool(document['train']), 'missing suite baseline train')
    require(set(suite_entry['requires']) == expected, 'suite requirements must name the released train')
    for name, item in overrides.items():
        require(item['status'] == 'released' and TAG.fullmatch(item['tag'])
                and item['tag'] == by_name[name]['tag'], name + ': override is not the released suite pin')
    for name, member in by_name.items():
        require(isinstance(member['tag'], str) and TAG.fullmatch(member['tag']), name + ': invalid tag')
        require(member['tag'] == entries[name]['released'] or name in overrides,
                name + ': suite pin differs from train without a released override')

    modules = configparser.ConfigParser(interpolation=None)
    modules.read(root / '.gitmodules')
    urls = {}
    for section in modules.sections():
        path = relative(modules[section]['path'])
        require(path not in urls, 'duplicate submodule path')
        urls[path] = resolve_module(origin, modules[section]['url'])
    links = {}
    for row in git(root, 'ls-tree', '-rz', 'HEAD').split('\0'):
        if not row:
            continue
        header, path = row.split('\t', 1)
        mode, kind, commit = header.split()
        if mode == '160000':
            require(kind == 'commit', 'gitlink has an invalid type')
            links[path] = commit
    require(set(links) == set(urls) == set(by_path), 'gitlinks, submodules and suite paths differ')
    require(all(not (root / path / '.git').exists() for path in links),
            'suite gate must not initialize submodules')
    origins = {'usdaeco': origin} | {m['name']: urls[p] for p, m in by_path.items()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        releases = dict(zip(origins, pool.map(remote_tags, origins.values())))
    require(releases['usdaeco'].get(tag) == revision, 'suite origin tag differs from checkout')
    pins = []
    for name, member in by_name.items():
        commit = releases[name].get(member['tag'])
        require(commit and commit == links[member['path']], name + ': gitlink differs from origin release tag')
        pins.append(dict(repo=name, tag=member['tag'], revision=commit,
                         train=entries[name]['released'], override=name in overrides))

    script = root / 'tools/usdaeco_suite/pins.py'
    method = 'git ls-tree against origin release tags'
    if script.is_file() and '--from-gitlinks' in command([sys.executable, script, '--help'], root):
        command([sys.executable, script, '--check', '--from-gitlinks'], root)
        method = 'pins.py --check --from-gitlinks; gitlinks also checked against origin tags'

    manifest = read(root, 'stage/manifest.json')
    integration = read(root, 'stage/integration.json')
    require(manifest['facility'] == 'demo-datacentre-01', 'unexpected suite facility')
    proofs = manifest['proofs']
    require(isinstance(proofs, dict) and bool(proofs)
            and all(isinstance(v, dict) and bool(v) for v in proofs.values()), 'missing recorded stage proofs')
    require(isinstance(integration, dict) and bool(integration.get('sourceSha256'))
            and isinstance(integration.get('quantitiesRecomputed'), int)
            and integration['quantitiesRecomputed'] > 0, 'missing measured integration evidence')
    files = manifest['files']
    require(isinstance(files, dict) and bool(files) and 'integration.json' in files,
            'missing stage file inventory')
    for path, record in files.items():
        artifact = root / 'stage' / relative(path)
        require(artifact.resolve().is_relative_to((root / 'stage').resolve()), 'stage artifact escapes its directory')
        data = artifact.read_bytes()
        require(len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'],
                'stage inventory differs: ' + path)

    references = []

    def reference(repo, ref, location):
        require(repo in releases and isinstance(ref, str) and TAG.fullmatch(ref)
                and ref in releases[repo], location + ': package/analysis tag is not released')
        references.append(dict(repo=repo, tag=ref, location=location, revision=releases[repo][ref]))

    def owner(record):
        if record.get('repo'):
            return record['repo']
        if record.get('package') == 'suite':
            return 'usdaeco'
        source = record.get('source', '')
        for path, member in by_path.items():
            if source.startswith(path + '/'):
                return member['name']
        if source.startswith(('stage/', 'tools/usdaeco_suite/')):
            return 'usdaeco'
        if record.get('producer', '').startswith('Bonsai '):
            # These twins are authored by the suite's recorded delivery operation.
            return 'usdaeco'
        if record.get('producer', '').startswith('usdaeco-datacentre generator '):
            return 'usdaeco-datacentre'
        raise ValueError('cannot resolve package/analysis tag owner')

    def tagged(value, path):
        if isinstance(value, dict):
            if 'tag' in value:
                reference(owner(value), value['tag'], path)
            for key, child in value.items():
                tagged(child, path + '/' + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                tagged(child, path + '/' + str(index))

    packages, analyses = manifest['packages'], manifest['analyses']
    require(bool(packages) and bool(analyses), 'missing packages or analyses')
    for package in packages:
        require(files.get(f'packages/{package}/{package}.usda', {}).get('tag'), 'package lacks a release tag')
    for analysis, record in analyses.items():
        require(record.get('tag') and isinstance(record.get('run'), bool), analysis + ': missing tag or run state')
        require(owner(record) == 'usdaeco-' + analysis, analysis + ': source repository differs')
    tagged(manifest, 'manifest')
    tagged(integration, 'integration')
    recorded = dict(proofs)
    if 'mute' in recorded:
        mute = dict(recorded['mute'])
        mute['rows'] = len(mute.get('rows', []))
        recorded['mute'] = mute
    return dict(tag=tag, revision=revision, train=family['train'], baselineTrain=document['train'],
                pins=pins, overrides=overrides, gitlinkMethod=method, submodulesInitialized=0,
                files=len(files), packages=len(packages), analyses=analyses, references=references,
                recordedProofs=recorded,
                integration={k: integration[k] for k in ('source', 'sourceSha256', 'quantitiesRecomputed')},
                documents={path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                           for path in ('suite.json', 'stage/manifest.json', 'stage/integration.json')},
                scope='Release provenance and committed evidence; stage checks, renders, rebuilds and suite check.py are not rerun.')


def gate(family, destination):
    started = time.monotonic()
    print('== stage: suite release provenance', flush=True)
    try:
        evidence = audit(acquire(family, destination), family)
        advances = ', '.join(name + ' ' + item['tag'] for name, item in evidence['overrides'].items()) or 'none'
        detail = (f"{evidence['tag']}; {len(evidence['pins'])} gitlinks; {len(evidence['references'])} released stage references; "
                  f"{len(evidence['recordedProofs'])} recorded proofs; overrides: {advances}; stage execution not rerun")
        passed = True
    except (ValueError, OSError, KeyError, TypeError, StopIteration, configparser.Error) as exc:
        evidence = {}
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        passed = False
    evidence['seconds'] = round(time.monotonic() - started, 2)
    return dict(gate='suite', passed=passed, result=detail, evidence=evidence)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'out/suite')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    row = gate(read(ROOT, 'family.json'), args.output / 'source')
    (args.output / 'suite.json').write_text(json.dumps(row, indent=2) + '\n')
    print(('PASS ' if row['passed'] else 'FAIL ') + row['result'])
    print(f"1 checks, {int(not row['passed'])} failed")
    return int(not row['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
