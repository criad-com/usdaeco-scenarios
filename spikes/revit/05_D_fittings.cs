double z = M(3.0);
var level = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().First(l => l.Name == "L1");
var ptype = new FilteredElementCollector(doc).OfClass(typeof(PipeType)).Cast<PipeType>().First(t => t.Name == "Standard");
var sys = new FilteredElementCollector(doc).OfClass(typeof(PipingSystemType)).Cast<PipingSystemType>().First(s => s.Name == "Domestic Cold Water");
sb.Append(RunTest("T10 new P4 from P3 free end at an angle + NewElbowFitting", () => {
    var p4 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, new XYZ(M(3), M(3), z), new XYZ(0, M(3), z)); SetCmt(p4, "P4"); p4.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05)); doc.Regenerate();
    var e2 = doc.Create.NewElbowFitting(Nearest(ByCmt("P3"), new XYZ(M(3), M(3), z)), Nearest(p4, new XYZ(M(3), M(3), z))); SetCmt(e2, "E2"); }));
sb.Append(RunTest("T11 collinear P5 beyond P3 with a 1000 gap; extend P3 to touch it: auto-connect?", () => {
    var p5 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, new XYZ(M(3), M(4), z), new XYZ(M(3), M(6), z)); SetCmt(p5, "P5"); p5.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05)); doc.Regenerate();
    SetCurve("P3", new XYZ(M(3), M(0.0397), z), new XYZ(M(3), M(4), z)); }));
sb.Append(RunTest("T12 same, then NewUnionFitting on the touching connectors", () => {
    var p5 = Pipe.Create(doc, sys.Id, ptype.Id, level.Id, new XYZ(M(3), M(4), z), new XYZ(M(3), M(6), z)); SetCmt(p5, "P5"); p5.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(0.05)); doc.Regenerate();
    SetCurve("P3", new XYZ(M(3), M(0.0397), z), new XYZ(M(3), M(4), z)); doc.Regenerate();
    var u = doc.Create.NewUnionFitting(Nearest(ByCmt("P3"), new XYZ(M(3), M(4), z)), Nearest(p5, new XYZ(M(3), M(4), z))); SetCmt(u, "U1"); }));
return sb.ToString();
