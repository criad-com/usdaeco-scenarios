sb.Append(RunKeep("T7d P1b diameter 65 mm: which fittings appear at commit?", () => SetDia("P1b", 65)));
sb.Append(RunKeep("T7d revert to 50", () => SetDia("P1b", 50)));
return sb.ToString();
