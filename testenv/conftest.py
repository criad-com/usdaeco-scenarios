import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from family import ROOT, activate

import json
state = ROOT / ".work/runtime.json"
default = json.loads(state.read_text())["pluginset"] if state.is_file() else str(ROOT / ".work/pluginset")
activate(os.environ.get("PXR_PLUGINPATH_NAME", default))
