// ---- shared helpers (prepended to every spike script) ----
var doc = uiapp.ActiveUIDocument.Document;
var sb = new System.Text.StringBuilder();
double M(double v) => UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Meters);
double Mm(double v) => Math.Round(UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters), 1);
string P(XYZ p) => "(" + Mm(p.X) + "," + Mm(p.Y) + "," + Mm(p.Z) + ")";
string Cmt(Element e) => e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)?.AsString() ?? "";
void SetCmt(Element e, string s) => e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(s);
Element ByCmt(string s) => new FilteredElementCollector(doc).WhereElementIsNotElementType().Where(e => Cmt(e) == s).FirstOrDefault();
ConnectorManager CM(Element e) => (e as MEPCurve)?.ConnectorManager ?? (e as FamilyInstance)?.MEPModel?.ConnectorManager;
Connector Nearest(Element e, XYZ pt) { Connector best = null; double bd = 1e9; foreach (Connector c in CM(e).Connectors) { double d = c.Origin.DistanceTo(pt); if (d < bd) { bd = d; best = c; } } return best; }
string Describe(Element e) {
    var s = new System.Text.StringBuilder();
    s.Append(Cmt(e) + " [" + e.GetType().Name + " id=" + e.Id + "]");
    var lc = e.Location as LocationCurve;
    if (lc != null) s.Append(" curve " + P(lc.Curve.GetEndPoint(0)) + "->" + P(lc.Curve.GetEndPoint(1)) + " len=" + Mm(lc.Curve.Length) + "mm");
    var lp = e.Location as LocationPoint; if (lp != null) s.Append(" at " + P(lp.Point));
    var dia = e.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM); if (dia != null && dia.HasValue) s.Append(" dia=" + Mm(dia.AsDouble()) + "mm");
    var cm = CM(e);
    if (cm != null) foreach (Connector c in cm.Connectors.Cast<Connector>().OrderBy(c => c.Id)) {
        string peer = "-"; if (c.IsConnected) foreach (Connector r in c.AllRefs) { if (r.Owner.Id != e.Id && r.ConnectorType == ConnectorType.End) peer = Cmt(r.Owner) + "#" + r.Id; }
        s.Append(" | c" + c.Id + " " + P(c.Origin) + " r=" + Mm(c.Radius) + " " + (c.IsConnected ? "->" + peer : "free"));
    }
    var wall = e as Wall;
    if (wall != null) { var wlc = wall.Location as LocationCurve; s.Append(" width=" + Mm(wall.Width) + " flipped=" + wall.Flipped);
        for (int end = 0; end < 2; end++) { var ids = new List<string>(); foreach (Element j in wlc.get_ElementsAtJoin(end)) if (j.Id != e.Id) ids.Add(Cmt(j)); s.Append(" | end" + end + " " + wlc.get_JoinType(end) + " allow=" + WallUtils.IsWallJoinAllowedAtEnd(wall, end) + " joined=[" + string.Join(",", ids) + "]"); } }
    var fi = e as FamilyInstance; if (fi != null && fi.Host != null) s.Append(" host=" + Cmt(fi.Host));
    return s.ToString();
}
class FailRec : IFailuresPreprocessor {
    public List<string> Msgs = new List<string>();
    public bool RollbackOnError = true;
    public FailureProcessingResult PreprocessFailures(FailuresAccessor fa) {
        bool err = false;
        foreach (var f in fa.GetFailureMessages()) {
            var ids = string.Join(",", f.GetFailingElementIds().Select(i => i.ToString()));
            Msgs.Add(f.GetSeverity() + " [" + f.GetFailureDefinitionId().Guid.ToString().Substring(0, 8) + "] " + f.GetDescriptionText() + " els=" + ids + " resolutions=" + f.GetNumberOfResolutions());
            if (f.GetSeverity() == FailureSeverity.Error) err = true;
            if (f.GetSeverity() == FailureSeverity.Warning) fa.DeleteWarning(f);
        }
        return (err && RollbackOnError) ? FailureProcessingResult.ProceedWithRollBack : FailureProcessingResult.Continue;
    }
}
Transaction Tx(string name, FailRec rec) { var t = new Transaction(doc, name); var o = t.GetFailureHandlingOptions(); o.SetFailuresPreprocessor(rec); o.SetClearAfterRollback(true); t.SetFailureHandlingOptions(o); return t; }
string Fails(FailRec rec) => rec.Msgs.Count == 0 ? "failures: none" : "failures:\n  " + string.Join("\n  ", rec.Msgs);
// ---- test harness: run an edit in a transaction, diff named elements, roll back ----
string[] Names = new[] { "P1", "T1", "P1b", "E1", "P2", "P3", "P4", "P5", "E2", "U1", "WA", "WB", "D1" };
Dictionary<string,string> Snap() { var d = new Dictionary<string,string>(); foreach (var n in Names) { var e = ByCmt(n); if (e != null) d[n] = Describe(e); } return d; }
string RunTest(string title, Action body, bool keep = false) {
    var r = new System.Text.StringBuilder(); r.AppendLine("## " + title);
    var before = Snap(); var rec = new FailRec(); rec.RollbackOnError = false; string ex = null;
    var sw = System.Diagnostics.Stopwatch.StartNew();
    using (var t = Tx(title, rec)) {
        t.Start();
        try { body(); doc.Regenerate(); } catch (Exception e) { ex = e.GetType().Name + ": " + e.Message.Split('\n')[0]; }
        Dictionary<string,string> after = null;
        try { after = Snap(); } catch (Exception e) { r.AppendLine("  snapshot failed: " + e.Message.Split('\n')[0]); }
        if (after != null) {
            foreach (var n in Names) {
                string b = before.ContainsKey(n) ? before[n] : null, a = after.ContainsKey(n) ? after[n] : null;
                if (a != b) r.AppendLine("  " + (b == null ? "NEW " : a == null ? "GONE " : "") + (a ?? n));
            }
            var newPipes = new FilteredElementCollector(doc).OfClass(typeof(Pipe)).Cast<Pipe>().Where(p => Cmt(p) == "").ToList();
            var newFit = new FilteredElementCollector(doc).OfClass(typeof(FamilyInstance)).OfCategory(BuiltInCategory.OST_PipeFitting).Cast<FamilyInstance>().Where(f => Cmt(f) == "").ToList();
            foreach (var p in newPipes) r.AppendLine("  NEW unlabeled " + Describe(p));
            foreach (var f in newFit) r.AppendLine("  NEW unlabeled fitting " + f.Symbol.FamilyName + " " + Describe(f));
        }
        if (ex != null) r.AppendLine("  EXCEPTION " + ex);
        var st = keep ? t.Commit() : t.RollBack();
        r.AppendLine("  " + Fails(rec) + " | tx " + st + " | " + sw.ElapsedMilliseconds + " ms");
    }
    return r.ToString();
}
void SetCurve(string name, XYZ a, XYZ b) { var e = ByCmt(name); (e.Location as LocationCurve).Curve = Line.CreateBound(a, b); }
void Move(string name, XYZ d) { ElementTransformUtils.MoveElement(doc, ByCmt(name).Id, d); }
void SetDia(string name, double mm) { ByCmt(name).get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(M(mm / 1000.0)); }

// commit variant: run, commit (errors roll back via the preprocessor), report failures + state after commit
string RunKeep(string title, Action body) {
    var r = new System.Text.StringBuilder(); r.AppendLine("## " + title + " [COMMIT]");
    var before = Snap(); var rec = new FailRec(); rec.RollbackOnError = true; string ex = null; TransactionStatus st;
    using (var t = Tx(title, rec)) { t.Start(); try { body(); } catch (Exception e) { ex = e.GetType().Name + ": " + e.Message.Split('\n')[0]; } st = ex == null ? t.Commit() : t.RollBack(); }
    var after = Snap();
    foreach (var n in Names) { string b = before.ContainsKey(n) ? before[n] : null, a = after.ContainsKey(n) ? after[n] : null; if (a != b) r.AppendLine("  " + (b == null ? "NEW " : a == null ? "GONE " : "") + (a ?? n)); }
    foreach (var p in new FilteredElementCollector(doc).OfClass(typeof(Pipe)).Cast<Pipe>().Where(p => Cmt(p) == "")) r.AppendLine("  NEW unlabeled " + Describe(p));
    foreach (var f in new FilteredElementCollector(doc).OfClass(typeof(FamilyInstance)).OfCategory(BuiltInCategory.OST_PipeFitting).Cast<FamilyInstance>().Where(f => Cmt(f) == "")) r.AppendLine("  NEW unlabeled fitting " + f.Symbol.FamilyName + ":" + f.Symbol.Name + " " + Describe(f));
    if (ex != null) r.AppendLine("  EXCEPTION " + ex);
    r.AppendLine("  " + Fails(rec) + " | tx " + st);
    return r.ToString();
}
