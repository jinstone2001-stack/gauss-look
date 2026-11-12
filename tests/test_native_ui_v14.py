"""Native v1.4 language/font and animation regressions (working Tk required)."""
from tkinter import font, ttk

import numpy as np
import pytest

from test_native_ui_v12 import native_app, app
from test_analysis_v11 import enriched_fchk
from gausslook.native_dialogs import PathFileDialog


def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)


@pytest.mark.parametrize("korean, english", [("Malgun Gothic", "Arial"), ("Gulim", "Calibri")])
def test_language_roundtrips_restore_each_font_and_labels(app, korean, english):
    available = {name.casefold(): name for name in font.families(app.root)}
    app.preferences.update(font_family_ko=korean, font_family_en=english)
    original = app.calc.public()
    for _ in range(3):
        for language, family, label in (("ko", korean, "파일 열기"), ("en", english, "Open files")):
            app.apply_language(language)
            actual = font.nametofont("TkDefaultFont").actual("family")
            if family.casefold() in available:
                assert actual.casefold() == family.casefold()
            else:
                assert actual
            assert not actual.startswith("@")
            assert app.title_font.actual("family") == actual
            assert any(isinstance(w, ttk.Button) and w.cget("text") == label for w in descendants(app.root))
    assert app.calc.public() == original
    app.save_preferences()
    app.load_preferences()
    assert app.preferences["font_family_ko"] == korean
    assert app.preferences["font_family_en"] == english


def test_settings_default_size_is_integer_and_saves_unchanged(app):
    app.preferences["font_size"] = 10
    window = app.settings()
    try:
        controls = [w for w in descendants(window) if isinstance(w, ttk.Combobox)]
        size = next(w for w in controls if tuple(map(str, w["values"])) == tuple(map(str, range(8, 25))))
        assert size.get() == "10"
        assert any("Gulim" in w["values"] for w in controls)
        assert any("Calibri" in w["values"] for w in controls)
        save = next(w for w in descendants(window) if isinstance(w, ttk.Button) and w.cget("text") == "적용 / 저장")
        save.invoke()
        assert app.preferences["font_size"] == 10
        assert not window.winfo_exists()
    finally:
        if window.winfo_exists():
            window.destroy()


def test_file_picker_open_is_left_of_cancel(app, tmp_path):
    dialog = PathFileDialog(app, tmp_path)
    try:
        dialog.win.transient("")
        dialog.win.deiconify()
        dialog.win.update()
        buttons = {w.cget("text"): w for w in descendants(dialog.win) if isinstance(w, ttk.Button)}
        assert buttons["선택 파일 열기"].winfo_x() < buttons["취소"].winfo_x()
    finally:
        dialog.win.destroy()


@pytest.mark.parametrize("operation", ["action", "panel", "task"])
def test_checkpoint_animation_stops_before_other_work(app, tmp_path, monkeypatch, operation):
    checkpoint = tmp_path / "modes.fchk"
    checkpoint.write_text(enriched_fchk())
    app.load(app.engine.load(checkpoint)["ids"][0])
    app.play_mode(0)
    app.root.after(150, app.root.quit)
    app.root.mainloop()
    assert app.animation is not None
    reference = np.asarray(app.calc.frames[app.frame]["coords"])
    assert not np.allclose(app.viewer.coords, reference)
    captured = []
    if operation == "action":
        app.safe(lambda: captured.append(app.viewer.coords.copy()))()
        assert np.allclose(captured[0], reference)
    elif operation == "panel":
        app.select_panel("MO·표면")
    else:
        monkeypatch.setattr(app.engine, "task", lambda tid: {"title": "fixture", "progress": 100, "status": "done", "result": {}})
        app.watch("fixture")
    assert app.animation is None
    assert np.allclose(app.viewer.coords, reference)
    app.root.after(90, app.root.quit)
    app.root.mainloop()
    assert np.allclose(app.viewer.coords, reference)
