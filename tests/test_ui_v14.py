"""Preference migration and real RDKit builder regressions."""
import json
import time
from types import SimpleNamespace

import numpy as np
import pytest

from gausslook.engine import Engine
from gausslook.native_appearance import NativeAppearance


@pytest.mark.parametrize("legacy, key", [("Arial", "font_family_en"), ("Gulim", "font_family_ko")])
def test_preferences_migrate_fonts_and_integer_size(tmp_path, legacy, key):
    (tmp_path / ".gausslook-ui.json").write_text(
        json.dumps({"font_size": "10.0", "font_family": legacy}), encoding="utf-8")
    appearance = NativeAppearance()
    appearance.engine = SimpleNamespace(root=tmp_path)
    appearance.load_preferences()
    assert appearance.preferences[key] == legacy
    assert type(appearance.preferences["font_size"]) is int
    assert str(appearance.preferences["font_size"]) == "10"
    (tmp_path / ".gausslook-ui.json").write_text(json.dumps({
        "font_family": legacy, key: "Calibri" if key.endswith("en") else "Malgun Gothic",
        "font_size": "nan"}), encoding="utf-8")
    appearance.load_preferences()
    assert appearance.preferences[key] != legacy
    assert appearance.preferences["font_size"] == 10


def test_builder_generates_real_rdkit_coordinates_and_input(tmp_path):
    engine = Engine(tmp_path)
    try:
        tid = engine.action("smiles", smiles="CCO", conformers=3)["task"]
        deadline = time.monotonic() + 45
        while engine.task(tid)["status"] in ("queued", "running") and time.monotonic() < deadline:
            time.sleep(.02)
        task = engine.task(tid)
        assert task["status"] == "done", task
        calculation = engine.get(task["result"]["ids"][0])
        assert calculation.atoms.count(6) == 2 and calculation.atoms.count(8) == 1
        assert len(calculation.frames) == 3
        coords = np.asarray(calculation.frames[0]["coords"])
        assert coords.shape == (9, 3) and np.isfinite(coords).all()
        assert np.linalg.norm(coords[0] - coords[1]) > 1
        assert calculation.properties["conformer_method"] == "MMFF94"
        assert "#p B3LYP/def2SVP" in engine.action("input", calculation.id)["text"]
        bad = engine.action("smiles", smiles="not a smiles")["task"]
        deadline = time.monotonic() + 5
        while engine.task(bad)["status"] in ("queued", "running") and time.monotonic() < deadline:
            time.sleep(.02)
        assert engine.task(bad)["status"] == "error"
    finally:
        engine.close()
