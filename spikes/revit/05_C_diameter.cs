sb.Append(RunTest("T7 P1b diameter 50 -> 65 mm (in table)", () => SetDia("P1b", 65)));
sb.Append(RunTest("T8 P1b diameter -> 33 mm (NOT in table; 32/40 are)", () => SetDia("P1b", 33)));
sb.Append(RunTest("T9 P1b diameter -> 250 mm (beyond Copper-A table max 200)", () => SetDia("P1b", 250)));
return sb.ToString();
