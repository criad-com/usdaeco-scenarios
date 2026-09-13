"""Headless ifcopenshell spike: what happens to joined walls and port-connected
pipes when one element is extended or moved, and what an adapter must do."""
import argparse
import math, time, logging, io
import numpy as np
import ifcopenshell, ifcopenshell.api, ifcopenshell.geom, ifcopenshell.validate
import ifcopenshell.util.placement as up, ifcopenshell.util.shape as ush
import ifcopenshell.util.representation as urep, ifcopenshell.util.element as uel
import ifcopenshell.util.system as usys
from ifcopenshell.util.shape_builder import ShapeBuilder
from ifcopenshell.api import run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True, help="Destination IFC file")
args = parser.parse_args()

f = ifcopenshell.file(schema="IFC4X3")
run("root.create_entity", f, ifc_class="IfcProject", name="Spike")
run("unit.assign_unit", f, length={"is_metric": True, "raw": "METERS"})
model = run("context.add_context", f, context_type="Model")
body = run("context.add_context", f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model)
plan = run("context.add_context", f, context_type="Plan")
axis = run("context.add_context", f, context_type="Plan", context_identifier="Axis", target_view="GRAPH_VIEW", parent=plan)
builder = ShapeBuilder(f)
settings = ifcopenshell.geom.settings()

def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)

def placement(p, ang=0.0):
    m = np.eye(4); m[:3, :3] = rotz(ang); m[:3, 3] = p; return m

def shape_info(el):
    sh = ifcopenshell.geom.create_shape(settings, el)
    v = ush.get_shape_vertices(sh, sh.geometry)
    mn, mx = ush.get_bbox(v)
    return f"bbox {np.round(mn,3).tolist()}..{np.round(mx,3).tolist()} vol {ush.get_volume(sh.geometry):.4f} verts {len(v)}"

def world(el):
    return up.get_local_placement(el.ObjectPlacement)

# ------------------------------------------------------------------ walls
block = run("material.add_material", f, name="Block")
def make_wall(name, p1, p2, thickness=0.2, height=2.4):
    wall = run("root.create_entity", f, ifc_class="IfcWall", name=name, predefined_type="STANDARD")
    wtype = run("root.create_entity", f, ifc_class="IfcWallType", name=name + " type")
    lset = run("material.add_material_set", f, name=name + " layers", set_type="IfcMaterialLayerSet")
    layer = run("material.add_layer", f, layer_set=lset, material=block)
    run("material.edit_layer", f, layer=layer, attributes={"LayerThickness": thickness})
    run("material.assign_material", f, products=[wtype], type="IfcMaterialLayerSet", material=lset)
    run("type.assign_type", f, related_objects=[wall], relating_type=wtype)
    d = np.array(p2, float) - np.array(p1, float); L = float(np.linalg.norm(d)); ang = math.atan2(d[1], d[0])
    run("geometry.edit_object_placement", f, product=wall, matrix=placement([p1[0], p1[1], 0.0], ang))
    arep = run("geometry.add_axis_representation", f, context=axis, axis=[(0.0, 0.0), (L, 0.0)])
    run("geometry.assign_representation", f, product=wall, representation=arep)
    brep = run("geometry.add_wall_representation", f, context=body, length=L, height=height, thickness=thickness)
    run("geometry.assign_representation", f, product=wall, representation=brep)
    return wall

def axis_of(w):
    return [np.round(p, 3).tolist() for p in urep.get_reference_line(w)]

def body_items(w):
    rep = urep.get_representation(w, "Model", "Body", "MODEL_VIEW")
    return [i.is_a() for i in rep.Items]

A = make_wall("Wall A", (0, 0), (4, 0))
B = make_wall("Wall B", (4, 0), (4, 3))
print("W0 material on occurrence:", uel.get_material(A).is_a())
print("W0 before join  A:", axis_of(A), body_items(A), shape_info(A))
print("W0 before join  B:", axis_of(B), body_items(B), shape_info(B))

t = time.time()
rel = run("geometry.connect_wall", f, wall1=A, wall2=B)
print("W1 connect_wall ->", rel.is_a(), rel.RelatingConnectionType, "/", rel.RelatedConnectionType)
for w in (A, B): run("geometry.regenerate_wall_representation", f, wall=w)
print("W1 regenerated L-join in %.3fs" % (time.time() - t))
print("W1 after join   A:", axis_of(A), body_items(A), shape_info(A))
print("W1 after join   B:", axis_of(B), body_items(B), shape_info(B))

# extend A's axis 1 m past the join, regenerate
arepA = urep.get_representation(A, "Plan", "Axis", "GRAPH_VIEW")
item = arepA.Items[0]
builder.set_polyline_coords(item, [(0.0, 0.0), (5.0, 0.0)])
print("W2 axis A edited to:", axis_of(A))
for w in (A, B): run("geometry.regenerate_wall_representation", f, wall=w)
print("W2 after regen  A:", axis_of(A), body_items(A), shape_info(A))
print("W2 after regen  B:", axis_of(B), body_items(B), shape_info(B))

# move B 1 m in +X (with children), regenerate both: does A follow to close the gap?
mB = world(B); mB[0, 3] += 1.0
run("geometry.edit_object_placement", f, product=B, matrix=mB, should_transform_children=True)
print("W3 B moved, before regen A:", axis_of(A), shape_info(A))
run("geometry.regenerate_wall_representation", f, wall=A)
print("W3 B moved, after regen A only:", axis_of(A), shape_info(A))
run("geometry.regenerate_wall_representation", f, wall=B)
print("W3 B moved +1m  A:", axis_of(A), body_items(A), shape_info(A))
print("W3 B moved +1m  B:", axis_of(B), body_items(B), shape_info(B))
print("W3 connection still recorded:", [(r.RelatingConnectionType, r.RelatedConnectionType) for r in A.ConnectedTo])

# ------------------------------------------------------------------ pipes
steel = run("material.add_material", f, name="Steel")
def make_pipe(name, start, length, r_out=0.025, t=0.003):
    pipe = run("root.create_entity", f, ifc_class="IfcPipeSegment", name=name, predefined_type="RIGIDSEGMENT")
    ptype = run("root.create_entity", f, ifc_class="IfcPipeSegmentType", name=name + " type", predefined_type="RIGIDSEGMENT")
    pset = run("material.add_material_set", f, name=name + " profile", set_type="IfcMaterialProfileSet")
    prof = f.createIfcCircleHollowProfileDef("AREA", "DN50", None, r_out, t)
    run("material.add_profile", f, profile_set=pset, material=steel, profile=prof)
    run("material.assign_material", f, products=[ptype], type="IfcMaterialProfileSet", material=pset)
    run("type.assign_type", f, related_objects=[pipe], relating_type=ptype)
    m = np.eye(4)  # local +Z along world +X
    m[:3, 0] = (0, 1, 0); m[:3, 1] = (0, 0, 1); m[:3, 2] = (1, 0, 0); m[:3, 3] = start
    run("geometry.edit_object_placement", f, product=pipe, matrix=m)
    rep = run("geometry.add_profile_representation", f, context=body, profile=prof, depth=length)
    run("geometry.assign_representation", f, product=pipe, representation=rep)
    ports = []
    for zloc, fd in ((0.0, "SINK"), (length, "SOURCE")):
        port = run("system.add_port", f, element=pipe)
        port.PredefinedType = "PIPE"; port.FlowDirection = fd
        pm = m.copy(); pm[:3, 3] = m[:3, 3] + m[:3, 2] * zloc
        run("geometry.edit_object_placement", f, product=port, matrix=pm)
        ports.append(port)
    return pipe, ports

P1, (p1s, p1e) = make_pipe("Pipe 1", (0, 0, 1), 2.0)
P2, (p2s, p2e) = make_pipe("Pipe 2", (2, 0, 1), 1.5)
print("P0 port placement relative to owner:", p1e.ObjectPlacement.PlacementRelTo == P1.ObjectPlacement)
run("system.connect_port", f, port1=p1e, port2=p2s, direction="SOURCE")
def port_pos(p): return np.round(world(p)[:3, 3], 3).tolist()
def gap(): return float(np.linalg.norm(world(p1e)[:3, 3] - world(p2s)[:3, 3]))
print("P0 connected:", usys.get_connected_port(p1e) == p2s, "| P1 end", port_pos(p1e), "P2 start", port_pos(p2s), "gap %.3f" % gap())
print("P0 geometry P1:", shape_info(P1)); print("P0 geometry P2:", shape_info(P2))

# extend pipe 1 to 2.5 m: what the file does by itself = nothing. Adapter steps:
t = time.time()
rep = urep.get_representation(P1, "Model", "Body", "MODEL_VIEW")
ext = rep.Items[0]; print("P1 body item:", ext.is_a(), "depth", ext.Depth)
ext.Depth = 2.5                                              # (1) body
m1 = world(P1); pm = m1.copy(); pm[:3, 3] = m1[:3, 3] + m1[:3, 2] * 2.5
run("geometry.edit_object_placement", f, product=p1e, matrix=pm)   # (2) end port follows
print("P1 after depth edit: end port", port_pos(p1e), "| P2 start", port_pos(p2s), "| gap %.3f m" % gap(),
      "| still 'connected' in IFC:", usys.get_connected_port(p1e) == p2s)
# validation sees nothing: connected ports 0.5 m apart is schema-legal
log = io.StringIO(); logger = logging.getLogger("v"); logger.handlers = [logging.StreamHandler(log)]; logger.setLevel(logging.INFO)
ifcopenshell.validate.validate(f, logger, express_rules=True)
print("P1 validate (schema+WHERE rules) lines:", len([l for l in log.getvalue().splitlines() if l.strip()]))
# gap policy keepConnected: translate the downstream element (with its ports) by the port delta
delta = world(p1e)[:3, 3] - world(p2s)[:3, 3]
m2 = world(P2); m2[:3, 3] += delta
run("geometry.edit_object_placement", f, product=P2, matrix=m2, should_transform_children=True)  # (3) neighbour follows
print("P2 translated by", np.round(delta, 3).tolist(), "| gap now %.3f m" % gap(), "| %.3fs" % (time.time() - t))
print("P2 geometry P1:", shape_info(P1)); print("P2 geometry P2:", shape_info(P2))

# alternative policy: neighbour fixed, segment 2 shortened instead (both ends constrained)
rep2 = urep.get_representation(P2, "Model", "Body", "MODEL_VIEW"); ext2 = rep2.Items[0]
print("P3 alt policy would set P2 depth", ext2.Depth, "->", ext2.Depth - 0.5, "and move its start port; a fitting insert needs mep_bend_shape/mep_transition_shape + connect_port")
out = args.output
f.write(out); print("wrote", out, len(list(f)), "entities")
