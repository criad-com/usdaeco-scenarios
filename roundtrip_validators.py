"""Exchange rules missing from individual library validators; profiles only grade."""
from pathlib import Path
from pxr import Sdf, Usd, UsdGeom, UsdValidation

KEYWORD = "AecoRoundtripValidators"
PATH_KINDS = {"IfcWall", "IfcWallStandardCase", "IfcPipeSegment", "IfcDuctSegment",
              "IfcCableCarrierSegment", "IfcBeam", "IfcColumn", "IfcMember"}
KINDS = {"IfcWall": "AecoWallAPI", "IfcWallStandardCase": "AecoWallAPI",
         "IfcPipeSegment": "AecoPipeAPI", "IfcPipeFitting": "AecoPipeFittingAPI",
         "IfcOpeningElement": "AecoOpeningAPI",
         "IfcAudioVisualAppliance": "AecoCctvCameraAPI"}


def issue(name, stage, path, message):
    return UsdValidation.ValidationError(name, UsdValidation.ValidationErrorType.Warn,
            [UsdValidation.ValidationErrorSite(stage, Sdf.Path(path))], message)


def structure(stage, time_range):
    result = []
    for prim in stage.TraverseAll():
        if not prim.IsActive():
            continue
        kind = (prim.GetAttribute("aeco:class:ifc:code").Get() or "").split(".")[0]
        if prim.HasAPI("AecoElementAPI") and kind in PATH_KINDS:
            if not prim.HasAPI("AecoAxisAPI") or any(
                prim.GetAttribute("aeco:axis:" + n).Get() is None for n in ("start", "end")):
                result.append(issue("roundtripAxisMissing", stage, prim.GetPath(), "Path element needs a readable core axis"))
        expected = KINDS.get(kind) if prim.HasAPI("AecoElementAPI") else None
        if kind == "IfcPipeSegmentType":
            expected = "AecoPipeTypeAPI"
        if kind in ("IfcWallType", "IfcWallStandardCaseType"):
            expected = "AecoBuildUpAPI"
        if prim.GetTypeName() == "AecoPort" and any(prim.GetParent().HasAPI(api)
                for api in ("AecoPipeAPI", "AecoPipeFittingAPI")):
            expected = "AecoPipePortAPI"
        if prim.GetTypeName() == "AecoSystem" and kind == "IfcDistributionSystem":
            members = prim.GetRelationship("collection:members:includes").GetTargets()
            if any(stage.GetPrimAtPath(p).HasAPI("AecoPipeAPI") for p in members if stage.GetPrimAtPath(p)):
                expected = "AecoPipeSystemAPI"
        if expected and not prim.HasAPI(expected):
            result.append(issue("roundtripKindMissing", stage, prim.GetPath(), "Required kind API: " + expected))
        if prim.HasAPI("AecoElementAPI") and (kind == "IfcAudioVisualAppliance" or prim.HasAPI("AecoCctvCameraAPI")):
            if not any(child.IsA(UsdGeom.Camera) and child.HasAPI("AecoCctvSensorAPI")
                       for child in prim.GetChildren()):
                result.append(issue("roundtripSensorMissing", stage, prim.GetPath(),
                                    "Camera element needs a Camera child with AecoCctvSensorAPI"))
        # Sync's binding rule already covers path and section APIs. Include
        # identity-bearing non-path elements (doors/openings) in this exchange.
        from aeco_sync.validators import SYNC_APIS
        if (prim.HasAPI("AecoElementAPI") or prim.GetTypeName() == "AecoPort") and not SYNC_APIS.intersection(prim.GetAppliedSchemas()):
            names = [s.split(":", 1)[1] for s in prim.GetAppliedSchemas() if s.startswith("AecoHostBindingAPI:")]
            if not any(prim.GetAttribute(f"aeco:host:{name}:ref").Get() for name in names):
                result.append(issue("BindingMissing", stage, prim.GetPath(), "Exchange element needs a populated host binding"))
    return result


def layer_order(stage, time_range):
    from aeco_sync.stack import all_specs
    from aeco_sync.edits import classify
    layers = stage.GetLayerStack()
    results = [i for i, layer in enumerate(layers)
               if Path(layer.realPath).name.startswith("result.") and Path(layer.realPath).suffix == ".usda"]
    if not results:
        return [issue("roundtripResultMissing", stage, "/", "A sync-able session must contain a result layer")]
    findings = []
    # Include anonymous session/root and nested editor layers; result layers
    # legitimately author derived properties even above other host results.
    for i, layer in enumerate(layers[:max(results)]):
        if i in results:
            continue
        for spec in all_specs(layer):
            prim = stage.GetPrimAtPath(spec.path)
            if not prim:
                continue
            for prop in spec.properties:
                if classify(prim, prop.name) == "derived":
                    findings.append(issue("derivedAboveResult", stage, prop.path,
                        "Derived opinion above result layers in " + (Path(layer.realPath).name or "session layer")))
            if prim.HasAPI("AecoDerivedGeometryAPI") and (spec.HasInfo("active") or spec.specifier == Sdf.SpecifierDef):
                findings.append(issue("derivedAboveResult", stage, spec.path, "Derived geometry authored above result layers"))
    return findings


def register():
    registry = UsdValidation.ValidationRegistry()
    known = {m.name for m in registry.GetValidatorMetadataForKeyword(KEYWORD)}
    for name, callback in (("Structure", structure), ("LayerOrder", layer_order)):
        name = "aecoRoundtrip:" + name
        if name not in known:
            registry.RegisterStageValidator(UsdValidation.ValidatorMetadata(
                name=name, keywords=[KEYWORD], doc=callback.__name__), callback)


def evaluate(stage, profile):
    from usdaeco_tools import validators as core
    from usdaeco_pipe import validators as pipe
    from usdaeco_wall import validators as wall
    from usdaeco_buildup import validators as buildup
    from usdaeco_cctv import validators as cctv
    from aeco_sync import validators as sync
    from usdaeco_pipe.profiles import load_profile, apply_profile
    data = load_profile(profile)
    keywords = []
    for module in (core, pipe, wall, buildup, cctv, sync):
        module.register()
        keywords.append(module.KEYWORD)
    register()
    keywords.append(KEYWORD)
    if data.get("include_builtin", True):
        keywords.append("UsdCoreValidators")
    registry = UsdValidation.ValidationRegistry()
    names = [m.name for k in keywords for m in registry.GetValidatorMetadataForKeyword(k)]
    issues = apply_profile(list(UsdValidation.ValidationContext(
        registry.GetOrLoadValidatorsByName(names)).Validate(stage)), data)
    rows = [{"rule": e.GetName(), "severity": str(e.GetType()).rsplit(".", 1)[-1].lower(),
             "message": e.GetMessage(), "sites": [str(s.GetProperty().GetPath() if s.IsProperty() else s.GetPrim().GetPath()) for s in e.GetSites()]} for e in issues]
    return {"errors": sum(e.GetType() == UsdValidation.ValidationErrorType.Error for e in issues),
            "warnings": sum(e.GetType() == UsdValidation.ValidationErrorType.Warn for e in issues),
            "findings": rows}
