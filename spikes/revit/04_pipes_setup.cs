var level = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().First(l => l.Name == "L1");
var ptype = new FilteredElementCollector(doc).OfClass(typeof(PipeType)).Cast<PipeType>().First(t => t.Name == "Standard");
var sys = new FilteredElementCollector(doc).OfClass(typeof(PipingSystemType)).Cast<PipingSystemType>().First(s => s.Name == "Domestic Cold Water");
var rec = new FailRec();
using (var t = Tx("pipe network", rec)) {
    t.Start();
    double z = M(3.0);
    var p1 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, new XYZ(0, 0, z), new XYZ(M(6), 0, z));
    p1.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05));
    var p2 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, new XYZ(M(6), 0, z), new XYZ(M(6), M(4), z));
    p2.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05));
    doc.Regenerate();
    var corner = new XYZ(M(6), 0, z);
    var elbow = doc.Create.NewElbowFitting(Nearest(p1, corner), Nearest(p2, corner));
    SetCmt(elbow, "E1");
    var split = new XYZ(M(3), 0, z);
    var newId = PlumbingUtils.BreakCurve(doc, p1.Id, split);
    var p1b = doc.GetElement(newId) as Pipe;
    var p3 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, split, new XYZ(M(3), M(3), z));
    p3.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05));
    doc.Regenerate();
    // label by geometry: the piece touching x=0 is P1
    Pipe left = p1, right = p1b;
    if ((p1.Location as LocationCurve).Curve.GetEndPoint(0).X > M(0.1) && (p1.Location as LocationCurve).Curve.GetEndPoint(1).X > M(0.1)) { left = p1b; right = p1; }
    SetCmt(left, "P1"); SetCmt(right, "P1b"); SetCmt(p2, "P2"); SetCmt(p3, "P3");
    var tee = doc.Create.NewTeeFitting(Nearest(left, split), Nearest(right, split), Nearest(p3, split));
    SetCmt(tee, "T1");
    var st = t.Commit();
    sb.AppendLine("tx=" + st + " " + Fails(rec));
}
foreach (var n in new[] { "P1", "T1", "P1b", "E1", "P2", "P3" }) { var e = ByCmt(n); sb.AppendLine(e == null ? n + ": MISSING" : Describe(e)); }
return sb.ToString();
