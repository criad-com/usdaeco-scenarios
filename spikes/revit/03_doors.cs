var doors = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().ToList();
if (doors.Count == 0) {
    var rec = new FailRec();
    using (var t = Tx("load door", rec)) { t.Start(); Family fam; bool ok = doc.LoadFamily(@"C:\ProgramData\Autodesk\RVT 2027\Libraries\English\US\Doors\Commercial\M_Door-Passage-Single-Flush.rfa", out fam); var st = t.Commit(); sb.AppendLine("loaded door family: " + ok + " " + fam?.Name + " tx=" + st + " " + Fails(rec)); }
    doors = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().ToList();
}
sb.AppendLine("door symbols: " + doors.Count + " :: " + string.Join(" | ", doors.Take(6).Select(d => d.FamilyName + ":" + d.Name + " id=" + d.Id)));
var fit = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_PipeFitting).Cast<FamilySymbol>().ToList();
sb.AppendLine("pipe fitting symbols: " + fit.Count + " :: " + string.Join(" | ", fit.Take(10).Select(f => f.FamilyName + ":" + f.Name + " id=" + f.Id)));
return sb.ToString();
