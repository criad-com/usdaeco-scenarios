#!/usr/bin/env python3
"""Post a C# script file (or -c code) to the configured Revit REPL; print result or error."""
import json, sys, subprocess, tempfile, os, time
ENDPOINT = os.environ.get("AECO_REVIT_ENDPOINT", "http://repl.example:48886").rstrip("/")
def post(code, session="wallpipe", timeout=600):
    fd, p = tempfile.mkstemp(suffix=".json"); os.close(fd)
    with open(p, "w") as f: json.dump({"session": session, "code": code}, f)
    try:
        for attempt in range(20):
            st = subprocess.run(["curl", "-s", "-m", "5", f"{ENDPOINT}/status"], capture_output=True, text=True)
            if "Too many pending" in st.stdout: time.sleep(10); continue
            out = subprocess.run(["curl", "-s", "-m", str(timeout), "-X", "POST", f"{ENDPOINT}/eval",
                                  "-H", "Content-Type: application/json", "--data", "@" + p], capture_output=True, text=True)
            if not out.stdout.strip(): return {"error": "empty response rc=%d %s" % (out.returncode, out.stderr[:300])}
            r = json.loads(out.stdout)
            if "Too many pending" in str(r.get("error", "")): time.sleep(10); continue
            return r
        return {"error": "queue stayed full"}
    finally:
        os.unlink(p)
if __name__ == "__main__":
    a = sys.argv[1:]
    session = "wallpipe"; timeout = 600
    if a and a[0] == "-s": session = a[1]; a = a[2:]
    if a and a[0] == "-t": timeout = int(a[1]); a = a[2:]
    code = a[1] if a and a[0] == "-c" else open(a[0], encoding="utf-8").read()
    if not (a and a[0] == "-c") and os.path.basename(a[0]) not in ("00_sanity.cs", "01_newproject.cs", "02_inventory.cs"):
        code = open("helpers.cs", encoding="utf-8").read() + "\n" + code
    r = post(code, session, timeout)
    if r.get("error"): print("ERROR:", str(r["error"])[:3000]); sys.exit(1)
    print(r.get("result"))
