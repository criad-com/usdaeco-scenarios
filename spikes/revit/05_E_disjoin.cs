sb.Append(RunTest("T13 Disjoin: DisconnectFrom(P2.c0, E1.c2) then MoveElement P2 (+1000,0,0)", () => {
    var p2 = ByCmt("P2"); var e1 = ByCmt("E1"); var c0 = Nearest(p2, new XYZ(M(6), M(0.0333), M(3))); Connector peer = null; foreach (Connector r in c0.AllRefs) if (r.Owner.Id == e1.Id) peer = r;
    c0.DisconnectFrom(peer); doc.Regenerate(); Move("P2", new XYZ(M(1), 0, 0)); }));
sb.Append(RunTest("T14 Reconnect after move: P2 back, ConnectTo", () => {
    var p2 = ByCmt("P2"); var e1 = ByCmt("E1"); var c0 = Nearest(p2, new XYZ(M(6), M(0.0333), M(3))); Connector peer = null; foreach (Connector r in c0.AllRefs) if (r.Owner.Id == e1.Id) peer = r;
    c0.DisconnectFrom(peer); doc.Regenerate(); Move("P2", new XYZ(M(1), 0, 0)); doc.Regenerate(); Move("P2", new XYZ(M(-1), 0, 0)); doc.Regenerate(); c0.ConnectTo(peer); }));
return sb.ToString();
