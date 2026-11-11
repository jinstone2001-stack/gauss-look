"""Run mocked renderer / real HTTP integration; install jsdom separately (NODE_PATH)."""

import sys, os, threading, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gausslook.engine import Engine
from gausslook.webserver import make_server
from gausslook.model import BOHR_ANG
import numpy as np

root = ROOT
e = Engine(root)
r = e.demo()
c = e.get(r["ids"][0])
c.frames[0].update(
    energy_hartree=-76.123456789012, energy_kind="synthetic test energy", force_record=0
)
c.frames.append({"coords": c.frames[0]["coords"], "step": 2})
c.force_records = [
    {
        "forces_hartree_bohr": [[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]],
        "source": "synthetic DOM test",
        "coordinate_system": "fixture",
    }
]
c.modes[0]["frequency_cm1"] = -55
for m in c.modes:
    m["reference_frame"] = 0
c.properties["polarizability_records"] = [
    {"tensor_au": [[3, 0, 0], [0, 4, 0], [0, 0, 5]], "frequency_au": 0.0, "source": "static fixture"},
    {"tensor_au": [[6, 0, 0], [0, 8, 0], [0, 0, 10]], "frequency_au": 0.05, "source": "dynamic fixture"},
]
c.orbitals["alpha"]["has_coefficients"] = True
checkpoint = e.work / "fixture.fchk"
checkpoint.write_text("fixture")
e.checkpoints[c.id] = str(checkpoint)
e.utilities["cubegen"] = "mock"


def utility(name, args, task):
    f = e.fields[r["field_id"]]
    p = Path(args[3])
    a = np.array(f.coords) / BOHR_ANG
    lines = [
        "DOM fixture",
        "synthetic",
        f"{len(f.atoms)} " + " ".join(map(str, f.origin / BOHR_ANG)),
    ]
    for n, v in zip(f.values.shape[:3], f.axes / BOHR_ANG):
        lines.append(str(n) + " " + " ".join(map(str, v)))
    for z, v in zip(f.atoms, a):
        lines.append(f"{z} 0 " + " ".join(map(str, v)))
    lines.append(" ".join(map(str, f.values[:, :, :, 0].ravel())))
    p.write_text("\n".join(lines))


e.utility = utility
s = make_server(e, port=0)
t = threading.Thread(target=s.serve_forever, daemon=True)
t.start()
try:
    env = dict(os.environ)
    result = subprocess.run(
        ["node", "tests/ui_dom.cjs", f"http://127.0.0.1:{s.server_port}"],
        cwd=root,
        env=env,
        timeout=45,
    )
    raise SystemExit(result.returncode)
finally:
    s.shutdown()
    s.server_close()
    e.close()
