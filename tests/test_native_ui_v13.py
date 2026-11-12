"""Native v1.3 interaction and embedded-input regressions (working Tk required)."""
from types import SimpleNamespace
import sys
import time

import numpy as np
from tkinter import font, ttk

from test_native_ui_v12 import native_app, app
from gausslook.parser import parse_input


def test_mouse_redraw_is_coalesced_and_reverses_without_queue(app, monkeypatch):
    viewer = app.viewer
    viewer.render()
    calls = []
    original = viewer.render
    def rendered():
        calls.append(viewer.zoom)
        original()
    monkeypatch.setattr(viewer, "render", rendered)
    viewer.zoom = 1
    for _ in range(5):
        viewer.wheel(1.12)
    pending = viewer._render_job
    for _ in range(5):
        viewer.wheel(1 / 1.12)
        assert viewer._render_job == pending
    assert np.isclose(viewer.zoom, 1)
    assert calls == []
    app.root.after(35, app.root.quit)
    app.root.mainloop()
    assert len(calls) == 1
    assert np.isclose(viewer.zoom, 1 / 1.12)
    assert viewer._render_job is None


def test_stale_wheel_events_are_dropped_and_timestamp_wrap_is_supported(app, monkeypatch):
    import gausslook.desktop as desktop
    viewer = app.viewer
    viewer.render()
    if sys.platform == "win32":
        import ctypes
        monkeypatch.setattr(ctypes.windll.kernel32, "GetTickCount", lambda: 0x20)
        stale = 0xffffff00
        recent = 0xfffffff0
    else:
        viewer._wheel_clock = 0xffffff00, time.monotonic() - .3
        stale, recent = 0xffffff01, 0x20
    before = viewer.zoom
    assert viewer.wheel(1.12, SimpleNamespace(time=stale)) == "break"
    assert viewer._pending_zoom is None and viewer._render_job is None
    viewer.wheel(1.12, SimpleNamespace(time=recent))
    viewer.render()
    assert viewer.zoom > before


def test_static_topology_cached_through_rotation_and_mode_frames(app, monkeypatch):
    import gausslook.desktop as desktop
    calls = []
    original = desktop.bonds
    def counted(atoms, coords):
        calls.append(1)
        return original(atoms, coords)
    monkeypatch.setattr(desktop, "bonds", counted)
    viewer = app.viewer
    coords = np.asarray(app.calc.frames[0]["coords"]) + 3
    viewer.set_structure(app.calc.atoms, coords, bond_coords=coords)
    for shift in (.01, .02, .03):
        viewer.angle[0] += .1
        viewer.set_structure(app.calc.atoms, coords + shift, bond_coords=coords)
    viewer.render()
    assert len(calls) == 1
    changed = coords.copy()
    changed[0, 0] += .2
    viewer.set_structure(app.calc.atoms, changed, bond_coords=changed)
    assert len(calls) == 2
    viewer.set_structure([], [], reset=True)
    assert len(viewer.screen) == len(viewer.screen_radii) == 0


def test_embedded_input_uses_current_frame_and_validates_without_dialog(app):
    ui = app.gaussian_ui
    assert "title" in ui["variables"] and "solvent" in ui["variables"]
    assert ui["notebook"].winfo_toplevel() is app.root
    ui["variables"]["method"].set("HF")
    ui["variables"]["basis"].set("STO-3G")
    ui["variables"]["cores"].set("6")
    ui["variables"]["title"].set("Inline current frame")
    ui["override"].set(False)
    app.calc.frames.append({"coords": (np.asarray(app.calc.frames[0]["coords"]) + 4).tolist()})
    app.frame = len(app.calc.frames) - 1
    text = ui["generate"]()
    parsed = parse_input(text, "inline.gjf", "fixture")[0]
    assert np.allclose(parsed.frames[0]["coords"], app.calc.frames[app.frame]["coords"])
    assert "%nprocshared=6\n" in text and "#p HF/STO-3G" in text
    saved = []
    app.save = lambda label, extension, text: saved.append(text)
    app.export_input()
    assert saved == [text]
    app.apply_language("en")
    assert ui["notebook"].tab(0, "text") == "Calculation / method"
    app.apply_language("ko")
    assert ui["notebook"].tab(0, "text") == "계산 / 방법"


def test_light_theme_graph_colors_and_korean_font_fallback(app):
    app.preferences.update(theme="light", font_family_ko="Arial")
    app.apply_language("ko")
    app.apply_appearance()
    assert ttk.Style(app.root).lookup("TButton", "foreground", ("active",)) == "#192d41"
    assert app.viewer.vector_color == "#8c4b00"
    if app.cjk_font:
        assert not app.cjk_font.startswith("@")
        assert font.nametofont("TkDefaultFont").actual("family").lower() == app.cjk_font.lower()
    text_items = [item for item in app.mo_graph.find_all() if app.mo_graph.type(item) == "text"]
    assert text_items
    assert all(app.mo_graph.itemcget(item, "font") == "TkDefaultFont" for item in text_items)
    assert "#c5d3e4" not in {app.mo_graph.itemcget(item, "fill") for item in text_items}
    app.preferences["font_family_ko"] = "Malgun Gothic"


def test_language_retains_selected_orbital_and_polarizability_source(app):
    app.calc.properties["polarizability_records"] = [
        {"tensor_au": np.eye(3).tolist(), "source": "static fixture", "frequency_au": 0},
        {"tensor_au": (2 * np.eye(3)).tolist(), "source": "response fixture", "frequency_au": .1},
    ]
    app.fill_polar()
    app.polar_source.current(1)
    app.update_polar()
    mo = app.mo_table.get_children()[-1]
    app.mo_table.selection_set(mo)
    app.mo_pick(None)
    app.status.configure(text="Selected calculation / task status")
    for language in ("en", "ko"):
        app.apply_language(language)
        assert app.mo.get() == mo
        assert app.mo_table.selection() == (mo,)
        assert app.polar_source.current() == 1
        assert app.status.cget("text") == "Selected calculation / task status"


def test_path_folders_and_extensions_have_distinct_tags(app, tmp_path):
    from gausslook.native_dialogs import PathFileDialog
    (tmp_path / "결과 폴더").mkdir()
    for name in ("a.log", "a.fchk", "a.cube", "a.gjf"):
        (tmp_path / name).touch()
    dialog = PathFileDialog(app, tmp_path)
    rows = {dialog.paths[i].name: dialog.tree.item(i) for i in dialog.tree.get_children() if i != "parent"}
    assert rows["결과 폴더"]["values"][0].startswith("[+] ")
    assert rows["결과 폴더"]["values"][1] == "폴더"
    assert [rows[name]["tags"][0] for name in ("a.log", "a.fchk", "a.cube", "a.gjf")] == ["log", "checkpoint", "cube", "input"]
    dialog.win.destroy()


def test_picking_uses_visible_atom_radius_and_settings_are_compact(app):
    viewer = app.viewer
    viewer.set_structure([6], [[0, 0, 0]], reset=True)
    viewer.style = "sphere"
    viewer.zoom = 15
    viewer.render()
    x, y = viewer.screen[0, :2]
    viewer.dragged = False
    viewer.release(SimpleNamespace(x=x + viewer.screen_radii[0] * .8, y=y))
    assert viewer.selected == [0]
    window = app.settings()
    app.root.update_idletasks()
    assert window.winfo_reqwidth() <= 640
    assert window.winfo_reqheight() <= 570
    window.destroy()
