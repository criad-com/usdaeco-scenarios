double y = M(10);
sb.Append(RunKeep("W9 shorten WA from its UNJOINED start: (2000,y)->(8000,y)", () => SetCurve("WA", new XYZ(M(2), y, 0), new XYZ(M(8), y, 0))));
sb.Append(RunKeep("W9 revert", () => SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(8), y, 0))));
sb.Append(RunKeep("W1b shorten WA from the start past the door: (7000,y)->(8000,y)", () => SetCurve("WA", new XYZ(M(7), y, 0), new XYZ(M(8), y, 0))));
sb.Append(RunKeep("W1b revert (if committed)", () => SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(8), y, 0))));
sb.Append(RunKeep("W3b disallow join at WA end1, then extend WA to 10000", () => { WallUtils.DisallowWallJoinAtEnd(ByCmt("WA") as Wall, 1); doc.Regenerate(); SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(10), y, 0)); }));
sb.Append(RunKeep("W3b revert + allow", () => { SetCurve("WA", new XYZ(0, y, 0), new XYZ(M(8), y, 0)); WallUtils.AllowWallJoinAtEnd(ByCmt("WA") as Wall, 1); }));
sb.Append(RunKeep("W10 no-op regenerate (does the join come back?)", () => { doc.Regenerate(); }));
var opts = new IFCExportOptions(); opts.FileVersion = IFCVersion.IFC4; opts.ExportBaseQuantities = true; opts.AddOption("ExportIFCCommonPropertySets", "true"); opts.AddOption("StoreIFCGUID", "true");
var rec = new FailRec(); using (var t = Tx("ifc export 2", rec)) { t.Start(); bool ok = doc.Export((System.Environment.GetEnvironmentVariable("AECO_SPIKE_DIR") ?? System.IO.Directory.GetCurrentDirectory()), "wallpipe2", opts); t.Commit(); sb.AppendLine("export2 ok=" + ok + " " + Fails(rec)); }
return sb.ToString();
