double z = M(3.0);
sb.Append(RunKeep("T2c LocationCurve: move P2 connected start to (6000,-1000)", () => SetCurve("P2", new XYZ(M(6), M(-1), z), new XYZ(M(6), M(4), z))));
sb.Append(RunKeep("T2c revert", () => SetCurve("P2", new XYZ(M(6), M(0.0333), z), new XYZ(M(6), M(4), z))));
sb.Append(RunKeep("T7c P1b diameter 65 mm", () => SetDia("P1b", 65)));
sb.Append(RunKeep("T7c revert to 50", () => SetDia("P1b", 50)));
sb.Append(RunKeep("T9c P1b diameter 250 mm (beyond table)", () => SetDia("P1b", 250)));
sb.Append(RunKeep("T9c revert to 50", () => SetDia("P1b", 50)));
return sb.ToString();
