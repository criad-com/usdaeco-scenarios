var sw = System.Diagnostics.Stopwatch.StartNew();
var opts = new IFCExportOptions(); opts.FileVersion = IFCVersion.IFC4; opts.ExportBaseQuantities = true; opts.WallAndColumnSplitting = false;
opts.AddOption("ExportIFCCommonPropertySets", "true"); opts.AddOption("ExportInternalRevitPropertySets", "false"); opts.AddOption("ExportLinkedFiles", "false"); opts.AddOption("ExportBoundingBox", "false"); opts.AddOption("StoreIFCGUID", "true");
var rec = new FailRec();
using (var t = Tx("ifc export", rec)) { t.Start(); bool ok = doc.Export((System.Environment.GetEnvironmentVariable("AECO_SPIKE_DIR") ?? System.IO.Directory.GetCurrentDirectory()), "wallpipe", opts); var st = t.Commit(); sb.AppendLine("export ok=" + ok + " tx=" + st + " " + Fails(rec) + " " + sw.ElapsedMilliseconds + " ms"); }
foreach (var n in new[] { "P1", "T1", "P1b", "E1", "P2", "P3", "WA", "WB", "D1" }) { var e = ByCmt(n); var g = e.get_Parameter(BuiltInParameter.IFC_GUID); sb.AppendLine(n + " id=" + e.Id + " uid=" + e.UniqueId + " IfcGUID=" + (g == null ? "(no param)" : g.AsString())); }
var p1 = ByCmt("P1"); foreach (Connector c in CM(p1).Connectors) sb.AppendLine("P1 connector Id=" + c.Id + " dir=" + c.Direction + " " + P(c.Origin));
sb.AppendLine(System.IO.File.Exists(System.IO.Path.Combine(System.Environment.GetEnvironmentVariable("AECO_SPIKE_DIR") ?? System.IO.Directory.GetCurrentDirectory(), "wallpipe.ifc")) ? "file size=" + new System.IO.FileInfo(System.IO.Path.Combine(System.Environment.GetEnvironmentVariable("AECO_SPIKE_DIR") ?? System.IO.Directory.GetCurrentDirectory(), "wallpipe.ifc")).Length : "NO FILE");
return sb.ToString();
