"""Source checkout, codeless build and one-path runtime for the family gate."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LIBRARIES = {"core": "usdAeco", "axis": "usdAecoAxis", "buildup": "usdAecoBuildUp",
             "wall": "usdAecoWall", "pipe": "usdAecoPipe",
             "cctv": "usdAecoCctv", "sync": "usdAecoSync"}


def dependency_pins():
    data = json.loads((ROOT / 'dependencies.json').read_text())
    return data['repos'] | data.get('nativeKits', {})


def repos(*, include_optional=False):
    state = ROOT / ".work/runtime.json"
    default = json.loads(state.read_text())["sources"] if state.is_file() else str(ROOT.parent)
    parent = Path(os.environ.get("AECO_FAMILY_ROOT", default)).resolve()
    pins = dependency_pins()
    return {name: Path(os.environ.get("AECO_" + name.upper().replace('-', '_') + "_SOURCE",
                                     parent / pin['repo'])).resolve()
            for name, pin in pins.items()}


def release_pins():
    data = json.loads((ROOT / "dependencies.json").read_text())
    paths = repos()
    return {name: {"base_tag": pin["ref"], "revision": pin.get("revision") or
                   run(["git", "rev-parse", "refs/tags/" + pin["ref"] + "^{commit}"], cwd=paths[name]).strip()}
            for name, pin in (data["repos"] | data.get("nativeKits", {})).items() if name in paths}


def clean_env():
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def run(command, *, cwd=ROOT, env=None, timeout=600):
    proc = subprocess.run(list(map(str, command)), cwd=cwd, env=env or clean_env(),
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode:
        raise RuntimeError(f"{Path(str(command[0])).name} failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout


def ensure_sources():
    """Source acquisition belongs to the disposable root, never sibling checkouts."""
    return None


def plugin_dir(name):
    root = repos()[name]
    library = LIBRARIES[name]
    candidates = [root / "out/plugins" / library / "resources", root / library,
                  root / "plugins" / library / "resources"]
    if name == 'cctv':
        candidates.insert(0, root / library)
    return next((p for p in candidates if (p / "plugInfo.json").is_file()), candidates[0])


def environment(pluginset=None):
    paths = repos()
    env = clean_env()
    # Supply only the explicit family roots below, excluding unrelated inputs.
    for name in list(env):
        if name.startswith("AECO_") and name.endswith("_ROOT"):
            env.pop(name)
    env.update(PYTHON=sys.executable, AECO_CORE=str(paths["core"]),
               AECO_CORE_ROOT=str(paths["core"]), CORE_DIR=str(paths["core"]),
               USDAECO_CORE_DIR=str(paths["core"]), TOOLCHAIN_DIR=str(paths["toolchain"]),
               AECO_BUILDUP_ROOT=str(paths["buildup"]))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Bound USD/TBB work per independent suite to avoid oversubscribing renders.
    env.setdefault('PXR_WORK_THREAD_LIMIT', '2')
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env.pop("AECO_RUN_REVIT", None)
    env.pop("AECO_REVIT_ENDPOINT", None)
    env["AECO_FAMILY_ROOT"] = str(paths["core"].parent)
    for name, path in paths.items():
        env["AECO_" + name.upper().replace("-", "_") + "_ROOT"] = str(path)
        env["AECO_" + name.upper().replace("-", "_") + "_SOURCE"] = str(path)
    for name in LIBRARIES:
        env[name.upper() + "_PLUGIN_DIR"] = str(plugin_dir(name))
    if pluginset:
        env["PXR_PLUGINPATH_NAME"] = str(pluginset)
        env["AECO_KIND_PLUGIN"] = str(pluginset)
    else:
        env.pop("PXR_PLUGINPATH_NAME", None)
        env.pop("PXR_AR_DEFAULT_SEARCH_PATH", None)
    return env


def audit_sources():
    """Fail before builds or imports on any source drift."""
    ensure_sources()
    for name, path in repos(include_optional=True).items():
        if not (path / '.git').exists():
            raise RuntimeError('Pinned source unavailable: ' + name)
    pins = release_pins()
    report = {}
    for name, path in repos(include_optional=True).items():
        if not (path / ".git").exists():
            raise RuntimeError("Pinned source unavailable: " + name)
        revision = run(["git", "rev-parse", "HEAD"], cwd=path).strip()
        changed = run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=path)
        changed = [s for s in changed.splitlines() if s[3:] != "STEERING.md"]
        report[name] = dict(revision=revision, expected=pins[name]["revision"],
                            base_tag=pins[name]["base_tag"], modified=bool(changed))
    drift = [n for n, r in report.items() if r.get("status") != "NOT RUN" and (r["revision"] != r["expected"] or r["modified"])]
    if drift:
        raise RuntimeError("Source pin audit failed: " + ", ".join(drift))
    return report


def isolate_sources(directory):
    """Complete the sibling layout before auditing/building disposable clones."""
    directory = Path(directory).resolve() / "sources"
    directory.mkdir(parents=True, exist_ok=True)
    scenarios = directory / "usdaeco-scenarios"
    if scenarios.exists() or scenarios.is_symlink():
        try:
            matches_root = scenarios.resolve() == ROOT
        except (OSError, RuntimeError):
            matches_root = False
        if not matches_root:
            raise RuntimeError("Family layout conflict: sources/usdaeco-scenarios "
                               "must resolve to the current scenarios checkout")
    else:
        scenarios.symlink_to(os.path.relpath(ROOT, directory), target_is_directory=True)
    sources = repos(include_optional=True)
    declarations = dependency_pins()
    base = os.environ.get("AECO_GIT_BASE")
    for name, source in sources.items():
        repo = declarations.get(name, {}).get('repo', 'usdaeco-' + name)
        destination = directory / repo
        if not destination.exists():
            pin = declarations[name]
            if (source / ".git").exists():
                revision = run(["git", "rev-parse", "refs/tags/" + pin["ref"] + "^{commit}"], cwd=source).strip()
                if pin.get("revision", revision) != revision:
                    raise RuntimeError("Source pin audit failed: " + name)
                run(["git", "clone", "--no-hardlinks", "--no-checkout", source, destination])
            else:
                if not base:
                    base = run(["git", "remote", "get-url", "origin"]).strip().rsplit("/", 1)[0]
                run(["git", "clone", "--no-checkout", base.rstrip("/") + "/" + repo + ".git", destination])
            if (destination / ".git").exists():
                run(["git", "checkout", "--detach", "refs/tags/" + pin["ref"]], cwd=destination)
        os.environ["AECO_" + name.upper().replace('-', '_') + "_SOURCE"] = str(destination)
    report = audit_sources()
    (ROOT / ".work").mkdir(exist_ok=True)
    (ROOT / ".work/runtime.json").write_text(json.dumps({"sources": str(directory), "pluginset": str(directory.parent / "pluginset")}) + "\n")
    return report


def build_plugins(directory):
    """Build in dependency order, then invoke the usdaeco-pluginset entry point."""
    isolate_sources(directory)
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    paths = repos()
    for name in LIBRARIES:
        print(f"== stage: build {name}", flush=True)
        # CCTV consumers register its source plugin. Keep the build proof away
        # from the legacy install location auto-discovered by sync integrations.
        install = directory / 'cctv-install' if name == 'cctv' else paths[name] / 'out'
        output = run(["bash", paths[name] / "build.sh", "--install-root", install], cwd=paths[name], env=environment())
        (directory / ("build-" + name + ".log")).write_text(output)
    pluginset = directory / "pluginset"
    # This is the source entry point installed as usdaeco-pluginset by the kit.
    run([sys.executable, paths["toolchain"] / "tools/pluginset.py", pluginset,
         *[plugin_dir(n) for n in LIBRARIES]],
        env=environment())
    return pluginset


def activate(pluginset):
    """Call before any Usd stage/SchemaRegistry construction."""
    os.environ.update(environment(Path(pluginset).resolve()))
    paths = repos()
    if not all(p.is_relative_to(Path(pluginset).resolve().parent) for p in paths.values()):
        raise RuntimeError("Activate an isolated gate plugin set; run check.py first")
    sys.path[:0] = [str(paths[n] / "tools") for n in paths]
    sys.path[:0] = [str(paths[n]) for n in ("sync", "ifc", "bonsai", "revit", *[n for n in paths if n not in ("sync", "ifc", "bonsai", "revit")])]
    # Discover Python validators before constructing the process-wide registry.
    from pxr import Plug
    Plug.Registry().RegisterPlugins(str(Path(pluginset).resolve()))
    for name, library in LIBRARIES.items():
        Plug.Registry().RegisterPlugins(str(paths[name] / (library + "Validators")))
    require_core_validators()
    # Entry point metadata is generated only in disposable source checkouts.
    import runpy
    for name in ("ifc", "bonsai", "revit"):
        runpy.run_path(str(paths[name] / "bootstrap.py"))
    from usdaeco_check import plugin_requires
    result = plugin_requires([])
    if not result:
        raise RuntimeError(result.detail)


def require_core_validators():
    """An empty registry is a broken gate, never successful validation."""
    import usdAecoValidators
    from pxr import UsdValidation
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword('UsdAecoValidators')
    validators = registry.GetOrLoadValidatorsByName([item.name for item in metadata])
    if len(validators) != 8 or not all(validators):
        raise RuntimeError('All eight core validators must load through UsdValidation')
    return len(validators)


def placeholder_sources(parent, output, entries):
    """Snapshot present unpinned repositories without claiming suite acceptance."""
    result = {}
    for entry in entries:
        name = entry['name']
        if entry['tag'] is not None or entry['kind'] != 'usecase':
            continue
        source = Path(parent) / name
        destination = Path(output) / 'sources' / name
        if not (destination / '.git').exists() and (source / '.git').exists():
            run(['git', 'clone', '--no-hardlinks', source, destination])
        present = (destination / '.git').exists()
        result[name] = dict(present=present)
        if present:
            result[name]['revision'] = run(['git', 'rev-parse', 'HEAD'], cwd=destination).strip()
    return result


def cli(*args):
    from usdaeco_bonsai.runtime import python
    proc = python(["-m", "aeco_sync", *map(str, args)], capture_output=True, text=True, timeout=240)
    if proc.returncode:
        raise RuntimeError(proc.stderr + proc.stdout)
    return json.loads(proc.stdout)


def import_model(native, directory):
    """IFC conversion followed by the two production kind importers."""
    from usdaeco_ifc.convert import convert
    from usdaeco_pipe.importer import import_pipe
    from usdaeco_wall.importer import import_wall
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    core, pipe, wall = [directory / n for n in ("model.usda", "pipe.usda", "wall.usda")]
    convert(str(native), str(core))
    stats = {"pipe": import_pipe(core, native, pipe), "wall": import_wall(pipe, native, wall)}
    return wall, stats


def init_session(model, native, directory):
    """CLI init plus catalog bindings reached through native occurrence types.

    The core intentionally gives no aeco:id to class prims. CLI init binds
    identity-bearing prims; the production-importer route binds their types here.
    """
    import ifcopenshell
    import ifcopenshell.util.element
    from pxr import Usd
    from aeco_sync.stack import Session
    from aeco_sync.readback import bind
    session = Session(cli("init", model, native, "--directory", directory)["stage"])
    file = ifcopenshell.open(str(native))
    with Usd.EditContext(session.stage, session.layer("kind.usda")):
        for prim in session.stage.Traverse():
            if not prim.HasAPI("AecoElementAPI"):
                continue
            ref = prim.GetAttribute("aeco:host:ifc:ref").Get()
            if not ref:
                continue
            typ = ifcopenshell.util.element.get_type(file.by_guid(ref))
            if typ:
                for target in prim.GetInherits().GetAllDirectInherits():
                    bind(session.stage.GetPrimAtPath(target), "ifc", typ.GlobalId,
                         "#" + str(typ.id()), session.version("ifc"), Path(native).resolve())
    session.layer("kind.usda").Save()
    return session


def python_command(args, *, source=None, extra_sources=()):
    """Run Python from source without an installed package or PYTHONPATH."""
    paths = repos()
    roots = ([source] if source else []) + list(extra_sources) + list(paths.values()) + [ROOT]
    imports = list(dict.fromkeys(str(p / suffix) if suffix else str(p)
                                for p in roots for suffix in ('tools', 'src', '')))
    args = list(map(str, args))
    code = 'import sys,runpy;sys.dont_write_bytecode=True;sys.path[:0]=' + repr(imports) + ';'
    if args[0] == '-m':
        code += 'sys.argv=' + repr(args[1:]) + ';runpy.run_module(sys.argv[0],run_name="__main__")'
    elif args[0] == '-c':
        code += 'sys.argv=' + repr(['-c', *args[2:]]) + ';exec(' + repr(args[1]) + ')'
    else:
        code += 'sys.argv=' + repr(args) + ';runpy.run_path(sys.argv[0],run_name="__main__")'
    return [sys.executable, '-c', code]


def compatibility_sources(directory):
    """Historical acceptance fixtures stay outside the consumer plugin set."""
    directory = Path(directory).resolve() / 'compatibility'
    directory.mkdir(parents=True, exist_ok=True)
    result = {}
    fixtures = json.loads((ROOT / 'dependencies.json').read_text())['fixtures']
    for name, pin in fixtures.items():
        destination = directory / name
        source = repos()[pin['repo'].removeprefix('usdaeco-')]
        if not destination.exists():
            run(['git','clone','--no-hardlinks','--no-checkout',source,destination])
            run(['git','checkout','--detach',pin['revision']],cwd=destination)
        if run(['git','rev-parse','HEAD'],cwd=destination).strip() != pin['revision']:
            raise RuntimeError('Historical fixture revision mismatch: ' + name)
        result[name] = destination
    # The historical core commits its resource plugin. No old schema is built
    # or loaded into the main consumer process. The newer compatibility core
    # needs an installed resource layout for the released catalog suite.
    if 'core091' in result:
        core = result['core091']
        resource = core / 'out/plugins/usdAeco/resources/plugInfo.json'
        if not resource.exists():
            env = environment()
            env['TOOLCHAIN_DIR'] = str(result['toolchain031'])
            run(['bash', core / 'build.sh', '--install-root', core / 'out'], cwd=core, env=env)
        for name in ('axis010', 'axis011'):
            axis = result[name]
            if not (axis / 'out/plugins/usdAecoAxis/resources/plugInfo.json').exists():
                env = environment()
                env['TOOLCHAIN_DIR'] = str(result['toolchain031'])
                env['CORE_DIR'] = str(core)
                env['CORE_PLUGIN_DIR'] = str(resource.parent)
                run(['bash', axis / 'build.sh', '--install-root', axis / 'out'], cwd=axis, env=env)
    return result


def publication_fixture(source, destination):
    """Clone an audited fixture at the layout retained in published USDA layers."""
    source, destination = Path(source), Path(destination)
    revision = run(['git', 'rev-parse', 'HEAD'], cwd=source).strip()
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        run(['git', 'clone', '--no-hardlinks', '--no-checkout', source, destination])
        run(['git', 'checkout', '--detach', revision], cwd=destination)
    actual = run(['git', 'rev-parse', 'HEAD'], cwd=destination).strip()
    changed = run(['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=destination)
    if actual != revision or changed.strip():
        raise RuntimeError('Publication fixture differs from its audited source')
    return destination
