var doc = uiapp.ActiveUIDocument.Document;
var sb = new System.Text.StringBuilder();
sb.AppendLine("doc: " + doc.Title);
foreach (Level l in new FilteredElementCollector(doc).OfClass(typeof(Level))) sb.AppendLine("level: " + l.Name + " elev=" + Math.Round(UnitUtils.ConvertFromInternalUnits(l.Elevation, UnitTypeId.Millimeters)) + " mm id=" + l.Id);
foreach (PipeType t in new FilteredElementCollector(doc).OfClass(typeof(PipeType))) {
    var rpm = t.RoutingPreferenceManager;
    sb.AppendLine("pipeType: " + t.Name + " id=" + t.Id + " segRules=" + rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Segments) + " elbowRules=" + rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Elbows) + " junctionRules=" + rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Junctions) + " transitionRules=" + rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Transitions) + " unionRules=" + rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Unions));
    for (int i = 0; i < rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Elbows); i++) { var r = rpm.GetRule(RoutingPreferenceRuleGroupType.Elbows, i); var fam = doc.GetElement(r.MEPPartId); sb.AppendLine("   elbow rule " + i + ": " + (fam == null ? "(none)" : fam.Name) + " id=" + r.MEPPartId); }
    for (int i = 0; i < rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Segments); i++) { var r = rpm.GetRule(RoutingPreferenceRuleGroupType.Segments, i); var seg = doc.GetElement(r.MEPPartId) as PipeSegment; if (seg != null) { var sizes = seg.GetSizes().Select(s => Math.Round(UnitUtils.ConvertFromInternalUnits(s.NominalDiameter, UnitTypeId.Millimeters))).ToList(); sb.AppendLine("   segment rule " + i + ": " + seg.Name + " sizes(mm)=" + string.Join(",", sizes)); } }
}
foreach (PipingSystemType s in new FilteredElementCollector(doc).OfClass(typeof(PipingSystemType))) sb.AppendLine("pipingSystemType: " + s.Name + " id=" + s.Id + " class=" + s.SystemClassification);
foreach (WallType w in new FilteredElementCollector(doc).OfClass(typeof(WallType))) { if (w.Kind != WallKind.Basic) continue; var cs = w.GetCompoundStructure(); sb.AppendLine("wallType: " + w.Name + " id=" + w.Id + " width=" + Math.Round(UnitUtils.ConvertFromInternalUnits(w.Width, UnitTypeId.Millimeters)) + "mm layers=" + (cs == null ? -1 : cs.LayerCount)); }
var doors = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().ToList();
sb.AppendLine("door symbols loaded: " + doors.Count + " " + string.Join(" | ", doors.Take(5).Select(d => d.FamilyName + ":" + d.Name)));
if (doors.Count == 0) {
    using (var t = new Transaction(doc, "load door")) { t.Start(); Family fam; bool ok = doc.LoadFamily(@"C:\ProgramData\Autodesk\RVT 2027\Libraries\English\US\Doors\Commercial\M_Door-Passage-Single-Flush.rfa", out fam); t.Commit(); sb.AppendLine("loaded door family: " + ok + " " + (fam?.Name)); }
    doors = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilySymbol>().ToList();
    sb.AppendLine("door symbols now: " + string.Join(" | ", doors.Take(6).Select(d => d.FamilyName + ":" + d.Name + " id=" + d.Id)));
}
var fittings = new FilteredElementCollector(doc).OfClass(typeof(FamilySymbol)).OfCategory(BuiltInCategory.OST_PipeFitting).Cast<FamilySymbol>().ToList();
sb.AppendLine("pipe fitting symbols: " + fittings.Count + " " + string.Join(" | ", fittings.Take(12).Select(f => f.FamilyName + ":" + f.Name)));
return sb.ToString();
