double y = M(10);
var level = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().First(l => l.Name == "L1");
var wa = ByCmt("WA") as Wall;
double Vol(Element e) { double v = 0; foreach (GeometryObject g in e.get_Geometry(new Options())) { var s = g as Solid; if (s != null) v += s.Volume; } return Math.Round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.CubicMeters), 3); }
var syms = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().ToList();
sb.AppendLine("WA volume now " + Vol(wa) + " | door families: " + string.Join(" | ", syms.Select(s => s.FamilyName).Distinct()));
var rec = new FailRec();
using (var t = Tx("door fix", rec)) {
    t.Start();
    var old = ByCmt("D1"); if (old != null) doc.Delete(old.Id);
    var sym = syms.FirstOrDefault(s => s.FamilyName.Contains("Passage-Double")) ?? syms.First();
    if (!sym.IsActive) sym.Activate(); doc.Regenerate();
    var d = doc.Create.NewFamilyInstance(new XYZ(M(6), y, 0), sym, wa, Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
    SetCmt(d, "D1"); doc.Regenerate();
    sb.AppendLine("placed " + sym.FamilyName + ":" + sym.Name + " (4-arg overload) -> WA volume " + Vol(wa) + " | door level=" + doc.GetElement(d.LevelId)?.Name + " host=" + Cmt(d.Host));
    if (Vol(wa) >= 4.86) { doc.Delete(d.Id); var sym2 = syms.First(s => s.FamilyName.Contains("Exterior-Single")); if (!sym2.IsActive) sym2.Activate(); doc.Regenerate();
        var d2 = doc.Create.NewFamilyInstance(new XYZ(M(6), y, 0), sym2, wa, level, Autodesk.Revit.DB.Structure.StructuralType.NonStructural); SetCmt(d2, "D1"); doc.Regenerate();
        sb.AppendLine("placed " + sym2.FamilyName + " (5-arg) -> WA volume " + Vol(wa) + " | sill=" + d2.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble() + " elev=" + d2.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM)?.AsDouble()); }
    var st = t.Commit(); sb.AppendLine("tx=" + st + " " + Fails(rec));
}
sb.AppendLine("WA volume after commit " + Vol(ByCmt("WA")) + " | " + Describe(ByCmt("D1")));
sb.Append(RunKeep("W1d shorten WA from start past the (cutting?) door: (7000,y)->(8000,y)", () => SetCurve("WA", new XYZ(M(7), y, 0), new XYZ(M(8), y, 0))));
foreach (var w in doc.GetWarnings()) sb.AppendLine("  WARNING: " + w.GetDescriptionText().Split('\n')[0] + " els=" + string.Join(",", w.GetFailingElements().Select(i => Cmt(doc.GetElement(i)) + "#" + i)));
var dd = ByCmt("D1"); sb.AppendLine("door after: " + (dd == null ? "DELETED" : Describe(dd)));
sb.Append(RunKeep("W1d revert", () => SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(8), y, 0))));
sb.AppendLine("WA volume after revert " + Vol(ByCmt("WA")) + " | door: " + (ByCmt("D1") == null ? "DELETED" : "present"));
return sb.ToString();
