"""Explain residual targets from the study's saved per-view sample evidence."""
import json
from pathlib import Path

import numpy as np
from pxr import Sdf
from usdaeco_cctv.raycast import Scene
from usdaeco_cctv.study import Settings, enumerate_views, gather_obstacles, target_points


def residual_samples(stage, reports, kernel):
    evidence = {}
    for name, report in reports.items():
        selected = {p: r for p, r in report['results'].items()
                    if not r['fixedCoverage'] or any(Path(b).name.startswith('col_') for b in r['blockers'])}
        if not selected:
            continue
        settings = Settings(stage.GetPrimAtPath('/SecurityStudies/' + name))
        owners, triangles, indices = gather_obstacles(stage, settings)
        scene = Scene(triangles, indices, kernel, groups=settings.gprim_groups)
        transparent = {o.index for o in owners if o.through}
        views, _ = enumerate_views(stage, settings)
        layer = Sdf.Layer.FindOrOpen(report['layer'])
        saved = {key: json.loads(value['cache'])
                 for key, value in layer.customLayerData['aeco:cctv:views'].items()}
        targets = {}
        for path, result in selected.items():
            points = target_points(stage, stage.GetPrimAtPath(path))
            enclosed = scene.enclosed(points, skip=transparent)
            evaluated_indices = np.flatnonzero(~enclosed if settings.excludeEnclosedSamples
                                               else np.ones(len(points), dtype=bool))
            assert len(points) == result['sampleCount']
            assert int(enclosed.sum()) == result['enclosedSamples']
            assert len(evaluated_indices) == result['evaluatedSamples']
            fixed, union = np.zeros(len(evaluated_indices), bool), np.zeros(len(evaluated_indices), bool)
            column_samples = []
            for view in views:
                entry = saved[view.id]['targets'].get(path)
                if not entry:
                    continue
                assert len(entry['points']) == len(evaluated_indices)
                union |= entry['points']
                if not view.motorised:
                    fixed |= entry['points']
                if entry.get('blocker') and Path(entry['blocker']).name.startswith('col_'):
                    column_samples.append(dict(view=view.id, blocker=entry['blocker'],
                                               sampleIndex=int(evaluated_indices[0]),
                                               point=points[evaluated_indices[0]].tolist()))
            assert abs(float(union.mean()) - result['fraction']) < 1e-12
            missing = []
            for sample_index in evaluated_indices[~fixed]:
                point = points[sample_index:sample_index + 1]
                observations = []
                for view in views:
                    if view.motorised or not view.frustum.contains(point)[0]:
                        continue
                    skip = transparent | {o.index for o in owners
                                          if o.path in (view.camera.GetPath(), Sdf.Path(path))
                                          or o.element in (view.camera.GetPath(), Sdf.Path(path))}
                    blocked, blocker, _ = scene.occlusion(view.origin, point, skip)
                    observations.append(dict(view=view.id,
                        density=view.density(float(np.linalg.norm(point[0] - view.origin)), settings.densityModel),
                        requiredDensity=result['required'],
                        blocker=str(owners[int(blocker[0])].path) if blocked[0] and blocker[0] >= 0 else None))
                missing.append(dict(sampleIndex=int(sample_index), point=point[0].tolist(), fixedViews=observations))
            targets[path] = dict(sampleCount=len(points), enclosedSamples=int(enclosed.sum()),
                enclosedPoints=[dict(sampleIndex=int(i), point=points[i].tolist()) for i in np.flatnonzero(enclosed)],
                evaluatedSamples=len(evaluated_indices), fixedCoveredSamples=int(fixed.sum()),
                uncoveredFixedSamples=missing, columnBlockedPrimarySamples=column_samples)
        evidence[name] = targets
    return evidence
