sb.Append(RunTest("T4 MoveElement P2 by (+1000,0,0)", () => Move("P2", new XYZ(M(1), 0, 0))));
sb.Append(RunTest("T5 MoveElement P1 by (0,+1000,0) perpendicular", () => Move("P1", new XYZ(0, M(1), 0))));
sb.Append(RunTest("T6 MoveElement tee T1 by (+500,0,0)", () => Move("T1", new XYZ(M(0.5), 0, 0))));
return sb.ToString();
