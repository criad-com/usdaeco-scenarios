double z = M(3.0);
sb.Append(RunTest("T1 extend P2 free end (6000,33)->(6000,6000)", () => SetCurve("P2", new XYZ(M(6), M(0.0333), z), new XYZ(M(6), M(6), z))));
sb.Append(RunTest("T2 move P2 CONNECTED start away: (6000,-1000)->(6000,4000)", () => SetCurve("P2", new XYZ(M(6), M(-1), z), new XYZ(M(6), M(4), z))));
sb.Append(RunTest("T3 extend P1b past the elbow: (3039.7,0)->(7000,0)", () => SetCurve("P1b", new XYZ(M(3.0397), 0, z), new XYZ(M(7), 0, z))));
return sb.ToString();
