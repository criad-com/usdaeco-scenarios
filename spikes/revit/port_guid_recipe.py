"""Reproduce the Revit IFC exporter's IfcDistributionPort GUIDs from element GUIDs and connector ids.
Verified 13/13 against an IFC4 export of the wallpipe spike (Revit 2027.2, revit-ifc GUIDUtil/ConnectorExporter)."""
import hashlib, sys
import ifcopenshell, ifcopenshell.util.system as usys
T = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
def to_ifc_guid(b):  # GUIDUtil.ConvertToIFCGuid over new Guid(md5).ToByteArray()
    num = [b[3], b[2]*65536 + b[1]*256 + b[0], b[5]*65536 + b[4]*256 + b[7], b[6]*65536 + b[8]*256 + b[9], b[10]*65536 + b[11]*256 + b[12], b[13]*65536 + b[14]*256 + b[15]]
    out = ""
    for i, n in enumerate(num):
        ln = 2 if i == 0 else 4; chars = ""
        for _ in range(ln): chars = T[n % 64] + chars; n //= 64
        out += chars
    return out
def h(key): return to_ifc_guid(hashlib.md5(key.encode("utf-8")).digest())
def free_port(elem_guid, cid): return h(f"{elem_guid}Sub-element:IfcDistributionPort Connector: {cid}")
def in_port(cid, in_guid, out_guid): return h(f"InPort{cid}{in_guid}{out_guid}")       # on the element processed first
def out_port(cid, in_guid, out_guid): return h(f"OutPort{cid}{out_guid}{in_guid}")     # on the other element (same cid = the first element's connector)
if __name__ == "__main__":
    f = ifcopenshell.open(sys.argv[1]); ok = tot = 0
    for e in f.by_type("IfcPipeSegment") + f.by_type("IfcPipeFitting"):
        for p in usys.get_ports(e):
            c = p.Name.rsplit("_", 1)[1]; tot += 1; peer = usys.get_connected_port(p)
            if peer is None: cands = [free_port(e.GlobalId, c)]
            else:
                pe = usys.get_port_element(peer); d = peer.Name.rsplit("_", 1)[1]
                cands = [in_port(c, e.GlobalId, pe.GlobalId), out_port(d, pe.GlobalId, e.GlobalId)]
            ok += p.GlobalId in cands
    print(f"reproduced {ok}/{tot}")
