#!/usr/bin/env python3
"""Build and verify the family, IFC scenarios, Bonsai parity and production demo."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

from family import ROOT, LIBRARIES, activate, build_plugins, clean_env, environment, repos, isolate_sources


def repository_name(name):
    return name if name in ('usdSolid', 'usdSolidOcct') else 'usdaeco-' + name


def documentation_links(paths):
    """Retain the toolchain's file/link diagnostics using portable source names."""
    from usdaeco_check import link_check

    sources = {"scenarios": ROOT, **paths}
    checks = []
    for name, repo in sources.items():
        for path in (repo / "README.md", repo / "docs", repo / "demo"):
            if not path.exists():
                continue
            result = link_check(path)
            detail = result.detail
            for source, root in sorted(sources.items(), key=lambda item: len(str(item[1])), reverse=True):
                detail = detail.replace(str(root) + "/", repository_name(source) + "/")
            checks.append({"root": f"{repository_name(name)}/{path.name}",
                           "passed": bool(result), "detail": detail})
    passed = bool(checks) and all(item["passed"] for item in checks)
    detail = f"{sum(item['passed'] for item in checks)}/{len(checks)} roots"
    failures = [item["detail"] for item in checks if not item["passed"]]
    if failures:
        detail += "; " + "; ".join(failures)
    return passed, detail, checks


def acceptance_table(rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    return "| Gate | Result | Status |\n|---|---|---|\n" + "\n".join(
        "| " + " | ".join(cell(row[key]) for key in ("gate", "result", "status")) + " |"
        for row in rows) + "\n"


def structure_outcome(proc):
    """Report measured lint counts, including an explicit failure if absent."""
    counts = re.findall(r'(\d+) checks, (\d+) failed', proc.stdout)
    if not counts:
        return False, 'no structure acceptance count; see scenarios-structure.log'
    total, failed = map(int, counts[-1])
    passed = proc.returncode == 0 and total > 0 and failed == 0
    return passed, f'{total - failed}/{total} structure checks; current candidate, no recursive gate'


def publication_prerequisites(source, fixture_roots):
    """Verify availability of the byte-qualified inputs a publication requires."""
    import runpy

    namespace = runpy.run_path(str(source / 'src/dcbuild/dependencies.py'))
    document = json.loads((source / 'dependencies.json').read_text())
    pins = document.get('fixtures', {}) | document['repos']
    rows = []
    for name, root in fixture_roots.items():
        pin = pins[name]
        actual = namespace['runtime_digest'](root, pin['runtime_paths'])
        rows.append(dict(repo=pin['repo'], ref=pin['ref'], expected=pin['runtime_sha256'],
                         actual=actual, available=actual == pin['runtime_sha256']))
    return rows


def main():
    import os
    from family import python_command, plugin_dir, release_pins, placeholder_sources, dependency_pins
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".work/fresh")
    parser.add_argument("--pluginset", type=Path)
    parser.add_argument("--ifc-only", action="store_true")
    parser.add_argument("--profile", choices=("full", "fast"), default="full",
                        help="fast audits sources and committed outputs; publication suites and consumers are NOT RUN")
    parser.add_argument('--jobs', type=int, default=4, help='independent repository suite processes (default 4)')
    parser.add_argument("--reuse-library-report", type=Path, help="Reuse successful unchanged release checks; failures always run again")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started_gate = time.monotonic()
    rows, report = [], {"repositories": {}, "libraries": {}, "version": "0.8.1", "train": "aeco-0.8.1", "profile": args.profile}
    placeholder_root = Path(os.environ.get('AECO_FAMILY_ROOT', ROOT / 'out/family'))

    def save():
        report.update(rows=rows, passed=not any(r["status"] == "FAIL" for r in rows),
                      fullAcceptance=all(r["status"] == "PASS" for r in rows),
                      seconds=round(time.monotonic() - started_gate, 2),
                      counts={s: sum(r['status'] == s for r in rows) for s in ('PASS', 'FAIL', 'NOT RUN')})
        (output / "acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "acceptance.md").write_text(acceptance_table(rows))

    def portable(value):
        for name, path in sorted({"scenarios": ROOT, **repos()}.items(), key=lambda p: len(str(p[1])), reverse=True):
            value = value.replace(str(path), repository_name(name))
        return value.replace(str(output), "gate-output")

    def record(name, passed, detail, *, status=None, evidence=None):
        status = status or ("PASS" if passed else "FAIL")
        row = dict(gate=name, passed=bool(passed) and status == "PASS", status=status, result=portable(detail))
        if evidence is not None:
            row["evidence"] = json.loads(portable(json.dumps(evidence)))
        rows.append(row)
        print(f"{status} {name}: {row['result']}", flush=True)
        save()

    def execute(name, command, *, cwd=ROOT, env=None, timeout=1200):
        print("== stage: " + name, flush=True)
        started = time.monotonic()
        try:
            proc = subprocess.run(command, cwd=cwd, env=env or environment(pluginset),
                                  capture_output=True, text=True, timeout=timeout)
            log = proc.stdout + proc.stderr
            (output / (name + ".log")).write_text(log)
            return proc, round(time.monotonic() - started, 2)
        except subprocess.TimeoutExpired as exc:
            log = (exc.stdout or b'') + (exc.stderr or b'')
            (output / (name + ".log")).write_bytes(log if isinstance(log, bytes) else log.encode())
            return subprocess.CompletedProcess(command, 124, '', 'timeout; see ' + name + '.log'), round(time.monotonic() - started, 2)

    def finish():
        proc, _ = execute('tests', python_command(['-m','pytest','-q',ROOT / 'testenv']), timeout=240)
        if proc: record('gate regression tests', proc.returncode == 0, proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr)
        from sanitization import scan, source_files
        sanitation = scan(source_files(ROOT))
        record('sanitization', sanitation['passed'], f"{sanitation['files']} files; {len(sanitation['violations'])} violations", evidence=sanitation)
        passed, detail, checks = documentation_links({n: paths[n] for n in available})
        record('links at end', passed, detail, evidence=checks)
        elapsed = round(time.monotonic() - started_gate, 2)
        record('family wall-clock budget', elapsed <= 360, f'{elapsed}s / 360s; {args.profile} profile; {args.jobs} suite processes; source isolation, builds, suites and consumers included')
        save()
        print('\n' + acceptance_table(rows))
        print(f"{len(rows)} checks, {sum(r['status']=='FAIL' for r in rows)} failed, {sum(r['status']=='NOT RUN' for r in rows)} not run")
        return int(not report['passed'])

    print("== stage: isolate exact released sources", flush=True)
    report["repositories"] = isolate_sources(output)
    available = {n: r for n, r in report["repositories"].items() if r.get("status") != "NOT RUN"}
    record("revision pins", len(available) == len(report['repositories']), f"{len(available)}/{len(report['repositories'])} exact sources")
    paths = repos()
    sys.path.insert(0, str(paths["toolchain"] / "tools"))
    from family_manifest import validate_family
    from release_pins import audit, optional_compatibility
    inventory = json.loads((ROOT / "family.json").read_text())
    result = validate_family(inventory, inventory=True)
    record("family inventory", bool(result), result.detail)
    released = dict(inventory, repos=[r for r in inventory['repos'] if r['released'] is not None])
    result = validate_family(released)
    record("released family compatibility", bool(result), result.detail)
    indexed = {entry['name']: entry for entry in inventory['repos']}
    sys.path.insert(0, str(ROOT / 'tools'))
    from usdaeco_scenarios.drift import audit as drift_audit
    from usdaeco_scenarios.index import fresh_check, released_sources
    with released_sources(inventory['repos'], placeholder_root) as index_sources:
        drift = drift_audit(inventory, {repository_name(n): paths[n] for n in available} | {'usdaeco-scenarios': ROOT},
                            tag_sources={'aeco-toolchain': index_sources / 'aeco-toolchain'})
        index_result = fresh_check(ROOT / 'docs/family/README.md', family=ROOT / 'family.json', repos=index_sources)
    report['drift'] = drift
    for key, title in [('pins', 'drift dependency train intervals'), ('ranges', 'drift requirement ranges'), ('stories', 'drift use-case publication contracts')]:
        checks = drift[key]
        record(title, bool(checks) and all(r['passed'] for r in checks),
               f"{sum(r['passed'] for r in checks)}/{len(checks)}; {sum(not r['passed'] for r in checks)} mismatches", evidence=checks)
    record('family index freshness', bool(index_result), index_result.detail)
    manifest_matches = []
    for name in available:
        metadata = json.loads((paths[name] / 'library.json').read_text())
        entry = indexed[repository_name(name)]
        manifest_matches.append(metadata['requires'] == entry['requires']
                                and 'v' + metadata['version'] == entry['released'])
    record('family release manifests', all(manifest_matches),
           f'{sum(manifest_matches)}/{len(manifest_matches)} versions and declared ranges match tagged manifests')
    pin_rows = audit({n: paths[n] for n in available}, {n: release_pins()[n] for n in available})
    report['requirements'] = pin_rows
    record("released requirements", all(r['passed'] for r in pin_rows),
           f"{sum(r['passed'] for r in pin_rows)}/{len(pin_rows)} tags and declared requirements", evidence=pin_rows)
    companion = optional_compatibility(paths, release_pins(), optional=('cctv-exec',))['cctv-exec']
    record('optional cctv-exec compatibility', companion['status'] == 'PROVEN', companion['reason'], evidence=companion)
    report['placeholders'] = placeholder_sources(placeholder_root, output, inventory['repos'])
    for entry in inventory['repos']:
        if entry['released'] is None:
            placeholder = report['placeholders'].get(entry['name'])
            if placeholder is not None and not placeholder['present']:
                record(entry['name'].removeprefix('usdaeco-') + ' check.py', False,
                       'required wave-2 repository missing', evidence=placeholder)
                continue
            record(entry['name'].removeprefix('usdaeco-') + ' check.py', False,
                   'documentation seed; no executable suite' if entry['kind'] == 'meta' else
                   'repository present; unreleased wave-2 suite deferred until the next train',
                   status='NOT RUN', evidence=placeholder)
    for phase in ('before builds',):
        passed, detail, checks = documentation_links({n: paths[n] for n in available})
        record('links ' + phase, passed, detail, evidence=checks)
    pluginset = args.pluginset.resolve() if args.pluginset else build_plugins(output)
    probe = """from pxr import Plug, Usd
expected = {'usdAeco','usdAecoAxis','usdAecoBuildUp','usdAecoWall','usdAecoPipe','usdAecoCctv','usdAecoSync'}
actual = {p.name for p in Plug.Registry().GetAllPlugins() if p.name.startswith('usdAeco') and not p.name.endswith('Validators')}
assert actual == expected, actual
for name in ('AecoAxisAPI','AecoBuildUpAPI','AecoWallAPI','AecoPipeAPI','AecoCctvSensorAPI','AecoHostBindingAPI'):
    assert Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(name), name
assert Usd.SchemaRegistry().FindAppliedAPIPrimDefinition('AecoAxisAPI').GetPropertyMetadata('aeco:axis:length','aecoDerived') is True
"""
    proc, _ = execute('plugin-registry', [sys.executable, '-c', probe])
    if proc: record('one plugin path', proc.returncode == 0, '7/7 libraries' if not proc.returncode else proc.stderr)
    if args.profile == 'fast':
        activate(pluginset)
        from family import require_core_validators
        record('core validator registry', require_core_validators() == 8, '8/8 loaded through UsdValidation')
        from usdaeco_scenarios.evidence import variant_rows, committed_rows
        for row in variant_rows(paths['datacentre']) + committed_rows(paths):
            record(row['gate'], row['passed'], row['result'], evidence=row.get('evidence'))
        from usdaeco_scenarios.walkthrough import export, markdown
        story = export(inventory, paths['core'].parent, output / 'walkthrough')
        report['walkthrough'] = story
        readme_story = (ROOT / 'README.md').read_text().split('<!-- demo:start -->')[-1].split('<!-- demo:end -->')[0].strip()
        record('five-use-case walkthrough', len(story['steps']) == 5 and readme_story == markdown(story).strip(),
               '5 released example outputs and 5 renders; README story matches')
        for name in paths:
            record(name + ' check.py', False,
                   'fast profile: full suite includes publication or native reproduction; not executed', status='NOT RUN')
        record('publication reproductions and derived consumers', False,
               'fast profile checks committed artifacts; fresh examples, renders, determinism and roundtrips not executed', status='NOT RUN')
        proc, _ = execute('scenarios-structure', python_command([ROOT / 'check.py', '--structure-only']), env=environment())
        record('scenarios check.py', *structure_outcome(proc))
        return finish()

    from usdaeco_scenarios.suite_inputs import prepare, plugin as input_plugin, harness_source, example_environment
    suite_inputs, report['suiteInputs'], suite_sources = prepare(paths, output)
    suite_harnesses = {name: harness_source(source, suite_inputs[name], paths['toolchain'])
                       for name, source in paths.items()}
    report['suiteHarnesses'] = {
        name: dict(repo='usdaeco-toolchain',
                   ref='v' + json.loads((source / 'library.json').read_text())['version'],
                   scope='declared suite input' if source != paths['toolchain'] else 'train harness')
        for name, source in suite_harnesses.items()}
    report['suiteLayouts'] = {name: str(source.relative_to(output)) for name, source in suite_sources.items()}
    report['suiteToolchain'] = dict(dependency_pins()['toolchain'],
                                   reason='Consumer builds and scenarios lint use the train; suites use their declared harnesses')
    previous = json.loads(args.reuse_library_report.read_text()) if args.reuse_library_report else None
    if previous and (previous['repositories'] != report['repositories'] or previous.get('profile') != 'full'):
        raise ValueError('Cannot reuse library evidence with different source pins or profile')

    def check_environment(name):
        selected = suite_inputs[name]
        env = environment()
        env.pop('AECO_KIND_PLUGIN', None)
        env.pop('AECO_DATACENTRE_STAGE', None)
        for alias, path in selected.items():
            for suffix in ('ROOT', 'SOURCE'):
                env['AECO_' + alias.upper().replace('-', '_') + '_' + suffix] = str(path)
        env.update(AECO_CORE=str(selected['core']), CORE_DIR=str(selected['core']),
                   USDAECO_CORE_DIR=str(selected['core']), TOOLCHAIN_DIR=str(suite_harnesses[name]))
        for alias, library in LIBRARIES.items():
            env[alias.upper() + '_PLUGIN_DIR'] = str(input_plugin(selected[alias], library))
        # The executing suite uses its own schema; dependency plugins use the
        # recorded release inputs. The independent consumer uses the train.
        if name in LIBRARIES:
            env[name.upper() + '_PLUGIN_DIR'] = str(plugin_dir(name))
        schema_names = set()
        by_library = {e['library']: e for e in inventory['repos'] if e['library']}
        by_repo = {e['name']: e for e in inventory['repos']}
        def include(entry):
            lib = entry['library']
            if lib in schema_names: return
            if lib: schema_names.add(lib)
            for dep in entry['requires']:
                include(by_library.get(dep) or by_repo[dep])
        include(by_repo[source_names[name]])
        if name in ('ifc', 'bonsai', 'revit'):
            schema_names = {'usdAeco', 'usdAecoAxis', 'usdAecoCctv'}
        env['PXR_PLUGINPATH_NAME'] = os.pathsep.join(str(p) for alias, lib in LIBRARIES.items()
            if lib in schema_names for p in (env[alias.upper() + '_PLUGIN_DIR'],
                (paths[alias] if name == alias else selected[alias]) / (lib + 'Validators')))
        library = by_repo[source_names[name]]['library']
        if library and name not in LIBRARIES and name not in ('usdSolid', 'usdSolidOcct'):
            env['PXR_PLUGINPATH_NAME'] += os.pathsep + os.pathsep.join(
                str(p) for p in (paths[name] / library, paths[name] / (library + 'Validators')))
        if name in ('core', 'axis', 'buildup', 'toolchain'):
            env = example_environment(paths[name], env)
        if name == 'toolchain':
            env.pop('AECO_FAMILY_SIBLINGS', None)
        if name == 'datacentre':
            env['AECO_TOOLCHAIN_ROOT'] = str(suite_harnesses[name])
            env['AECO_TOOLCHAIN_SOURCE'] = str(suite_harnesses[name])
            validation = selected['validation_core']
            env['PXR_PLUGINPATH_NAME'] = os.pathsep.join(
                str(p) for p in (input_plugin(validation, 'usdAeco'), validation / 'usdAecoValidators'))
        env['PYTHONPATH'] = os.pathsep.join([str(selected['core']), str(paths[name])])
        if name == 'datacentre':
            env['PYTHONPATH'] = os.pathsep.join([str(selected['validation_core']), str(paths[name])])
        if args.ifc_only: env['AECO_BLENDER'] = 'unavailable'
        return env

    source_names = {name: pin['repo'] for name, pin in dependency_pins().items()}
    def run_suite(name):
        source = suite_sources[name]
        extras = [suite_harnesses[name], *[p for key, p in suite_inputs[name].items() if key != 'toolchain']]
        if name == 'datacentre':
            extras.insert(1, suite_inputs[name]['validation_core'])
        arguments = [source / 'check.py']
        if name == 'toolchain' and not all(os.environ.get(key) for key in
                ('AECO_NATIVE_SCHEMA', 'AECO_NATIVE_PLUGIN', 'AECO_NATIVE_PYTHON', 'AECO_USD_PYTHON')):
            arguments.append('--without-native')
        return execute(name, python_command(arguments, source=source, extra_sources=extras),
                       cwd=source, env=check_environment(name))

    pool = ThreadPoolExecutor(max_workers=args.jobs)
    # Start the longer independent suites first; report in manifest order.
    order = list(dict.fromkeys(['datacentre', 'ifc', 'plan', 'solid', *paths]))
    pending = {name: pool.submit(run_suite, name) for name in order
               if name in available and (paths[name] / 'check.py').is_file()
               and not (name == 'bonsai' and args.ifc_only)
               and not (previous and previous['libraries'].get(name, {}).get('passed'))}
    for name, source in paths.items():
        if name not in available or not (source / 'check.py').exists():
            record(name + ' check.py', False, 'source or check.py unavailable')
            continue
        if name == 'bonsai' and args.ifc_only:
            record('bonsai check.py', False, 'native host explicitly disabled', status='NOT RUN')
            continue
        if name == 'datacentre':
            prerequisite_rows = publication_prerequisites(source, {
                key: suite_inputs[name][key] for key in ('core', 'ifc', 'revit', 'toolchain', 'validation_core')})
            report['publicationPrerequisites'] = prerequisite_rows
            missing = [r for r in prerequisite_rows if not r['available']]
            if missing:
                record('datacentre declared runtime inputs', False,
                       '; '.join(r['repo'] + ' ' + r['ref'] + ' byte-qualified input unavailable' for r in missing),
                       evidence=prerequisite_rows)
        old = previous['libraries'].get(name, {}) if previous else {}
        if old.get('passed'):
            omitted = old.get('notRunCount', len(old.get('notRun', [])))
            old['notRunCount'] = omitted
            report['libraries'][name] = old
            record(name + ' check.py', True,
                   f"{old['checks'] - omitted}/{old['checks']}; {omitted} NOT RUN; "
                   f"{old['seconds']}s; reused successful check of unchanged release")
            if name == 'toolchain':
                for row in previous['rows']:
                    if row['gate'] == 'toolchain native templates':
                        record(row['gate'], False, row['result'], status=row['status'])
            if name in previous and name in ('ifc','bonsai'):
                report[name] = previous[name]
                for row in previous['rows']:
                    if row['gate'].startswith(name + ' ') and row['gate'] != name + ' check.py':
                        record(row['gate'], row['passed'], row['result'], status=row['status'])
            continue
        if name == 'toolchain' and not all(os.environ.get(key) for key in
                ('AECO_NATIVE_SCHEMA', 'AECO_NATIVE_PLUGIN', 'AECO_NATIVE_PYTHON', 'AECO_USD_PYTHON')):
            record('toolchain native templates', False,
                   'installed native template artifacts unavailable; source suite runs; no dependency downloads attempted',
                   status='NOT RUN')
        proc, seconds = pending[name].result()
        if proc is None: continue
        counts = re.findall(r'(\d+) checks, (\d+) failed', proc.stdout)
        total, failed = map(int, counts[-1]) if counts else (0, 0)
        passed = proc.returncode == 0 and total > 0 and failed == 0
        not_run = re.findall(r'^(?:NOT RUN|NOT_RUN|SKIP)\s+(.+)$', proc.stdout, re.M)
        omitted = re.findall(r'\d+ checks, \d+ failed, (\d+) not run', proc.stdout)
        omitted_count = int(omitted[-1]) if omitted else len(not_run)
        detail = (f'{total - failed - omitted_count}/{total}; {omitted_count} NOT RUN; {seconds}s'
                  if counts else 'no acceptance count; see ' + name + '.log')
        report['libraries'][name] = dict(passed=passed, checks=total, failed=failed, seconds=seconds,
                                         notRun=not_run, notRunCount=omitted_count, ref=release_pins()[name]['base_tag'])
        record(name + ' check.py', passed, detail)
        if name == 'ifc' and passed:
            data = json.loads((source / '.work/check.json').read_text())
            report['ifc'] = data
            for group, expected in [('synthetic',21), ('camera',9), ('datacentre',9)]:
                cases = data['hostCases'][group]
                good = sum(r['passed'] for r in cases)
                record('ifc scenarios' if group == 'synthetic' else 'ifc ' + group + ' scenarios',
                       len(cases) == good == expected, f'{good}/{expected}; IFC entry point')
        if name == 'bonsai' and passed:
            data = json.loads((source / 'out/check.json').read_text())
            report['bonsai'] = data
            cases = data['native']; good = sum(r['passed'] and r['repeatMutations'] == 0 for r in cases)
            record('bonsai scenarios', len(cases) == good == 21, f'{good}/21; native Bonsai entry point')
            record('bonsai idempotence', all(r['repeatMutations'] == 0 for r in cases), f'{len(cases)} cases; zero repeat mutations')
    pool.shutdown(wait=True)
    from usdaeco_check.example_paths import relocate_source
    for name in ('wall','pipe'):
        source = paths[name]
        env = check_environment(name)
        env['TOOLCHAIN_DIR'] = str(paths['toolchain'])
        axis = suite_inputs[name]['axis']
        env['AECO_AXIS_ROOT'] = str(paths['axis'])
        env['AXIS_PLUGIN_DIR'] = str(plugin_dir('axis'))
        env['PXR_PLUGINPATH_NAME'] = env['PXR_PLUGINPATH_NAME'].replace(
            str(input_plugin(axis, 'usdAecoAxis')), str(plugin_dir('axis'))).replace(
            str(axis / 'usdAecoAxisValidators'), str(paths['axis'] / 'usdAecoAxisValidators'))
        env['AECO_DATACENTRE_ROOT'] = str(paths['datacentre'])
        # Override mode does not refresh the harness's pinned-source alias.
        # Retarget it explicitly before S29 archives the train's source paths.
        relocate_source(source / 'examples/datacentre', paths['datacentre'])
        env['AECO_DATACENTRE_STAGE'] = str(paths['datacentre'] / 'dist/clash/dc.usda')
        proc, _ = execute(name + '-clash-consumer', python_command([source / 'examples/datacentre/run.py'], source=source), cwd=source, env=env)
        if proc:
            record(name + ' published clash compatibility', proc.returncode == 0,
                   release_pins()['datacentre']['base_tag'] + ' stage override; released findings and render contract' if not proc.returncode else 'see ' + name + '-clash-consumer.log')
    proc, _ = execute('scenarios-structure', python_command([ROOT / 'check.py', '--structure-only']), env=environment())
    if proc: record('scenarios check.py', *structure_outcome(proc))
    record('scenario + S4 parity', False, 'split integration case sets; production roundtrip parity is measured separately', status='NOT RUN')
    record('revit scenarios', False, 'live Revit execution outside this gate', status='NOT RUN')
    record('cctv-exec native', False, 'native consumer unavailable; source check recorded separately', status='NOT RUN')
    activate(pluginset)
    from family import require_core_validators
    record('core validator registry', require_core_validators() == 8, '8/8 loaded through UsdValidation')
    from usdaeco_scenarios.evidence import variant_rows, example_rows
    for row in variant_rows(paths['datacentre']) + example_rows(paths, report['libraries']):
        record(row['gate'], row['passed'], row['result'], evidence=row.get('evidence'))
    from usdaeco_scenarios.walkthrough import export, markdown
    story = export(inventory, paths['core'].parent, output / 'walkthrough')
    report['walkthrough'] = dict(train=story['train'], steps=[{k: s[k] for k in ('name','repo','tag','source','findings_sha256','render')} for s in story['steps']])
    readme_story = (ROOT / 'README.md').read_text().split('<!-- demo:start -->')[-1].split('<!-- demo:end -->')[0].strip()
    record('five-use-case walkthrough', len(story['steps']) == 5 and readme_story == markdown(story).strip(),
           '5 released example outputs and 5 renders; README story matches')
    if args.ifc_only: os.environ['AECO_BLENDER'] = 'unavailable'
    from demo.coverage import coverage_kernel
    kernel = coverage_kernel()
    proc, _ = execute('cctv-scenarios', python_command([ROOT / 'scenarios/cctv.py', '--pluginset', pluginset, '--kernel', kernel,
                                                     '--output', output / 'cctv-scenarios.json'], source=paths['cctv']), cwd=paths['cctv'])
    if proc:
        data = json.loads((output / 'cctv-scenarios.json').read_text()) if (output / 'cctv-scenarios.json').exists() else {}
        definitions = json.loads((paths['cctv'] / 'scenarios/cctv_cases.json').read_text())['cases']
        expected = {c['id'] for c in definitions if c['id'].startswith('V-')}
        actual = data.get('cases', []); good = {c['id'] for c in actual if c['passed']}
        record('cctv scenarios', proc.returncode == 0 and len(actual) == len(expected) and good == expected,
               f'{len(good)}/{len(expected)} ({kernel})', evidence=data)
    proc, _ = execute('demo', python_command([ROOT / 'demo/roundtrip.py', '--pluginset', pluginset, '--output', output / 'demo']))
    if proc and proc.returncode == 0:
        data = json.loads((output / 'demo/report.json').read_text()); report['demo'] = json.loads(portable(json.dumps(data)))
        both = len(data['hosts']) == 2
        record('demo ifc + bonsai', both, '3 edits per host; cleared intent', status=None if both else 'NOT RUN')
        parity = data['parity']
        record('demo parity', both and not parity.get('differences'), f"{parity.get('equal',0)}/{parity.get('compared',0)}", status=None if both else 'NOT RUN')
        record('roundtrip profile', all(h['profile']['errors'] == 0 for h in data['hosts'].values()), '0 errors')
        coverage = data['coverage']
        record('cctv demo derivation', coverage['derive']['sensors'] == 4 and not coverage['derive']['skipped'], '4/4 sensors')
        record('cctv demo steps', coverage['passed'] == 6 and coverage['failed'] == 0, '6/6 steps')
        rendered = coverage['render']
        record('cctv demo render', rendered['status'] == 'pass', '2/2 images' if rendered['status'] == 'pass' else rendered.get('reason',''), status=None if rendered['status'] == 'pass' else 'NOT RUN')
    elif proc: record('demo ifc + bonsai', False, 'see demo.log')
    proc, _ = execute('datacentre-scenario', python_command([ROOT / 'scenarios/published.py', '--pluginset', pluginset, '--output', output / 'datacentre']), timeout=600)
    if proc:
        first_consumer_row = len(rows)
        artifact = output / 'datacentre/report.json'
        if artifact.exists():
            data = json.loads(artifact.read_text()); report['datacentre'] = data
            for row in data['rows']:
                record(row['gate'], row['status'] == 'PASS', row['result'], status=row['status'], evidence=row.get('evidence'))
        else: record('datacentre scenario', False, 'no report; see datacentre-scenario.log')
        if proc.returncode and not any(r['status'] == 'FAIL' for r in rows[first_consumer_row:]):
            record('datacentre process', False, 'nonzero exit; see datacentre-scenario.log')
    return finish()



if __name__ == '__main__':
    raise SystemExit(main())
