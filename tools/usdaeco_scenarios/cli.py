"""Source-only commands for the release gate and narrated example."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def checkout(family, destination, git_base, kit_base=None):
    """Clone tagged sources without sharing mutable state with existing checkouts."""
    started = time.monotonic()
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    def clone(entry):
        name, tag = entry['name'], entry['released']
        target = destination / name
        if target.exists():
            raise ValueError('Fresh checkout destination already exists: ' + name)
        if name == 'usdaeco-scenarios':
            from packaging.version import Version
            metadata = json.loads((ROOT / 'library.json').read_text())
            if Version(metadata['version']) < Version(tag):
                raise ValueError('Scenarios candidate is older than the released train')
            target.symlink_to(os.path.relpath(ROOT, destination), target_is_directory=True)
            print('PASS current candidate ' + name + ' ' + tag, flush=True)
            return dict(repo=name, ref=tag, candidate='v' + metadata['version'],
                        revision=None, status='current-candidate')
        base = kit_base if name in ('usdSolid', 'usdSolidOcct') and kit_base else git_base
        options = ['--depth', '1'] if entry.get('kind') == 'suite' else []
        subprocess.run(['git', 'clone', '--quiet', '--branch', tag, '--no-recurse-submodules', *options,
                        base.rstrip('/') + '/' + name + '.git', str(target)],
                       check=True, capture_output=True)
        revision = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        tag_revision = subprocess.check_output(
            ['git', '-C', str(target), 'rev-parse', 'refs/tags/' + tag + '^{commit}'], text=True).strip()
        if revision != tag_revision:
            raise ValueError('Tag revision mismatch: ' + name)
        print('PASS checkout ' + name + ' ' + tag, flush=True)
        return dict(repo=name, ref=tag, revision=revision)

    with ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(clone, [e for e in family['repos'] if e['released']]))
    evidence = dict(train=family['train'], sources=sources, seconds=round(time.monotonic() - started, 2))
    (destination / 'checkout.json').write_text(json.dumps(evidence, indent=2) + '\n')
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    clone = commands.add_parser('checkout', help='populate a fresh family root at every release tag')
    clone.add_argument('--output', type=Path, default=ROOT / 'out/family')
    clone.add_argument('--git-base', default=os.environ.get('AECO_GIT_BASE', 'https://github.com/criad-com'))
    clone.add_argument('--kit-base', default=os.environ.get('AECO_KIT_GIT_BASE'))
    demo = commands.add_parser('demo', help='export the five released examples as one walkthrough')
    demo.add_argument('--family-root', type=Path, default=Path(os.environ.get('AECO_FAMILY_ROOT', ROOT / 'out/family')))
    demo.add_argument('--output', type=Path, default=ROOT / 'out/demo')
    args = parser.parse_args(argv)
    family = json.loads((ROOT / 'family.json').read_text())
    print('== stage: ' + args.command, flush=True)
    if args.command == 'checkout':
        checkout(family, args.output, args.git_base, args.kit_base)
    else:
        from usdaeco_scenarios.walkthrough import export
        export(family, args.family_root, args.output)
    return 0
