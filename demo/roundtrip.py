#!/usr/bin/env python3
"""Unattended production-importer IFC/Bonsai roundtrip with an optional Revit gate."""
import argparse
import json
import os
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from family import ROOT, activate, build_plugins, cli, import_model, init_session


def revit_available():
    endpoint = os.environ.get("AECO_REVIT_ENDPOINT", "").rstrip("/")
    if not endpoint:
        return False
    try:
        with urllib.request.urlopen(endpoint + "/status", timeout=45) as response:
            status = json.load(response)
            return response.status == 200 and isinstance(status, dict)
    except (OSError, ValueError):
        return False


def run_demo(directory, *, revit=True):
    from pxr import Sdf, Usd, UsdGeom
    from aeco_sync.stack import Session, value
    from aeco_sync.derive import derive_gprims
    from baselines.wallpipe import build
    from scenarios.compare import compare
    from roundtrip_validators import evaluate

    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    native = directory / "baseline.ifc"
    build(str(native))
    model, stats = import_model(native, directory / "import")
    print("import: core converter + production pipe/wall importers", flush=True)

    # The IFC contains only DN50. An explicitly supplied synthetic catalog
    # extends the imported type below result layers, before any editor intent.
    imported = Usd.Stage.Open(str(model))
    catalog = json.loads((ROOT / "demo/size_catalog.json").read_text())
    with Usd.EditContext(imported, imported.GetRootLayer()):
        for prim in imported.TraverseAll():
            if prim.IsAbstract() and prim.HasAPI("AecoPipeTypeAPI"):
                for key, values in catalog.items():
                    prim.GetAttribute("aeco:pipeType:" + key).Set(values)
    imported.GetRootLayer().Save()

    sessions, output = {}, {"import": stats, "hosts": {}}
    # Each host receives the identical baseline and the same three driver
    # requests. A sequential second apply on cleared intent would do no work.
    from demo.datacentre import scenario_module
    native_bonsai = scenario_module().bonsai_available()
    for host in (("ifc", "bonsai") if native_bonsai else ("ifc",)):
        session = init_session(model, native, directory / host)
        elements = {p.GetAttribute("aeco:class:ifc:name").Get(): p
                    for p in session.stage.Traverse() if p.HasAPI("AecoElementAPI")}
        with Usd.EditContext(session.stage, session.layer("derived.usda")):
            for prim in elements.values():
                kind = "pipe" if prim.HasAPI("AecoPipeAPI") else "wall" if prim.HasAPI("AecoWallAPI") else None
                if kind:
                    derive_gprims(session.stage, prim, kind, "roundtrip demo")
        session.layer("derived.usda").Save()
        cli("--stage", session.path, "edit", elements["Pipe 1"].GetPath(), "length=2.5", "diameter=.065")
        cli("--stage", session.path, "edit", elements["Wall B"].GetPath(), "move=1,0,0")
        applied = cli("--stage", session.path, "apply", "--host", host)
        if applied["accepted"] != 3 or applied["refused"] or applied["pending"]:
            raise AssertionError(applied)
        for layer in session.stage.GetLayerStack():
            layer.Reload()
        current = session.current()
        resolved = {}
        receipt = session.layer("result." + host + ".usda")
        for label in ("Pipe 1", "Pipe 2", "Wall A", "Wall B"):
            prim = current.GetPrimAtPath(elements[label].GetPath())
            names = ["aeco:axis:start", "aeco:axis:end", "aeco:axis:length"]
            names += ["aeco:pipe:nominalDiameter", "aeco:pipe:outerDiameter", "aeco:pipe:innerDiameter"] if prim.HasAPI("AecoPipeAPI") else ["aeco:wall:height", "aeco:wall:thickness"]
            resolved[label] = {name: value(prim.GetAttribute(name).Get()) for name in names}
            resolved[label]["worldTranslation"] = value(UsdGeom.XformCache().GetLocalToWorldTransform(prim).ExtractTranslation())
            assert all(receipt.GetPropertyAtPath(prim.GetPath().AppendProperty(name)) for name in names), label
        assert abs(resolved["Pipe 1"]["aeco:axis:length"] - 2.5) < 1e-4
        assert abs(resolved["Pipe 1"]["aeco:pipe:nominalDiameter"] - .065) < 1e-8
        assert abs(resolved["Wall A"]["aeco:axis:length"] - 5) < 1e-4
        profile = evaluate(session.stage, ROOT / "profiles/roundtrip.json")
        if profile["errors"]:
            raise AssertionError(profile)
        output["hosts"][host] = {"stage": str(session.path), "resolved": resolved,
                                  "diagnostics": applied["diagnostics"], "profile": profile,
                                  "accepted": applied["accepted"], "pending": applied["pending"]}
        sessions[host] = session
        print(f"{host}: 3 edits applied; intent empty; roundtrip profile: 0 errors", flush=True)
        print(json.dumps({"result." + host: resolved, "diagnostics": applied["diagnostics"]}, indent=2))

    if native_bonsai:
        parity = compare(sessions["ifc"].path.parent / "result.ifc.usda",
                         sessions["bonsai"].path.parent / "result.bonsai.usda")
        if parity["differences"]:
            raise AssertionError(parity)
        print(f"ifc/bonsai parity: {parity['equal']}/{parity['compared']}", flush=True)
    else:
        parity = {"status": "NOT RUN", "reason": "Bonsai unavailable"}
    output["parity"] = parity
    from demo.coverage import run_coverage
    output["coverage"] = run_coverage(directory / "coverage")
    if revit and __import__("os").environ.get("AECO_RUN_REVIT") == "1" and revit_available():
        seed = os.environ.get("AECO_REVIT_STAGE")
        if not seed:
            raise RuntimeError("Revit is available: set AECO_REVIT_STAGE to a session bound to the native fixture (see demo/README.md)")
        from scenarios.revit import run_suite
        output["revit"] = run_suite(Path(seed), directory / "revit")
        if output["revit"]["status"] != "pass":
            raise AssertionError(output["revit"])
        print("revit: rollback scenario suite passed")
    else:
        output["revit"] = {"status": "NOT RUN", "reason": "live Revit acceptance not configured"}
        print("revit: skipped (endpoint not available)", flush=True)
    (directory / "report.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".work/demo")
    parser.add_argument("--pluginset", type=Path, help="Reuse a built aggregate; otherwise build the family")
    args = parser.parse_args()
    pluginset = args.pluginset or build_plugins(ROOT / ".work")
    activate(pluginset)
    run_demo(args.output)


if __name__ == "__main__":
    main()
