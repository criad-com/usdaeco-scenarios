"""Camera exchange contracts and the portable coverage demo outputs."""
import hashlib
from pathlib import Path

import pytest
from pxr import Sdf, Usd, UsdGeom

from family import ROOT, environment, repos
from roundtrip_validators import evaluate


def camera_stage():
    stage = Usd.Stage.CreateInMemory()
    camera = UsdGeom.Xform.Define(stage, "/Camera").GetPrim()
    camera.ApplyAPI("AecoElementAPI")
    camera.GetAttribute("aeco:id").Set("camera-fixture")
    camera.ApplyAPI("AecoClassificationAPI", "ifc")
    camera.GetAttribute("aeco:class:ifc:code").Set("IfcAudioVisualAppliance.CAMERA")
    return stage, camera


def errors(stage):
    return {f["rule"] for f in evaluate(stage, ROOT / "profiles/roundtrip.json")["findings"]
            if f["severity"] == "error"}


def test_classified_camera_requires_kind_and_sensor():
    stage, camera = camera_stage()
    assert {"roundtripKindMissing", "roundtripSensorMissing"} <= errors(stage)
    camera.ApplyAPI("AecoCctvCameraAPI")
    assert "roundtripKindMissing" not in errors(stage)
    sensor = UsdGeom.Camera.Define(stage, "/Camera/Sensor_0").GetPrim()
    sensor.ApplyAPI("AecoCctvSensorAPI")
    assert "roundtripSensorMissing" not in errors(stage)


@pytest.mark.parametrize("defect", ["no_api", "mesh", "inactive", "nested"])
def test_sensor_requires_active_camera_child_with_api(defect):
    stage, camera = camera_stage()
    camera.ApplyAPI("AecoCctvCameraAPI")
    sensor = stage.DefinePrim("/Camera/Head/Sensor_0" if defect == "nested" else "/Camera/Sensor_0",
                             "Mesh" if defect == "mesh" else "Camera")
    if defect != "no_api":
        sensor.ApplyAPI("AecoCctvSensorAPI")
    if defect == "inactive":
        sensor.SetActive(False)
    assert "roundtripSensorMissing" in errors(stage)


def test_inherited_sensor_satisfies_exchange():
    stage, camera = camera_stage()
    camera.ApplyAPI("AecoCctvCameraAPI")
    stage.CreateClassPrim("/_TypeCatalog/CameraType")
    sensor = UsdGeom.Camera.Define(stage, "/_TypeCatalog/CameraType/Sensor_0").GetPrim()
    sensor.ApplyAPI("AecoCctvSensorAPI")
    camera.GetInherits().AddInherit("/_TypeCatalog/CameraType")
    assert "roundtripSensorMissing" not in errors(stage)


def test_native_camera_edit_is_hardened_by_roundtrip_profile():
    stage, camera = camera_stage()
    camera.ApplyAPI("AecoCctvCameraAPI")
    sensor = UsdGeom.Camera.Define(stage, "/Camera/Sensor_0")
    sensor.GetPrim().ApplyAPI("AecoCctvSensorAPI")
    sensor.CreateFocalLengthAttr(9)
    assert "cctvNativeCameraAuthored" in errors(stage)


def test_family_excludes_opt_in_real_data(monkeypatch):
    monkeypatch.setenv("AECO_PRIVATE_FIXTURE_ROOT", "/private-fixture")
    monkeypatch.setenv("PYTHONPATH", "/foreign-python")
    env = environment()
    assert "AECO_PRIVATE_FIXTURE_ROOT" not in env and "PYTHONPATH" not in env
    assert env["CCTV_PLUGIN_DIR"] == str(repos()["cctv"] / "usdAecoCctv")


def test_import_folds_handles_into_bindings_with_seven_plugins(tmp_path):
    import importlib.util
    from pxr import Plug
    from family import LIBRARIES, repos
    from usdaeco_cctv import iter_cameras, sensors_of
    from usdaeco_cctv.importer import import_cctv
    assert {p.name for p in Plug.Registry().GetAllPlugins() if p.name.startswith("usdAeco") and not p.name.endswith("Validators")} == set(LIBRARIES.values())
    spec = importlib.util.spec_from_file_location("cctv_import_fixtures", repos()["cctv"] / "testenv/fixtures.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    native, core, kind = [tmp_path / name for name in ("fixture.ifc", "core.usda", "kind.usda")]
    fixture.build_baseline(native)
    fixture.convert(native, core)
    stats = import_cctv(core, native, kind)
    assert stats == dict(cameras=3, sensors=6, presets=2, types=3, propsBlocked=137,
                         subInstancesFolded=2, unmatched=0)
    stage = Usd.Stage.Open(str(kind))
    sensors = [s for camera in iter_cameras(stage) for s in sensors_of(camera)]
    refs = [s.GetAttribute("aeco:host:revit:ref").Get() for s in sensors
            if s.HasAPI("AecoHostBindingAPI", "revit")]
    assert len(refs) == len(set(refs)) == 2
    assert {ref.split(":")[1] for ref in refs} == {"fov", "symbol"}
    assert sum(p.HasAPI("AecoElementAPI") for p in stage.Traverse()) == 4
    assert all(not s.GetAttribute("aeco:id").HasAuthoredValueOpinion() for s in sensors)


@pytest.fixture(scope="module")
def coverage(tmp_path_factory):
    from demo import coverage as demo
    # The unattended demo renders; these tests verify the portable inputs
    # independently, without spending another two image renders per gate.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(demo, "render", lambda *args: {"status": "skipped", "reason": "render inputs tested separately"})
        return demo.run_coverage(tmp_path_factory.mktemp("coverage") / "demo")


def test_six_steps_preserve_shipped_findings(coverage):
    from demo.coverage import STEPS
    assert [step["id"] for step in coverage["steps"]] == list(STEPS)
    assert all(step["passed"] for step in coverage["steps"])
    tray = next(step for step in coverage["steps"] if step["id"] == "V-tray")
    assert tray["results"]["Door_1"]["dutyFraction"] == .375
    assert {row[0] for row in tray["findings"]} == {"cctvPtzSoleCoverage", "cctvTargetTooFar"}


def test_lookthrough_hides_only_own_guides_without_changing_stage(coverage, tmp_path):
    from demo.coverage import render_inputs
    stage_path = Path(coverage["stage"])
    source_stage = Usd.Stage.Open(str(stage_path))
    sources = [Path(layer.realPath) for layer in source_stage.GetLayerStack()
               if layer.realPath]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    sensor = "/CctvLobby/Site/Building/L0/Lobby/Cam_1/Sensor_0"
    inputs, hidden = render_inputs(stage_path, tmp_path, sensor)
    assert hidden and all(path.startswith(sensor + "/") for path in hidden)
    overview = Usd.Stage.Open(str(inputs["overview"][0]))
    lookthrough = Usd.Stage.Open(str(inputs["lookthrough"][0]))
    for path in hidden:
        assert lookthrough.GetPrimAtPath(path).GetAttribute("guideVisibility").Get() == "invisible"
        assert lookthrough.GetPrimAtPath(path).GetAttribute("visibility").Get() == "invisible"
        assert overview.GetPrimAtPath(path).GetAttribute("guideVisibility").Get() != "invisible"
    other = lookthrough.GetPrimAtPath(sensor.replace("Cam_1", "Cam_2") + "/Sector")
    assert other and other.GetAttribute("guideVisibility").Get() != "invisible"
    assert other.GetAttribute("visibility").Get() != "invisible"
    assert Sdf.Layer.FindOrOpen(str(tmp_path / "lookthrough.session.usda")).GetPrimAtPath(hidden[0])
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}


def test_coverage_composes_in_vanilla_runtime(coverage):
    import os
    import subprocess
    import sys
    probe = '''import sys
from pxr import Plug, Usd, UsdGeom
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
stage = Usd.Stage.Open(sys.argv[1])
assert stage and not stage.GetCompositionErrors() and stage.Flatten()
assert sum(p.IsA(UsdGeom.Camera) for p in stage.Traverse()) == 4
fallbacks = stage.GetMetadata('fallbackPrimTypes')
assert all(p.GetTypeName() in fallbacks for p in stage.Traverse() if p.GetTypeName().startswith('Aeco'))
assert not any(p.name.startswith('usdAeco') for p in Plug.Registry().GetAllPlugins())
'''
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PXR_PLUGINPATH_NAME", "PXR_AR_DEFAULT_SEARCH_PATH")}
    subprocess.run([sys.executable, "-c", probe, coverage["stage"]], env=env, check=True, timeout=30)
