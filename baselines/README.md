# Baseline builders

Run `env -u PYTHONPATH "$PYTHON" baselines/wallpipe.py wallpipe.ifc` or
`env -u PYTHONPATH "$PYTHON" baselines/wall_corner.py corner.ifc`.
Both require IfcOpenShell 0.8.5 and numpy, and produce IFC4X3 in metres.

`wallpipe.py` is copied unchanged from Sync's scenario builder; keep its API
compatible with `build(output)` when updating. The second builder adapts Wall's
synthetic import fixture with a third wall forming a T junction. It includes
one door with body geometry filling a real wall opening. Geometry and identity
are synthesized afresh; no external project input is needed.
