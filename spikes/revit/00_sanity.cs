var app = uiapp.Application;
var sb = new System.Text.StringBuilder();
sb.AppendLine("Revit " + app.VersionNumber + " build " + app.VersionBuild);
var active = uiapp.ActiveUIDocument?.Document;
sb.AppendLine("active: " + (active == null ? "(none)" : active.Title + " | " + active.PathName));
int n = 0;
foreach (Document d in app.Documents) {
    n++;
    if (n <= 6) sb.AppendLine("  doc: " + d.Title + " | modifiable=" + d.IsModifiable + " | family=" + d.IsFamilyDocument + " | " + d.PathName);
}
sb.AppendLine("open documents: " + n);
sb.AppendLine("thread: " + System.Threading.Thread.CurrentThread.ManagedThreadId + " | " + System.Threading.Thread.CurrentThread.Name);
return sb.ToString();
