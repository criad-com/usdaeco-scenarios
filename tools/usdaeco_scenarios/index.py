"""Run the shared index generator with the gate's generic-kit inventory adapter."""
import json
import hashlib
from pathlib import Path
import tempfile


def collect(family, sources):
    """Read released cards, with an explicit card for the current candidate."""
    import family_readme
    from family_manifest import validate_family
    family_readme.validate_family = validate_family
    data = json.loads(Path(family).read_text())
    candidate = next(e for e in data['repos'] if e['name'] == 'usdaeco-scenarios')
    root = Path(__file__).resolve().parents[2]
    metadata_text = (root / 'library.json').read_text()
    metadata = json.loads(metadata_text)
    if candidate['released'] != 'v' + metadata['version']:
        raise ValueError('Scenarios candidate version differs from train')
    projected = dict(data, repos=[e for e in data['repos'] if e != candidate])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'family.json'
        path.write_text(json.dumps(projected))
        snapshot = family_readme.collect(path, sources)
    cards = {c['name']: c for c in snapshot['cards']}
    cards[candidate['name']] = dict(
        name=candidate['name'], available=True, commit=None, candidate=True,
        library=metadata, purpose='Pinned family acceptance', licence=metadata['licence'],
        example=None, status='Current release candidate; its structure and regressions run without recursion. '
        'Measured full and fast results are recorded in acceptance; this card does not establish tag publication.',
        source_sha256={'library.json': hashlib.sha256(metadata_text.encode()).hexdigest()})
    return dict(format=1, family=data, cards=[cards[e['name']] for e in data['repos']])


def render(snapshot):
    import family_readme
    text = family_readme.render(snapshot)
    board = next(e for e in snapshot['family']['repos'] if e['name'] == 'usdaeco-board')
    return text.replace('/usdaeco-board/blob/v0.1.2/', '/usdaeco-board/blob/' + board['released'] + '/')


def fresh_check(output, *, family, repos):
    from usdaeco_check.report import Result
    try:
        output = Path(output)
        snapshot = json.loads(output.with_name('index.json').read_text())
        if collect(family, repos) != snapshot or output.read_text() != render(snapshot):
            raise ValueError('Source cards or family README differ; regenerate the index')
        return Result('family README fresh', True,
                      f"{len(snapshot['cards'])} rows; tagged sources and explicit current candidate")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return Result('family README fresh', False, str(exc))


def generate(family, sources, output):
    snapshot = collect(family, sources)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_name('index.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    output.write_text(render(snapshot))
    return fresh_check(output, family=family, repos=sources)


if __name__ == '__main__':
    import argparse
    import os
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', default='family.json')
    parser.add_argument('--repos', default=os.environ.get('AECO_FAMILY_ROOT', 'out/family'))
    parser.add_argument('--output', default='docs/family/README.md')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root), str(Path(os.environ.get('TOOLCHAIN_DIR', Path(args.repos) / 'usdaeco-toolchain')) / 'tools')]
    result = generate(args.family, args.repos, args.output)
    print(('PASS' if result else 'FAIL') + ' ' + result.detail)
    raise SystemExit(0 if result else 1)
