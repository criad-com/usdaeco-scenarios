var app = uiapp.Application;
var sb = new System.Text.StringBuilder();
string tpl = @"C:\ProgramData\Autodesk\RVT 2027\Templates\English\Default-Multi-Discipline_Metric.rte";
string dir = (System.Environment.GetEnvironmentVariable("AECO_SPIKE_DIR") ?? System.IO.Directory.GetCurrentDirectory()); System.IO.Directory.CreateDirectory(dir);
string path = System.IO.Path.Combine(dir, "wallpipe.rvt");
Document existing = null;
foreach (Document d in app.Documents) if (string.Equals(d.PathName, path, StringComparison.OrdinalIgnoreCase)) existing = d;
if (existing == null) {
    if (System.IO.File.Exists(path)) System.IO.File.Delete(path);
    var nd = app.NewProjectDocument(tpl);
    sb.AppendLine("created from template: " + nd.Title + " units=" + nd.GetUnits().GetFormatOptions(SpecTypeId.Length).GetUnitTypeId().TypeId);
    var so = new SaveAsOptions(); so.OverwriteExistingFile = true;
    nd.SaveAs(path, so);
    sb.AppendLine("saved: " + nd.PathName);
    nd.Close(false);
    sb.AppendLine("closed background copy");
}
var uidoc = uiapp.OpenAndActivateDocument(path);
var doc = uidoc.Document;
sb.AppendLine("activated: " + doc.Title + " | active=" + (uiapp.ActiveUIDocument?.Document.Title));
sb.AppendLine("active view: " + (uidoc.ActiveView?.Name) + " (" + uidoc.ActiveView?.ViewType + ")");
int n = 0; foreach (Document d in app.Documents) n++;
sb.AppendLine("open documents now: " + n);
return sb.ToString();
