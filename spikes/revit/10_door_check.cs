double y = M(10);
var wa = ByCmt("WA") as Wall; var d = ByCmt("D1") as FamilyInstance;
double vol = 0; foreach (GeometryObject g in wa.get_Geometry(new Options())) { var s = g as Solid; if (s != null) vol += s.Volume; }
sb.AppendLine("WA solid volume=" + Math.Round(UnitUtils.ConvertFromInternalUnits(vol, UnitTypeId.CubicMeters), 3) + " m3 (full box 4.8) | door host=" + Cmt(d.Host) + " HOST_ID=" + d.get_Parameter(BuiltInParameter.HOST_ID_PARAM)?.AsElementId() + " facing=" + P(d.FacingOrientation) + " symbol=" + d.Symbol.FamilyName + ":" + d.Symbol.Name + " level=" + doc.GetElement(d.LevelId)?.Name);
sb.AppendLine("doc warnings before: " + doc.GetWarnings().Count);
sb.Append(RunKeep("W1c shorten WA from start past the door (7000->8000), then read Document.GetWarnings()", () => SetCurve("WA", new XYZ(M(7), y, 0), new XYZ(M(8), y, 0))));
foreach (var w in doc.GetWarnings()) sb.AppendLine("  WARNING " + w.GetSeverity() + ": " + w.GetDescriptionText() + " els=" + string.Join(",", w.GetFailingElements().Select(i => Cmt(doc.GetElement(i)) + "#" + i)));
d = ByCmt("D1") as FamilyInstance; sb.AppendLine("door after: " + (d == null ? "DELETED" : Describe(d) + " bbox=" + (d.get_BoundingBox(null) == null ? "none" : P(d.get_BoundingBox(null).Min))));
sb.Append(RunKeep("W1c revert", () => SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(8), y, 0))));
sb.AppendLine("doc warnings after revert: " + doc.GetWarnings().Count);
return sb.ToString();
