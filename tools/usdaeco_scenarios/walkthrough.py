"""A portable walkthrough assembled from the five released example artifacts."""
import hashlib
import json
from pathlib import Path
import shutil

ORDER = ('cctv', 'clash', 'plan', 'compliance', 'repeat')


def summary(name, findings):
    by_name = {r.get('name', r.get('kind')): r for r in findings}
    if name == 'cctv':
        derived = by_name['Derive']
        targets = by_name['CriticalDoors']['results'].values()
        return (f"Start with visibility: {derived['sensors']} sensors generate {derived['sectors']} sectors. "
                f"CriticalDoors covers {sum(r['fixedCoverage'] for r in targets)}/{len(by_name['CriticalDoors']['results'])} fixed targets; "
                f"Privacy reports {len(by_name['Privacy']['exclusionsCovered'])} covered exclusions.")
    if name == 'clash':
        cases = [r for r in findings if r.get('name') == 'RouteComparison']
        text = '; '.join(f"{r['case']}: mesh {r['mesh']['verdict']}, exact {r['exact']['verdict']}" for r in cases)
        return f"Then inspect physical interference across {len(cases)} measured pairs: {text}. Exact geometry resolves the mesh uncertainty."
    if name == 'plan':
        problems = [r for r in findings if r.get('programme') == 'A' and 'severity' in r]
        b = [r for r in findings if r.get('programme') == 'B' and 'severity' in r]
        text = ', '.join(f"{r['name']} ({r['occurrences']})" for r in problems)
        return f"Sequence the pod delivery and ceiling closure. Programme A reports {text}. Programme B reports {len(b)} such findings after the sequence changes; work dates remain programme data."
    if name == 'compliance':
        counts = by_name['summary']
        return (f"Check the iris readers against illustrative requirements: {counts['pass']} readers pass and {counts['fail']} fails "
                f"across {counts['readers']} readers, producing {counts['clause_failures']} clause failures. These are demonstration clauses, not a regulatory certification.")
    if name == 'repeat':
        drift, delta = by_name['FloorDrift'], by_name['ScheduleDelta']
        return (f"Finally compare repeated office floors: {drift['all_changes']['changed']} changed wall and {drift['extra_doors']} extra door. "
                f"The released example reports a partition-length delta of {delta['partition_length_m']:g} m and a door delta of {delta['doors']:g}. "
                "Its pinned floor source is recorded below; newer data variants are checked separately.")
    raise ValueError('Unknown walkthrough step: ' + name)


def collect(family, sources):
    entries = {e['name']: e for e in family['repos']}
    steps = []
    for name in ORDER:
        repo = 'usdaeco-' + name
        entry = entries[repo]
        example = Path(sources) / repo / 'examples/datacentre'
        manifest = json.loads((example / 'manifest.json').read_text())
        findings_path = example / 'expected/findings.json'
        findings = json.loads(findings_path.read_text())
        render = next((r for r in manifest['renders'] if Path(r['path']).name == 'overview.png'), manifest['renders'][0])
        image = example / render['path']
        if hashlib.sha256(image.read_bytes()).hexdigest() != render['sha256']:
            raise ValueError(repo + ': render hash differs from the release manifest')
        if hashlib.sha256(findings_path.read_bytes()).hexdigest() != manifest['findings_sha256']:
            raise ValueError(repo + ': findings hash differs from the release manifest')
        url = f"https://github.com/criad-com/{repo}/tree/{entry['released']}/examples/datacentre"
        steps.append(dict(name=name, repo=repo, tag=entry['released'], source=manifest['datacentre'],
                          narrative=summary(name, findings), findings=findings,
                          findings_sha256=manifest['findings_sha256'], render=render,
                          example_url=url, render_url=url.replace('/tree/', '/raw/') + '/' + render['path']))
    return dict(train=family['train'], facility='demo-datacentre-01', steps=steps)


def markdown(data, *, local=False):
    lines = [f"Walk through `{data['facility']}` in train `{data['train']}`. Each step uses its repository's "
             "released findings and one recorded render. Public links name intended mirror locations; network availability is not checked.", '']
    for i, step in enumerate(data['steps'], 1):
        findings = (step['name'] + '/findings.json' if local else
                    step['example_url'] + '/expected/findings.json')
        render = (step['name'] + '/render' + Path(step['render']['path']).suffix if local else step['render_url'])
        lines += [f"**{i}. {step['name'].upper()}** — {step['narrative']}", '',
                  f"[Example and output]({step['example_url']}) · [Findings]({findings})",
                  f"Data source: `{step['source']['ref']}` / `{step['source']['variant']}`.", '',
                  f"![{step['name']} example]({render})", '']
    return '\n'.join(lines)


def export(family, sources, output):
    data = collect(family, sources)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for step in data['steps']:
        target = output / step['name']
        target.mkdir(exist_ok=True)
        example = Path(sources) / step['repo'] / 'examples/datacentre'
        shutil.copyfile(example / 'expected/findings.json', target / 'findings.json')
        shutil.copyfile(example / step['render']['path'], target / ('render' + Path(step['render']['path']).suffix))
        print('PASS demo ' + step['name'] + ': ' + step['narrative'], flush=True)
    (output / 'story.json').write_text(json.dumps(data, indent=2) + '\n')
    (output / 'README.md').write_text('# Demo data centre walkthrough\n\n' + markdown(data, local=True))
    return data
