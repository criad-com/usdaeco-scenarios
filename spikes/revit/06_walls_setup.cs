var level = new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().First(l => l.Name == "L1");
var wt = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().First(w => w.Name == "Generic - 200mm");
var dsym = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().First();
var rec = new FailRec();
using (var t = Tx("walls", rec)) {
    t.Start();
    var wa = Wall.Create(doc, Line.CreateBound(new XYZ(0, M(10), 0), new XYZ(M(8), M(10), 0)), wt.Id, level.Id, M(3), 0, false, false); SetCmt(wa, "WA");
    var wb = Wall.Create(doc, Line.CreateBound(new XYZ(M(8), M(10), 0), new XYZ(M(8), M(16), 0)), wt.Id, level.Id, M(3), 0, false, false); SetCmt(wb, "WB");
    doc.Regenerate();
    if (!dsym.IsActive) dsym.Activate();
    var d = doc.Create.NewFamilyInstance(new XYZ(M(6), M(10), 0), dsym, wa, level, Autodesk.Revit.DB.Structure.StructuralType.NonStructural); SetCmt(d, "D1");
    var st = t.Commit(); sb.AppendLine("tx=" + st + " " + Fails(rec));
}
foreach (var n in new[] { "WA", "WB", "D1" }) sb.AppendLine(Describe(ByCmt(n)));
foreach (var n in new[] { "WA", "WB" }) { var w = ByCmt(n) as Wall; var lc = w.Location as LocationCurve;
    for (int end = 0; end < 2; end++) { var joined = lc.get_ElementsAtJoin(end); var ids = new List<string>(); foreach (Element e in joined) ids.Add(Cmt(e) + "#" + e.Id);
        sb.AppendLine(n + " end" + end + ": joinAllowed=" + WallUtils.IsWallJoinAllowedAtEnd(w, end) + " joinType=" + lc.get_JoinType(end) + " joined=[" + string.Join(",", ids) + "]"); }
    sb.AppendLine(n + " height=" + Mm(w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()) + " locLine=" + w.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).AsInteger() + " flipped=" + w.Flipped + " width=" + Mm(w.Width) + " len=" + Mm(w.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH).AsDouble()) + " lenReadOnly=" + w.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH).IsReadOnly);
}
var door = ByCmt("D1") as FamilyInstance; sb.AppendLine("D1 host=" + Cmt(door.Host) + " at " + P((door.Location as LocationPoint).Point));
return sb.ToString();
