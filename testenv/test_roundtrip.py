import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from pxr import Sdf, Usd, UsdGeom
from family import ROOT, import_model, init_session, repos
from baselines.wallpipe import build
from roundtrip_validators import evaluate


@pytest.fixture
def session(tmp_path):
    native = tmp_path / "baseline.ifc"
    build(str(native))
    model, _ = import_model(native, tmp_path / "model")
    return init_session(model, native, tmp_path / "session")


def rules(session):
    return {f["rule"] for f in evaluate(session.stage, ROOT / "profiles/roundtrip.json")["findings"]
            if f["severity"] == "error"}


def pipe(session):
    return next(p for p in session.stage.Traverse() if p.HasAPI("AecoPipeAPI"))


def test_imported_baseline_conforms(session):
    assert not rules(session)


@pytest.mark.parametrize("schema, expected", [("AecoPipeAPI", "roundtripKindMissing"),
                                               ("AecoAxisAPI", "roundtripAxisMissing")])
def test_missing_contracts_fail(session, schema, expected):
    with Usd.EditContext(session.stage, session.intent):
        pipe(session).RemoveAPI(schema)
    assert expected in rules(session)


def test_empty_binding_fails(session):
    with Usd.EditContext(session.stage, session.intent):
        pipe(session).GetAttribute("aeco:host:ifc:ref").Set("")
    assert "BindingMissing" in rules(session)


@pytest.mark.parametrize("location", ["root", "intent", "nested", "session"])
def test_derived_above_results_even_when_value_is_unchanged(session, location):
    if location == "nested":
        layer = Sdf.Layer.CreateAnonymous("editor.usda")
        session.intent.subLayerPaths.append(layer.identifier)
    else:
        layer = {"root": session.root, "intent": session.intent,
                 "session": session.stage.GetSessionLayer()}[location]
    prim = pipe(session)
    with Usd.EditContext(session.stage, layer):
        attr = prim.GetAttribute("aeco:pipe:outerDiameter")
        attr.Set(attr.Get())
    assert "derivedAboveResult" in rules(session)


def test_result_may_author_derived(session):
    with Usd.EditContext(session.stage, session.layer("result.ifc.usda")):
        attr = pipe(session).GetAttribute("aeco:pipe:outerDiameter")
        attr.Set(attr.Get())
    assert "derivedAboveResult" not in rules(session)


def test_no_result_layer_fails(session):
    session.root.subLayerPaths.remove("result.ifc.usda")
    assert "roundtripResultMissing" in rules(session)


def test_corner_door_and_l_t_joins(tmp_path):
    from baselines.wall_corner import build as corner
    native = tmp_path / "corner.ifc"
    file = corner(native)
    assert len(file.by_type("IfcWall")) == 3
    assert len(file.by_type("IfcDoor")) == 1
    assert {r.RelatingConnectionType for r in file.by_type("IfcRelConnectsPathElements")} == {"ATEND", "ATPATH"}
    model, stats = import_model(native, tmp_path / "model")
    assert stats["wall"]["fillings"] == 1 and stats["wall"]["joinTargets"] == 4
    session = init_session(model, native, tmp_path / "session")
    assert not rules(session)
    opening = next(p for p in session.stage.Traverse() if p.HasAPI("AecoOpeningAPI"))
    host = session.stage.GetPrimAtPath(opening.GetRelationship("aeco:opening:host").GetTargets()[0])
    with Usd.EditContext(session.stage, session.intent):
        host.GetAttribute("aeco:axis:end").Set((.25, 0, 0))
    assert "WallOpeningOutsideHost" in rules(session)


def test_stage_composes_without_plugins(session):
    probe = '''import sys
from pxr import Plug, Usd, UsdGeom
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
stage = Usd.Stage.Open(sys.argv[1])
assert stage and not stage.GetCompositionErrors() and stage.Flatten()
assert sum(p.IsA(UsdGeom.Mesh) for p in stage.Traverse()) == 4
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
'''
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PXR_PLUGINPATH_NAME")}
    subprocess.run([sys.executable, "-c", probe, str(session.path)], env=env, check=True)


def test_nix_pins_match_manifest():
    pins = json.loads((ROOT / "dependencies.json").read_text())["repos"]
    flake = (ROOT / "flake.nix").read_text()
    assert all(f'github:criad-com/{pin["repo"]}?ref={pin["ref"]}' in flake for name, pin in pins.items())


@pytest.mark.parametrize("library", ["pipe", "wall", "buildup", "cctv", "sync"])
def test_library_profile_regressions(library):
    # A fresh process avoids colliding same-named test modules across repos.
    from family import python_command
    candidates = [repos()[library] / 'testenv/test_profiles.py', repos()[library] / 'tests/test_profiles.py']
    profile = next((p for p in candidates if p.exists()), None)
    # Sync moved its legacy profile suite into the protocol regression tree.
    if profile is None and library == 'sync':
        profile = repos()[library] / 'tests/test_validators.py'
    assert profile and profile.exists(), 'Released profile regression suite unavailable'
    subprocess.run(python_command(["-m", "pytest", "-q", profile], source=repos()[library]),
                   cwd=repos()[library], check=True, timeout=120,
                   env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})


def test_revit_probe_is_optional_and_bounded(monkeypatch):
    from demo import roundtrip
    monkeypatch.delenv("AECO_REVIT_ENDPOINT", raising=False)
    assert not roundtrip.revit_available()
    monkeypatch.setenv("AECO_REVIT_ENDPOINT", "http://repl.example")
    def unavailable(url, timeout):
        assert url == "http://repl.example/status" and timeout == 45
        raise OSError("unavailable")
    monkeypatch.setattr(roundtrip.urllib.request, "urlopen", unavailable)
    assert not roundtrip.revit_available()
