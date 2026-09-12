"""Reproduce released suites with their declared inputs, preserving train drift."""
import json
import os
from pathlib import Path

from family import LIBRARIES, environment, run


def declarations(source):
    data = json.loads((source / 'dependencies.json').read_text())
    direct = data['repos'] | data.get('nativeKits', {})
    # Explicit flake inputs and byte-qualified generation fixtures need
    # checkouts. Synthetic and recorded-file fixtures remain data.
    fixtures = {k: p for k, p in data.get('fixtures', {}).items()
                if isinstance(p, dict) and (p.get('runtime_paths') or p.get('flakeInput') is True)}
    return direct, fixtures


def harness_source(source, selected, train_toolchain):
    """Repository suites execute their declared toolchain, including fixtures."""
    direct, fixtures = declarations(source)
    declared = any(pin.get('repo') == 'usdaeco-toolchain'
                   for pin in (direct | fixtures).values())
    return selected['toolchain'] if declared else train_toolchain


def example_environment(source, environment):
    """Keep declared facility inputs only for suites that consume that source."""
    direct, fixtures = declarations(source)
    env = dict(environment)
    metadata = json.loads((Path(source) / 'library.json').read_text())
    minimal = metadata['name'] in ('usdAeco', 'usdAecoAxis')
    if minimal or not any(pin.get('repo') == 'usdaeco-datacentre' for pin in (direct | fixtures).values()):
        env.pop('AECO_DATACENTRE_ROOT', None)
        env.pop('AECO_DATACENTRE_STAGE', None)
    return env


def prepare(paths, output):
    """Clone exact suite inputs locally; never rewrite a released manifest."""
    by_repo = {('usdaeco-' + n if not n.startswith('usdSolid') else n): p
               for n, p in paths.items()}
    by_repo['usdaeco-scenarios'] = Path(os.environ['AECO_FAMILY_ROOT']) / 'usdaeco-scenarios'
    cache, suites, evidence, execution = {}, {}, {}, {}
    for name, source in paths.items():
        selected = dict(paths)
        recorded = {}
        direct, fixtures = declarations(source)
        for kind, pins in (('direct', direct), ('fixture', fixtures)):
            for key, pin in pins.items():
                repo, ref = pin.get('repo'), pin.get('ref')
                if repo not in by_repo or not ref:
                    continue
                # Public releases may carry byte-qualified historical runtime
                # fixtures in-tree; their old tags need not exist on the mirror.
                vendored = source / pin['path'] if kind == 'fixture' and pin.get('path') else None
                if vendored and vendored.is_dir() and pin.get('runtime_paths') and pin.get('runtime_sha256'):
                    if key in recorded:
                        raise ValueError('Fixture shadows a direct suite input: ' + key)
                    selected[key] = vendored
                    recorded[key] = dict(repo=repo, ref=ref, scope=kind, path=pin['path'],
                                         runtime_sha256=pin['runtime_sha256'])
                    continue
                origin = by_repo[repo]
                revision = run(['git', 'rev-parse', ref + '^{commit}'], cwd=origin).strip()
                recorded_revisions = {pin.get('revision'), pin.get('publicRevision')} - {None}
                if recorded_revisions and revision not in recorded_revisions:
                    raise ValueError('Suite input revision mismatch: ' + repo + ' ' + ref)
                identity = repo, revision
                if identity not in cache:
                    if run(['git', 'rev-parse', 'HEAD'], cwd=origin).strip() == revision:
                        target = origin
                    else:
                        target = Path(output) / 'release-inputs' / ref / repo
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if not target.exists():
                            run(['git', 'clone', '--no-hardlinks', '--no-checkout', origin, target])
                            run(['git', 'checkout', '--detach', revision], cwd=target)
                        if run(['git', 'rev-parse', 'HEAD'], cwd=target).strip() != revision:
                            raise ValueError('Suite input checkout mismatch: ' + repo)
                    cache[identity] = target
                alias = key if kind == 'fixture' or key == 'validation_core' else repo.removeprefix('usdaeco-')
                if kind == 'fixture' and alias in recorded:
                    raise ValueError('Fixture shadows a direct suite input: ' + alias)
                selected[alias] = cache[identity]
                recorded[alias] = dict(repo=repo, ref=ref, revision=revision, scope=kind)
        execution[name] = source
        suites[name] = selected
        evidence[name] = recorded

    # Released suites still expect installed core/axis resource directories.
    # Build only our disposable older inputs; the train set is already built.
    for name, library in LIBRARIES.items():
        for target in sorted({m[name] for m in suites.values()} - {paths[name]}):
            if not (target / library / 'schema.usda').is_file():
                continue
            selected = next(m for m in suites.values() if m[name] == target)
            env = environment()
            for alias, path in selected.items():
                env['AECO_' + alias.upper().replace('-', '_') + '_ROOT'] = str(path)
            # Generation fixtures do not replace the schema dependency used
            # to build a modern validation/transport input.
            core = selected.get('validation_core', selected['core'])
            env.update(TOOLCHAIN_DIR=str(paths['toolchain']), CORE_DIR=str(core),
                       AECO_CORE=str(core), AECO_CORE_ROOT=str(core), USDAECO_CORE_DIR=str(core),
                       CORE_PLUGIN_DIR=str(plugin(core, 'usdAeco')))
            print('== stage: build declared suite input ' + target.name + ' ' +
                  json.loads((target / 'library.json').read_text())['version'], flush=True)
            run(['bash', target / 'build.sh', '--install-root', target / 'out'], cwd=target, env=env)
    return suites, evidence, execution


def plugin(source, library):
    candidates = [source / 'out/plugins' / library / 'resources', source / library,
                  source / 'plugins' / library / 'resources']
    return next(p for p in candidates if (p / 'plugInfo.json').is_file())
