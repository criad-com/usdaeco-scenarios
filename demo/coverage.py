"""Portable lobby derivation, the six coverage steps, and optional Embree images."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from family import clean_env, repos

STEPS = ("V-baseline", "V-temp-ignored", "V-temp-counted",
         "V-unclassified", "V-tray", "V-stale")


def coverage_kernel():
    try:
        from embreex import rtcore_scene  # noqa: F401
    except (ImportError, OSError):
        return "numpy"
    return "embree"


def scenario_runner():
    # Load by filename: the IFC integration owns the scenarios package name.
    from family import ROOT
    spec = importlib.util.spec_from_file_location('consumer_cctv_cases', ROOT / 'scenarios/cctv.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.runner()


def render_inputs(stage_path, directory, sensor_path):
    """Bake disposable viewer snapshots; visibility edits belong to the session."""
    from pxr import Gf, Usd, UsdGeom
    stage = Usd.Stage.Open(str(stage_path))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        camera = UsdGeom.Camera.Define(stage, "/DemoOverview")
        camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(
            Gf.Vec3d(18, -18, 19), Gf.Vec3d(6, 4, 1), Gf.Vec3d(0, 0, 1)).GetInverse())
        camera.CreateFocalLengthAttr(28)
        camera.CreateClippingRangeAttr(Gf.Vec2f(.1, 100))
    overview = directory / "overview.usda"
    stage.Flatten().Export(str(overview))
    sensor = stage.GetPrimAtPath(sensor_path)
    if not sensor or not sensor.IsA(UsdGeom.Camera):
        raise ValueError("Look-through sensor is not a Camera: " + sensor_path)
    hidden = []
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        for prim in Usd.PrimRange(sensor):
            imageable = UsdGeom.Imageable(prim)
            if imageable and imageable.ComputePurpose() == UsdGeom.Tokens.guide:
                UsdGeom.VisibilityAPI.Apply(prim).CreateGuideVisibilityAttr(UsdGeom.Tokens.invisible)
                # usdrecord's legacy Embree imaging path ignores per-purpose
                # visibility. These prims are guides only, so mirror the same
                # session opinion in native visibility for that renderer.
                imageable.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
                hidden.append(str(prim.GetPath()))
    if not hidden:
        raise AssertionError("Look-through sensor has no derived guides")
    stage.GetSessionLayer().Export(str(directory / "lookthrough.session.usda"))
    lookthrough = directory / "lookthrough.usda"
    stage.Flatten().Export(str(lookthrough))
    return {"overview": (overview, "/DemoOverview"), "lookthrough": (lookthrough, sensor_path)}, hidden


def render(stage_path, directory, sensor_path, *, prepared=None, render_env=None):
    """Render through the shared CPU renderer with the selected runtime."""
    from pxr import Sdf, Usd, UsdGeom
    from usdaeco_render import render as render_views
    inputs, hidden = prepared or render_inputs(stage_path, directory, sensor_path)
    if not shutil.which('usdrecord'):
        return dict(status='skipped',reason='usdrecord is unavailable',hiddenGuides=hidden)
    images = {}
    for name, (source, camera_path) in inputs.items():
        layer = Sdf.Layer.CreateNew(str(Path(directory) / (name + '.render.usda')))
        layer.subLayerPaths = [os.path.relpath(source, directory)]
        stage = Usd.Stage.Open(layer)
        base = Usd.Stage.Open(str(source))
        for key in ('defaultPrim','upAxis','metersPerUnit','fallbackPrimTypes'):
            if base.HasAuthoredMetadata(key): stage.SetMetadata(key,base.GetMetadata(key))
        sensor = UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
        camera = UsdGeom.Camera.Define(stage, '/Renders/' + name)
        value = sensor.GetCamera()
        value.transform = UsdGeom.Xformable(sensor).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        camera.SetFromCamera(value)
        layer.Save()
        records = render_views(layer.realPath, output=directory, views=[name], size=(640,400), purposes='guide,proxy,render')
        assert len(records) == 1
        images[name] = str(Path(directory) / (name + '.png'))
    return dict(status='pass',images=images,hiddenGuides=hidden)


def run_coverage(directory):
    from pxr import Usd
    from usdaeco_cctv.derive import derive_file
    from usdaeco_cctv.study import run_study
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    runner = scenario_runner()
    suite = runner.load_cases()
    kernel = coverage_kernel()
    model = directory / "lobby.usda"
    runner.open_copy(repos()["cctv"] / suite["example"]).GetRootLayer().Export(str(model))
    derived = directory / "analysis/cctv.derived.usda"
    stats = derive_file(model, derived)
    assert stats["sensors"] == 4 and not stats["skipped"], stats
    print(f"cctv derive: {stats['sensors']} sensors; {stats['sectors']} sectors; {stats['tours']} tour", flush=True)
    stage = Usd.Stage.Open(str(derived))
    study = run_study(stage, suite["studyPath"], directory / "analysis/cctv.DoorCoverage.usda", kernel=kernel)
    findings, errors, _ = runner.findings_of(stage)
    assert not findings and not errors, (findings, errors)
    assert len(study["results"]) == 3 and all(
        r["level"] == "identify" and r["fixedCoverage"] for r in study["results"].values())
    composed = Usd.Stage.CreateNew(str(directory / "stage.usda"))
    composed.GetRootLayer().subLayerPaths = ["./analysis/cctv.DoorCoverage.usda", "./analysis/cctv.derived.usda"]
    for name in ("defaultPrim", "upAxis", "metersPerUnit", "fallbackPrimTypes",
                 "timeCodesPerSecond", "framesPerSecond", "startTimeCode", "endTimeCode"):
        if stage.HasAuthoredMetadata(name):
            composed.SetMetadata(name, stage.GetMetadata(name))
    composed.GetRootLayer().Save()
    print(f"cctv study: 3 doors identify; fixed coverage; 0 findings ({kernel})", flush=True)
    cases = {case["id"]: case for case in suite["cases"]}
    steps_dir = directory / "steps"
    steps_dir.mkdir()
    done = {}
    for index, cid in enumerate(STEPS, 1):
        result = runner.run_case(cases[cid], suite, steps_dir, kernel, done)
        done[cid] = result
        print(f"cctv step {index}/6 {cid}: " + ("; ".join(
            f"{rule} ({severity}) @ {site}" for rule, severity, site in result["findings"]) or "no findings"), flush=True)
        for rule, severity, site in result["findings"]:
            print("  " + result["messages"][rule + "@" + site], flush=True)
        if not result["passed"]:
            raise AssertionError(result)
    rendered = render(directory / "stage.usda", directory / "renders", suite["root"] + "/Cam_1/Sensor_0")
    report = {"derive": stats, "study": runner.result_summary(study), "kernel": kernel,
              "steps": list(done.values()), "passed": len(done), "failed": 0,
              "render": rendered, "stage": str(directory / "stage.usda")}
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
