double y = M(10);
sb.Append(RunKeep("W6 WA type -> Interior - 125mm Partition", () => { var wt = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().First(w => w.Name == "Interior - 125mm Partition"); (ByCmt("WA") as Wall).WallType = wt; }));
sb.Append(RunKeep("W6 revert", () => { var wt = new FilteredElementCollector(doc).OfClass(typeof(WallType)).Cast<WallType>().First(w => w.Name == "Generic - 200mm"); (ByCmt("WA") as Wall).WallType = wt; }));
sb.Append(RunKeep("W7 MoveElement WA by (0,+1000,0) (perpendicular to itself)", () => Move("WA", new XYZ(0, M(1), 0))));
sb.Append(RunKeep("W7 revert", () => Move("WA", new XYZ(0, M(-1), 0))));
sb.Append(RunKeep("W8 Flip WA", () => (ByCmt("WA") as Wall).Flip()));
sb.Append(RunKeep("W8 revert", () => (ByCmt("WA") as Wall).Flip()));
return sb.ToString();
