"""Native UI regressions. A working Tk display is needed for the GUI cases."""
import json
from pathlib import Path
import numpy as np
import pytest

from gausslook.engine import Engine
from gausslook.parser import parse_input
from gausslook.native_appearance import sort_tree


@pytest.fixture(scope="module")
def native_app(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("native-ui")
    tk = pytest.importorskip("tkinter")
    original = tk.Tk
    def hidden_root(*args, **kwargs):
        try:
            root = original(*args, **kwargs)
        except tk.TclError as exc:
            pytest.skip(f"A working Tk display is required: {exc}")
        root.withdraw()
        return root
    from gausslook.desktop import App
    engine = Engine(tmp_path)
    engine.demo()
    try:
        tk.Tk = hidden_root
        value = App(engine)
    except BaseException:
        engine.close()
        raise
    finally:
        tk.Tk = original
    value.callback_errors = []
    value.root.report_callback_exception = lambda *error: value.callback_errors.append(error)
    yield value
    assert not value.callback_errors
    value.close()


@pytest.fixture
def app(native_app):
    value = native_app
    value.stop()
    value.load(value.engine.demo()["ids"][0])
    value.preferences.update(theme="dark", background="")
    value.apply_language("ko")
    value.apply_appearance()
    return value


def test_language_and_theme_preserve_calculation_and_inputs(app):
    before = app.calc.public()
    app.route.delete(0, "end")
    app.route.insert(0, "#p HF/STO-3G")
    app.smiles.delete(0, "end")
    app.smiles.insert(0, "CO")
    app.apply_language("en")
    assert app.panel_select["values"][0] == "Summary"
    assert app.manual.english
    assert "Language, theme" in app.manual.topics["values"][0]
    app.preferences["theme"] = "light"
    app.apply_appearance()
    assert app.viewer.cget("background") == "#f6f9fc"
    app.preferences["background"] = "#112233"
    app.apply_appearance()
    assert app.viewer.cget("background") == "#112233"
    app.apply_language("ko")
    assert app.panel_select["values"][0] == "개요"
    assert not app.manual.english
    assert app.route.get() == "#p HF/STO-3G" and app.smiles.get() == "CO"
    assert app.calc.public() == before
    app.save_preferences()
    saved = json.loads(app.preference_path.read_text(encoding="utf-8"))
    assert saved["language"] == "ko" and saved["theme"] == "light"


def test_sorted_native_mode_rows_keep_source_identity(app):
    app.calc.modes[0]["frequency_cm1"] = 100.0
    app.calc.modes[1]["frequency_cm1"] = -20.0
    app.calc.modes[2]["frequency_cm1"] = 2.0
    app.fill_modes()
    sort_tree(app.mode_table, "cm-1")
    assert list(app.mode_table.get_children()) == ["1", "2", "0"]
    sort_tree(app.mode_table, "cm-1")
    assert list(app.mode_table.get_children()) == ["0", "2", "1"]
    selected = []
    app.play_mode = lambda index: selected.append(index)
    app.mode_table.selection_set("2")
    app.root.update()
    assert selected[-1] == 2


def test_sorted_native_missing_energy_stays_last(app):
    app.calc.frames[0]["energy_hartree"] = -10.0
    coords = app.calc.frames[0]["coords"]
    app.calc.frames.extend([{"coords": coords, "energy_hartree": -2.0}, {"coords": coords}])
    app.fill_frame_table()
    sort_tree(app.frame_table, "Energy / Eh")
    assert list(app.frame_table.get_children()) == ["0", "1", "2"]
    sort_tree(app.frame_table, "Energy / Eh")
    assert list(app.frame_table.get_children()) == ["1", "0", "2"]
    app.frame_table.selection_set("1")
    app.root.update()
    assert app.frame == 1


def test_native_path_paste_parent_and_back(app, tmp_path):
    from gausslook.native_dialogs import PathFileDialog
    folder = tmp_path / "계산 결과" / "nested folder"
    folder.mkdir(parents=True)
    dialog = PathFileDialog(app)
    dialog.path.set(str(folder))
    dialog.go()
    assert dialog.current == folder
    assert dialog.tree.item("parent", "values")[0] == ".."
    dialog.tree.selection_set("parent")
    dialog.activate()
    assert dialog.current == folder.parent
    dialog.back()
    assert dialog.current == folder
    source = folder / "sample.xyz"
    source.write_text("1\nfixture\nH 0 0 0\n")
    dialog.path.set(str(source))
    dialog.go()
    assert dialog.result == (str(source),)


def test_native_gaussian_form_roundtrip_and_route_override(app):
    from gausslook.native_dialogs import gaussian_dialog
    app.calc.frames.append({"coords": (np.array(app.calc.frames[0]["coords"]) + 2).tolist()})
    app.frame = 1
    window = gaussian_dialog(app)
    controls = window.gaussian_ui
    variables = controls["variables"]
    for key, value in {"title":"Selected frame", "method":"HF", "basis":"STO-3G", "job":"SP", "cores":"8", "memory":"12GB", "checkpoint":"chosen.chk"}.items():
        variables[key].set(value)
    text = controls["generate"]()
    assert text.startswith("%mem=12GB\n%nprocshared=8\n%chk=chosen.chk\n#p HF/STO-3G")
    parsed = parse_input(text, "chosen.gjf", "fixture")[0]
    assert np.allclose(parsed.frames[0]["coords"], app.calc.frames[1]["coords"])
    controls["override"].set(True)
    variables["route"].set("#p B3LYP/6-31G(d) Freq")
    assert "#p B3LYP/6-31G(d) Freq\n" in controls["generate"]()
    window.destroy()
    saved = []
    app.save = lambda label, extension, text: saved.append(text)
    app.export_input()
    assert saved[0].startswith("%mem=12GB\n%nprocshared=8\n%chk=chosen.chk\n#p B3LYP/6-31G(d) Freq")


def test_catalog_has_all_english_labels():
    docs = Path(__file__).resolve().parent.parent / "docs"
    items = json.loads((docs / "feature_status.json").read_text(encoding="utf-8"))
    labels = json.loads((docs / "feature_labels_en.json").read_text(encoding="utf-8"))
    assert len(items) == len(labels) == 140
    assert set(labels) == {item["id"] for item in items}
