"""Security schedule and hall policy, graded together with all family validators."""
import json
from pathlib import Path
from pxr import Sdf, Usd, UsdGeom, UsdValidation

KEYWORD = 'AecoDatacentreValidators'
STUDIES = ('CriticalDoors', 'ExternalDoors', 'Corridors', 'Yards', 'YardsNight', 'Lobby', 'Privacy', 'RevitParity')
DESIGN_RULES = {'cctvTargetUncovered', 'cctvTargetTooFar', 'cctvPtzSoleCoverage', 'cctvExclusionCovered'}


def policy(stage, time_range=None):
    from roundtrip_validators import issue
    issues = []
    for name in STUDIES:
        prim = stage.GetPrimAtPath('/SecurityStudies/'+name)
        if not prim or not prim.IsActive() or not prim.HasAPI('AecoCctvStudyAPI'):
            issues.append(issue('dcStudyMissing', stage, '/', 'Required security study is missing: '+name))
    root = stage.GetPrimAtPath('/SecurityStudies')
    halls = root.GetRelationship('halls').GetTargets() if root else []
    bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'guide'])
    cache = UsdGeom.XformCache()
    for prim in stage.Traverse():
        if not prim.HasAPI('AecoCctvCameraAPI') or prim.GetAttribute('aeco:cctv:scenario').Get() == 'door':
            continue
        position = cache.GetLocalToWorldTransform(prim).ExtractTranslation()
        for path in halls:
            hall = stage.GetPrimAtPath(path)
            extent = next((p for p in hall.GetChildren() if p.GetAttribute('aeco:derived:role').Get()=='extent'), hall) if hall else None
            if hall and (prim.GetPath().HasPrefix(path) or bbox.ComputeWorldBound(extent).ComputeAlignedRange().Contains(position)):
                issues.append(issue('dcHallCamera', stage, prim.GetPath(), 'Only door cameras are permitted inside hall '+str(path)))
    return issues


def evaluate(stage, profile=None):
    from family import ROOT
    from usdaeco_tools import validators as core
    from usdaeco_pipe import validators as pipe
    from usdaeco_wall import validators as wall
    from usdaeco_buildup import validators as buildup
    from usdaeco_cctv import validators as cctv
    from aeco_sync import validators as sync
    from usdaeco_pipe.profiles import load_profile, apply_profile
    data = load_profile(profile or ROOT / 'profiles/datacentre.json')
    registry = UsdValidation.ValidationRegistry()
    name = 'aecoDatacentre:Policy'
    if not registry.GetValidatorMetadataForKeyword(KEYWORD):
        registry.RegisterStageValidator(UsdValidation.ValidatorMetadata(name=name, keywords=[KEYWORD], doc='Required schedule and hall camera policy'), policy)
    names = [name]
    for module in (core, pipe, wall, buildup, cctv, sync):
        module.register()
        names += [m.name for m in registry.GetValidatorMetadataForKeyword(module.KEYWORD)]
    if data.get('include_builtin', True):
        names += [m.name for m in registry.GetValidatorMetadataForKeyword('UsdCoreValidators')]
    issues = apply_profile(list(UsdValidation.ValidationContext(registry.GetOrLoadValidatorsByName(names)).Validate(stage)), data)
    findings = [dict(rule=e.GetName(), severity=str(e.GetType()).rsplit('.',1)[-1].lower(),
                     message=e.GetMessage(), sites=[str(s.GetProperty().GetPath() if s.IsProperty() else s.GetPrim().GetPath()) for s in e.GetSites()]) for e in issues]
    findings.sort(key=lambda x: (x['rule'], x['sites'], x['message']))
    return dict(findings=findings, errors=sum(f['severity']=='error' for f in findings),
                warnings=sum(f['severity']=='warn' for f in findings),
                designFindings=[f for f in findings if f['rule'] in DESIGN_RULES],
                implementationErrors=[f for f in findings if f['severity']=='error' and f['rule'] not in DESIGN_RULES])
