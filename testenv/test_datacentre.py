"""Security profile, explicit sampling, source drift and deterministic evidence."""
import json
from pathlib import Path
import pytest
from pxr import Gf,Sdf,Usd,UsdGeom
from family import ROOT,environment,repos
from demo.datacentre import scenario_module
from datacentre_validators import evaluate,policy,STUDIES

@pytest.fixture(scope='module')
def dc():
    return scenario_module()


def test_security_profile_keeps_release_errors():
    profile=json.loads((ROOT/'profiles/datacentre.json').read_text())
    for name in ('dcStudyMissing','dcHallCamera','cctvStudyMissingResults','cctvStudyIncomplete','cctvStudyStale',
                 'cctvTargetUncovered','cctvPtzSoleCoverage','cctvExclusionCovered','cctvTargetTooFar'):
        assert profile['severity_overrides'][name]=='error'
    assert profile['severity_overrides']['cctvTargetMostlyEnclosed']=='warn'


def test_absent_and_never_run_schedule_are_errors():
    stage=Usd.Stage.CreateInMemory()
    findings=evaluate(stage)['implementationErrors']
    assert sum(f['rule']=='dcStudyMissing' for f in findings)==len(STUDIES)
    for name in STUDIES:
        stage.DefinePrim('/SecurityStudies/'+name,'Scope').ApplyAPI('AecoCctvStudyAPI')
    findings=evaluate(stage)['implementationErrors']
    assert not any(f['rule']=='dcStudyMissing' for f in findings)
    assert sum(f['rule']=='cctvStudyMissingResults' for f in findings)==len(STUDIES)


def test_hall_rule_uses_world_location_and_scenario():
    stage=Usd.Stage.CreateInMemory();root=stage.DefinePrim('/SecurityStudies','Scope')
    hall=UsdGeom.Cube.Define(stage,'/Hall');hall.CreateSizeAttr(10.)
    root.CreateRelationship('halls').SetTargets(['/Hall'])
    camera=UsdGeom.Xform.Define(stage,'/Camera').GetPrim();camera.ApplyAPI('AecoCctvCameraAPI')
    camera.GetAttribute('aeco:cctv:scenario').Set('corridor')
    assert any(f.GetName()=='dcHallCamera' for f in policy(stage))
    camera.GetAttribute('aeco:cctv:scenario').Set('door')
    assert not any(f.GetName()=='dcHallCamera' for f in policy(stage))


@pytest.mark.parametrize('normal,axis,sign',[('+X',0,1),('-X',0,-1),('+Y',1,1),('-Y',1,-1)])
def test_door_grid_samples_approach_face(dc,normal,axis,sign):
    points=dc.door_points(dict(approach_normal=normal,centre=[0,0,1.6],width=1.8,height=2.1))
    assert len(points)>40
    assert all(abs(p[axis]-.15*sign)<1e-9 and .3<=p[2]<2.1 for p in points)


def test_corridor_grid_spacing_and_density_are_explicit(dc):
    points=dc.grid_points([[0,0,0],[2,1,0]],spacing=.5)
    assert len(points)==8
    assert sorted(set(p[0] for p in points))==[.25,.75,1.25,1.75]
    assert all(p[2]==1.5 for p in points)


def test_determinism_ignores_only_clock_metadata(dc):
    a=Usd.Stage.CreateInMemory();p=UsdGeom.Xform.Define(a,'/Camera')
    a.GetRootLayer().customLayerData={'aeco:cctv:time':'first','semantic':'same'}
    before=dc.semantic_digest(a)
    a.GetRootLayer().customLayerData={'aeco:cctv:time':'second','semantic':'same'}
    assert dc.semantic_digest(a)==before
    p.AddTranslateOp().Set(Gf.Vec3d(1,0,0))
    assert dc.semantic_digest(a)!=before


def test_all_source_roots_override_ambient_values(monkeypatch):
    monkeypatch.setenv('AECO_CCTV_ROOT','wrong')
    monkeypatch.setenv('AECO_DATACENTRE_ROOT','wrong')
    env=environment()
    assert 'PYTHONPATH' not in env
    for name,path in repos().items():
        assert env['AECO_'+name.upper().replace('-', '_')+'_ROOT']==str(path)


def test_sanitization_covers_asset_metadata(tmp_path):
    from sanitization import scan
    path=tmp_path/'asset.json'
    path.write_text(json.dumps({'metadata':{'device':':'.join(['ab','cd','ef','01','23','45'])}}))
    assert not scan([path])['passed']
    path.write_text('{"facility":"demo-datacentre-01"}')
    assert scan([path])['passed']


@pytest.mark.parametrize('type_name,value,valid', [
    (Sdf.ValueTypeNames.String, 'NEW', True),
    (Sdf.ValueTypeNames.StringArray, ['NEW'], False),
])
def test_raw_validation_preserves_conversion_and_refuses_type_conflicts(dc,tmp_path,type_name,value,valid):
    sem=Usd.Stage.CreateNew(str(tmp_path/'core.semantics.usda'))
    typ=sem.CreateClassPrim('/Type')
    typ.CreateAttribute('aeco:props:Common:Status',type_name,custom=True).Set(value)
    prim=sem.DefinePrim('/Element','Xform')
    prim.CreateAttribute('aeco:props:Common:Status',Sdf.ValueTypeNames.String,custom=True).Set('NEW')
    prim.GetInherits().AddInherit('/Type')
    sem.GetRootLayer().Save()
    root=Sdf.Layer.CreateNew(str(tmp_path/'core.usda'));root.subLayerPaths=['core.semantics.usda'];root.defaultPrim='Element';root.Save()
    raw=(tmp_path/'core.semantics.usda').read_bytes()
    if valid:
        assert dc.validate_raw_conversion(tmp_path/'core.usda') == dict(
            builtinErrors=0,builtinTypeErrors=0,compositionErrors=0)
    else:
        with pytest.raises(RuntimeError,match='Raw conversion failed validation'):
            dc.validate_raw_conversion(tmp_path/'core.usda')
    assert (tmp_path/'core.semantics.usda').read_bytes()==raw
    assert {p.name for p in tmp_path.iterdir()} == {'core.usda','core.semantics.usda'}


@pytest.mark.parametrize('change', ['none','extra-blocker','different-target','different-study',
                                   'different-view','lost-coverage','changed-samples','missing-manifest',
                                   'invalid-manifest','unproven-dedicated-views'])
def test_column_exception_requires_exact_released_evidence(dc,tmp_path,change):
    import copy
    source=ROOT/'testenv/fixtures/column-view-exception.json'
    manifest=json.loads(source.read_text())
    studies={'Corridors': {'results': copy.deepcopy(manifest['originalResults'])}}
    results=studies['Corridors']['results']; target=next(iter(results)); result=results[target]
    if change=='extra-blocker': result['blockers'].append('/Model/col_999')
    if change=='different-target': results['/SecurityTargets/another']=results.pop(target)
    if change=='different-study': studies['CriticalDoors']=studies.pop('Corridors')
    if change=='different-view':
        result['viewNotes']=[s.replace('spine_4','spine_9').replace('spine_5','spine_9') for s in result['viewNotes']]
    if change=='lost-coverage': result.update(fixedCoverage=False,fraction=.8)
    if change=='changed-samples': result['sampleCount']-=1
    if change=='invalid-manifest': manifest={}
    if change=='unproven-dedicated-views': manifest['results'][target]['fixedCoverage']=False
    path=tmp_path/'exception.json'
    if change!='missing-manifest': path.write_text(json.dumps(manifest))
    evidence=dc.column_exception(studies,path)
    assert evidence['matched'] == (change=='none')
    assert evidence['note']


def test_png_content_reader_needs_no_imaging_wheel(tmp_path):
    import struct,zlib
    from demo.png import pixels
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    p=tmp_path/'content.png'
    p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,1,8,2,0,0,0))
                  +chunk(b'IDAT',zlib.compress(bytes([0,255,0,0,0,255,0])))+chunk(b'IEND',b''))
    assert pixels(p).tolist()==[[[1.,0.,0.],[0.,1.,0.]]]


def test_pin_drift_stops_before_build(monkeypatch,tmp_path):
    import family
    (tmp_path / '.git').mkdir()
    monkeypatch.setenv('AECO_CCTV_SOURCE', str(tmp_path))
    monkeypatch.setattr(family,'ensure_sources',lambda:None)
    monkeypatch.setattr(family,'repos',lambda **kwargs:{'cctv':tmp_path})
    calls=[]
    def command(argv,**kwargs):
        calls.append(argv)
        assert argv[0]=='git', 'A build ran before the source audit completed'
        if argv[1] == 'rev-parse':
            return 'unreviewed-revision' if argv[-1] == 'HEAD' else 'a' * 40
        return ''
    monkeypatch.setattr(family,'run',command)
    with pytest.raises(RuntimeError,match='Source pin audit failed: cctv'):
        family.build_plugins(tmp_path/'build')
    assert calls


def test_normalization_sorts_declarations_but_preserves_authored_order(dc):
    a,b=Usd.Stage.CreateInMemory(),Usd.Stage.CreateInMemory()
    for name in ['Second','First']:a.DefinePrim('/Root/'+name,'Xform')
    for name in ['First','Second']:b.DefinePrim('/Root/'+name,'Xform')
    assert dc.semantic_digest(a)==dc.semantic_digest(b)
    a.GetPrimAtPath('/Root').SetChildrenReorder(['Second','First'])
    assert dc.semantic_digest(a)!=dc.semantic_digest(b)


def test_privacy_tiles_preserve_every_sample(dc):
    points=dc.grid_points([[-10,-10,0],[10,10,0]],spacing=1.,inset=.3)
    tiles=dc.spatial_tiles(points)
    assert len(tiles)>1
    assert sorted(tuple(p) for group in tiles for p in group)==sorted(map(tuple,points))
    assert all(max(p[0] for p in group)-min(p[0] for p in group)<4 for group in tiles)


def test_case_snapshot_keeps_driver_edits_in_a_portable_layer(tmp_path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('case_snapshot',ROOT/'scenarios/dc_cases.py')
    cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
    stage=Usd.Stage.CreateNew(str(tmp_path/'base.usda'))
    cube=UsdGeom.Cube.Define(stage,'/Object');UsdGeom.SetStageMetersPerUnit(stage,1.)
    stage.GetRootLayer().Save();before=(tmp_path/'base.usda').read_bytes()
    with Usd.EditContext(stage,stage.GetSessionLayer()):
        cube.AddTranslateOp().Set(Gf.Vec3d(1,2,3))
    cases.snapshot(stage,tmp_path/'edited.usda')
    reopened=Usd.Stage.Open(str(tmp_path/'edited.stage.usda'))
    assert UsdGeom.Xformable(reopened.GetPrimAtPath('/Object')).GetLocalTransformation().ExtractTranslation()==Gf.Vec3d(1,2,3)
    assert (tmp_path/'base.usda').read_bytes()==before
    assert all(not Path(p).is_absolute() for p in reopened.GetRootLayer().subLayerPaths)
