"""Independent driver edits on the generated facility; baseline stays untouched."""
from pathlib import Path
import os
import uuid

from pxr import Gf, Sdf, Usd, UsdGeom
from usdaeco_cctv.study import run_study
from usdaeco_cctv import validators as checks

SENSOR = 'aeco:cctvSensor:'
STUDY = 'aeco:cctvStudy:'
TARGET = 'aeco:cctvTarget:'


def codes(stage, name):
    prim = stage.GetPrimAtPath('/SecurityStudies/'+name)
    findings = [e for fn in (checks._missing_results, checks._incomplete, checks._stale, checks._uncovered,
                            checks._ptz_sole, checks._too_far, checks._exclusion_covered)
                for e in fn(prim, None)]
    return [dict(rule=e.GetName(), message=e.GetMessage(), sites=[str(s.GetPrim().GetPath()) for s in e.GetSites()]) for e in findings]


def camera(stage, name):
    return next(p for p in stage.Traverse() if p.HasAPI('AecoCctvCameraAPI') and p.GetName()==name.replace('.','_'))


def snapshot(stage, output, result=None):
    """Persist driver edits and a portable composed case for independent review."""
    output=Path(output)
    layer=Sdf.Layer.CreateAnonymous('case-drivers.usda')
    layer.TransferContent(stage.GetSessionLayer())
    layer.subLayerPaths=[]
    drivers=output.with_suffix('.drivers.usda');layer.Export(str(drivers))
    composed=Usd.Stage.CreateNew(str(output.with_suffix('.stage.usda')))
    base=Path(stage.GetRootLayer().realPath)
    composed.GetRootLayer().subLayerPaths=[drivers.name]+([Path(result).name] if result else [])+[os.path.relpath(base,output.parent)]
    for field in ('metersPerUnit','upAxis','fallbackPrimTypes','defaultPrim','timeCodesPerSecond','startTimeCode','endTimeCode'):
        if stage.HasAuthoredMetadata(field):composed.SetMetadata(field,stage.GetMetadata(field))
    composed.GetRootLayer().Save()


def study(stage, name, output, kernel):
    result=run_study(stage, '/SecurityStudies/'+name, output, kernel=kernel)
    snapshot(stage,output,result=output)
    return result


def run_cases(stage_path, directory, kernel):
    directory=Path(directory); directory.mkdir(parents=True, exist_ok=True)
    rows=[]
    def fresh(results=False):
        stage=Usd.Stage.Open(str(stage_path if results else Path(stage_path).with_name("schedule.usda")))
        stage.SetEditTarget(stage.GetSessionLayer())
        return stage
    def row(cid, ok, **evidence):
        print('== stage: '+cid+': '+('PASS' if ok else 'FAIL'),flush=True)
        rows.append(dict(gate=cid,passed=bool(ok),status='PASS' if ok else 'FAIL',evidence=evidence))
    # Lower a real source tray and require a newly lost, attributed sightline.
    stage=fresh()
    tray_before=study(stage,'CriticalDoors',directory/'tray-before.usda',kernel)
    stage.SetEditTarget(stage.GetSessionLayer())
    trays=[p for p in stage.Traverse() if p.HasAPI('AecoElementAPI') and 'Spine' in p.GetName() and 'IfcCableCarrierSegment' in (p.GetAttribute('aeco:class:ifc:code').Get() or '')]
    tray=sorted(trays,key=lambda p:str(p.GetPath()))[0]
    matrix=UsdGeom.Xformable(tray).GetLocalTransformation()
    matrix.SetTranslateOnly(matrix.ExtractTranslation()+Gf.Vec3d(0,0,-.9))
    UsdGeom.Xformable(tray).MakeMatrixXform().Set(matrix)
    r=study(stage,'CriticalDoors',directory/'tray.usda',kernel)
    lost=[path for path,value in r['results'].items()
          if tray_before['results'][path]['fixedCoverage'] and not value['fixedCoverage']]
    row('DC-tray',all(v['fixedCoverage'] for v in tray_before['results'].values()) and bool(lost)
        and all(str(tray.GetPath()) in r['results'][path]['blockers'] for path in lost),
        tray=str(tray.GetPath()), loweredMetres=.9, beforeFixedCovered=11,
        afterFixedCovered=sum(v['fixedCoverage'] for v in r['results'].values()),
        lostTargets={path:r['results'][path] for path in lost}, findings=codes(stage,'CriticalDoors'))
    # A hoarding across the loading approach, excluded and included by phase.
    stage=fresh()
    before=study(stage,'ExternalDoors',directory/'temporary-before.usda',kernel)
    target='/SecurityTargets/door_dock'
    assert before['results'][target]['fixedCoverage']
    box=UsdGeom.Cube.Define(stage,'/ScenarioEdits/LoadingHoarding')
    box.CreateSizeAttr(1.)
    box.AddTranslateOp().Set(Gf.Vec3d(57.,-1.25,1.8))
    box.AddScaleOp().Set(Gf.Vec3f(4.,.15,3.6))
    prim=box.GetPrim();prim.ApplyAPI('AecoElementAPI')
    prim.GetAttribute('aeco:id').Set(str(uuid.uuid5(uuid.NAMESPACE_DNS,'usdaeco-datacentre:scenario.hoarding')))
    prim.GetAttribute('aeco:phase').Set('temporary')
    prim.ApplyAPI('AecoClassificationAPI','ifc')
    prim.GetAttribute('aeco:class:ifc:code').Set('IfcBuildingElementProxy')
    ignored=study(stage,'ExternalDoors',directory/'temporary-ignored.usda',kernel)
    stage.SetEditTarget(stage.GetSessionLayer())
    stage.GetPrimAtPath('/SecurityStudies/ExternalDoors').GetAttribute(STUDY+'phases').Set(['existing','proposed','temporary'])
    included=study(stage,'ExternalDoors',directory/'temporary-included.usda',kernel)
    row('DC-temporary',ignored['results']==before['results'] and not included['results'][target]['views']
        and str(prim.GetPath()) in included['results'][target]['blockers'],
        ignoredFraction=ignored['results'][target]['fraction'], includedFraction=included['results'][target]['fraction'],
        blocker=str(prim.GetPath()), findings=codes(stage,'ExternalDoors'))
    # A real corridor camera moved inside a hall violates both geometry/privacy and placement policy.
    stage=fresh();cam=camera(stage,'sec.cam.corr.corr.w.1')
    parent=UsdGeom.XformCache().GetLocalToWorldTransform(cam.GetParent())
    local=Gf.Matrix4d().SetTranslate(Gf.Vec3d(5.,19.,2.9))*parent.GetInverse()
    UsdGeom.Xformable(cam).MakeMatrixXform().Set(local)
    cam.GetChild('Sensor_0').GetAttribute(SENSOR+'pan').Set(20.)
    privacy=stage.GetPrimAtPath('/SecurityStudies/Privacy')
    Usd.CollectionAPI(privacy,'cameras').GetIncludesRel().SetTargets([cam.GetPath()])
    r=study(stage,'Privacy',directory/'privacy.usda',kernel)
    findings=codes(stage,'Privacy')
    row('DC-privacy',bool(r['exclusionsCovered']) and any(f['rule']=='cctvExclusionCovered' and len(f['sites'])>=3 for f in findings),
        findings=findings, camera=str(cam.GetPath()), exclusions=r['exclusionsCovered'], panDegrees=20.)
    from datacentre_validators import policy
    hall=[e for e in policy(stage) if e.GetName()=='dcHallCamera']
    row('DC-hall-rule',bool(hall), errors=len(hall), camera=str(cam.GetPath()))
    # NOC is monitored by contract; a turn toward it cannot itself be a privacy defect.
    stage=fresh();cam=camera(stage,'sec.cam.corr.ocorr.0.1')
    sensor=cam.GetChild('Sensor_0');sensor.GetAttribute(SENSOR+'pan').Set(sensor.GetAttribute(SENSOR+'pan').Get()+20.)
    row('DC-noc-turn',not any('noc' in str(p).lower() for p in stage.GetPrimAtPath('/SecurityStudies/Privacy').GetRelationship('collection:exclusions:includes').GetTargets()),
        panDelta=20., limitation='NOC monitoring is allowed. Privacy-error demonstration uses a hall intrusion instead.')
    # Remove the actual main-door dome, retaining the other dome and all
    # original lobby targets, thresholds, points and PTZ presets.
    stage=fresh();prim=stage.GetPrimAtPath('/SecurityStudies/Lobby')
    baseline=study(stage,'Lobby',directory/'duty-before.usda',kernel)
    target='/SecurityTargets/lobby_door_main'
    stage.SetEditTarget(stage.GetSessionLayer())
    dome=camera(stage,'sec.cam.lobby.fixed.2');removed=str(dome.GetPath())
    dome.SetActive(False)
    r=study(stage,'Lobby',directory/'duty.usda',kernel)
    value=r['results'][target];findings=codes(stage,'Lobby')
    row('DC-ptz-duty',baseline['results'][target]['fixedCoverage'] and value['fraction']==1.
        and abs(value['dutyFraction']-2/3)<1e-12 and not value['fixedCoverage']
        and value['views']==[str(camera(stage,'sec.cam.lobby').GetChild('Sensor_0').GetPath())]
        and any(f['rule']=='cctvPtzSoleCoverage' and target in f['sites'] for f in findings),
        removedCamera=removed, target=target, beforeFixedCoverage=baseline['results'][target]['fixedCoverage'],
        afterFixedCoverage=value['fixedCoverage'], sampleCount=value['sampleCount'], enclosedSamples=value['enclosedSamples'],
        fraction=value['fraction'], dutyFraction=value['dutyFraction'], expectedDuty=2/3, findings=findings)
    # IR overrides must affect both the effective hash and the result.
    stage=fresh();cam=camera(stage,'sec.cam.ext.dock')
    cam.CreateAttribute('aeco:cctvType:irRange',Sdf.ValueTypeNames.Double).Set(.1)
    r=study(stage,'ExternalDoors',directory/'night.usda',kernel)
    row('DC-night-override',r['inputHash']!=before['inputHash'] and not r['results']['/SecurityTargets/door_dock']['views'],
        irMetres=.1, fraction=r['results']['/SecurityTargets/door_dock']['fraction'], findings=codes(stage,'ExternalDoors'))
    stage=fresh(results=True);cam=camera(stage,'sec.cam.door.hall.a.w');sensor=cam.GetChild('Sensor_0')
    sensor.GetAttribute(SENSOR+'pan').Set(sensor.GetAttribute(SENSOR+'pan').Get()+20.)
    snapshot(stage,directory/'stale.usda')
    findings=codes(stage,'CriticalDoors')
    row('DC-stale',any(f['rule']=='cctvStudyStale' for f in findings),findings=[f for f in findings if f['rule']=='cctvStudyStale'])
    stage=fresh(results=True);result=next(stage.GetPrimAtPath('/SecurityStudies/CriticalDoors/Results').GetChildren().__iter__())
    result.SetActive(False);snapshot(stage,directory/'incomplete.usda');findings=codes(stage,'CriticalDoors')
    row('DC-results-incomplete',any(f['rule']=='cctvStudyIncomplete' for f in findings),findings=[f for f in findings if f['rule']=='cctvStudyIncomplete'])
    return rows
