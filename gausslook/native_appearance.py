"""Native preferences, bilingual labels and compact inspector sorting."""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, font, colorchooser, messagebox
from .model import COLORS, ELEMENTS
from .help_ui import install_tooltips


LABELS = {
    "파일 열기": "Open files", "데모": "Demo", "원본 새로고침": "Reload source",
    "프로젝트 저장": "Save project", "보고서 JSON": "Report JSON", "표시 설정": "Display settings",
    "도움말": "Help", "번호": "Labels", "중심": "Center", "선택 해제": "Clear selection",
    "▶ 경로": "Play path", "정지": "Stop", "현재 plot CSV 저장": "Save plot CSV",
    "배율": "Scale", "진폭": "Amplitude", "± XYZ": "Mode XYZ", "+ 표면": "+ Surface",
    "− 표면": "- Surface", "숨기기": "Hide", "실행": "Run", "원본 출력": "Source output",
    "지원 범위": "Feature status", "Gaussian 입력 저장": "Save Gaussian input",
    "선택 원자 삭제 → 새 구조": "Delete selected / new model",
    "SMILES → conformer (RDKit)": "SMILES to conformers (RDKit)",
    "공통 엔진 JSON 분석": "Shared analysis engine / JSON", "폰트": "Font",
    "글자 크기": "Font size", "적용": "Apply", "Gaussian 입력 설정…": "Gaussian input settings…",
    "X11 표면은 CPU preview입니다. 복잡한 표면은 웹 모드를 권장합니다.": "CPU surface preview. Use web mode for complex surfaces.",
    "파일을 열거나 데모를 선택하세요.": "Open a file or select Demo.",
    "프로젝트 탐색기": "PROJECT EXPLORER", "작업 취소": "Cancel task",
    "전하 / 다중도": "Charge / Multiplicity", "스펙트럼 그리기": "Plot",
}


def is_korean_font(family):
    return not family.startswith("@") and any(part in family.casefold() for part in (
        "cjk kr", "gulim", "nanum", "malgun", "sans kr", "source han sans k",
        "고딕", "돋움", "굴림", "바탕", "batang", "dotum"))


def sortable_value(value):
    """Sort numeric strings numerically; retain nonnumeric and missing values."""
    text = str(value).strip()
    if text.lower() in ("", "—", "–", "-", "none", "nan", "n/a", "unavailable", "missing"):
        return None
    try:
        atom = re.fullmatch(r"(\d+)\s+[A-Z][a-z]?", text)
        if atom:
            return (0, int(atom[1]))
        number = float(text.replace("−", "-").replace(",", "").replace("D", "E").replace("d", "e"))
        return (0, number) if math.isfinite(number) else None
    except ValueError:
        return (1, text.casefold())


def sort_tree(tree, column):
    """Reorder existing item IDs so selection callbacks keep their source identity."""
    descending = getattr(tree, "_sort_descending", {}).get(column, False)
    rows, missing = [], []
    for iid in tree.get_children(""):
        value = sortable_value(tree.set(iid, column))
        (missing if value is None else rows).append((value, iid))
    rows.sort(key=lambda item: item[0], reverse=descending)
    for position, (_, iid) in enumerate(rows + missing):
        tree.move(iid, "", position)
    for key in tree["columns"]:
        tree.heading(key, text=tree._heading_labels[key] + (" ▼" if descending else " ▲") if key == column else tree._heading_labels[key])
    tree._sort_descending = {column: not descending}


def install_sorting(tree):
    tree._heading_labels = {column: tree.heading(column, "text") for column in tree["columns"]}
    for column in tree["columns"]:
        tree.heading(column, command=lambda key=column: sort_tree(tree, key))


class NativeAppearance:
    def load_preferences(self):
        self.preference_path = self.engine.root / ".gausslook-ui.json"
        self.preferences = {"language": "ko", "theme": "dark", "font_family_ko": "Malgun Gothic", "font_family_en": "Arial", "font_size": 10,
                            "atom_scale": 1.0, "bond_scale": 1.0, "selection": "#09bfd6",
                            "element_colors": {}, "text_colors": {}, "last_directory": str(self.engine.root),
                            "background": "", "style": "ball", "labels": False, "hydrogens": True}
        try:
            saved = json.loads(self.preference_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                self.preferences.update({key: value for key, value in saved.items() if key in self.preferences})
                legacy = saved.get("font_family")
                if isinstance(legacy, str) and legacy and not legacy.startswith("@"):
                    key = "font_family_ko" if is_korean_font(legacy) else "font_family_en"
                    if key not in saved:
                        self.preferences[key] = legacy
        except (OSError, ValueError):
            pass
        if self.preferences["language"] not in ("ko", "en"):
            self.preferences["language"] = "ko"
        if self.preferences["theme"] not in ("dark", "light"):
            self.preferences["theme"] = "dark"
        for key, low, high, fallback in [("font_size", 8, 24, 10), ("atom_scale", .3, 3, 1), ("bond_scale", .3, 3, 1)]:
            try:
                value = float(self.preferences[key])
                self.preferences[key] = max(low, min(high, value)) if math.isfinite(value) else fallback
            except (TypeError, ValueError):
                self.preferences[key] = fallback
        self.preferences["font_size"] = int(self.preferences["font_size"])
        for key, fallback in (("font_family_ko", "Malgun Gothic"), ("font_family_en", "Arial")):
            value = self.preferences[key]
            if not isinstance(value, str) or not value.strip() or value.startswith("@"):
                self.preferences[key] = fallback
        for key in ("text_colors", "element_colors"):
            if not isinstance(self.preferences[key], dict):
                self.preferences[key] = {}
            self.preferences[key] = {str(k): v for k, v in self.preferences[key].items()
                                     if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v)}
        if not isinstance(self.preferences["background"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", self.preferences["background"]):
            self.preferences["background"] = ""
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(self.preferences["selection"])):
            self.preferences["selection"] = "#09bfd6"
        if self.preferences["style"] not in ("ball", "stick", "line", "sphere"):
            self.preferences["style"] = "ball"
        self.language = self.preferences["language"]
        self.language_pairs = dict(LABELS)

    def save_preferences(self):
        try:
            self.preference_path.write_text(json.dumps(self.preferences, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            self.status.configure(text=self.words("설정을 저장하지 못했습니다: ", "Could not save preferences: ") + str(exc))

    def words(self, ko, en):
        self.language_pairs[ko] = en
        return ko if self.cjk else en

    def apply_language(self, language=None):
        self.interrupt_animation()
        if language:
            self.language = language
        self.cjk = self.language == "ko"
        self.preferences["language"] = self.language
        lookup = {text: (ko, en) for ko, en in self.language_pairs.items() for text in (ko, en)}

        def translate(parent):
            for widget in parent.winfo_children():
                try:
                    value = widget.cget("text")
                    previous = getattr(widget, "_language_pair", ())
                    pair = previous if str(value) in previous else lookup.get(str(value))
                    if pair:
                        widget._language_pair = pair
                        widget.configure(text=pair[0 if self.cjk else 1])
                except tk.TclError:
                    pass
                if isinstance(widget, ttk.Notebook):
                    for tab in widget.tabs():
                        pair = lookup.get(widget.tab(tab, "text"))
                        if pair:
                            widget.tab(tab, text=pair[0 if self.cjk else 1])
                translate(widget)

        translate(self.root)
        names = ["Summary", "MO / Fields", "Vibrations", "Energy / Force", "Polarizability", "Quality / TS", "Properties", "Build / Input", "Tools", "Help"]
        current = self.panel_select.current()
        self.panel_names = {name: name if self.cjk else en for name, en in zip(self.panels, names)}
        self.panel_select["values"] = list(self.panel_names.values())
        self.panel_select.current(max(0, current))
        for name, label in self.panel_names.items():
            self.notebook.tab(self.panels[name], text=label)
        self.manual.set_language(not self.cjk)
        self.viewer.empty_text = self.words("GaussLook / 파일 열기 또는 데모", "GaussLook / Open files or Demo")
        self.apply_appearance()
        self.viewer.render()
        self.plot.english = not self.cjk
        self.plot.render()
        if self.calc:
            self.refresh_summary()
            self.fill_modes()
            self.fill_mos()
            self.fill_frame_table()
            self.fill_polar()
            self.update_frame_analysis()
        self.language_var.set("한국어" if self.cjk else "English")
        install_tooltips(self.root, english=not self.cjk)

    def apply_appearance(self, parent=None):
        settings = self.preferences
        dark = settings["theme"] == "dark"
        self.palette = {"bg": "#111820" if dark else "#eaf0f5", "panel": "#1a2532" if dark else "#ffffff",
                        "canvas": "#0b111a" if dark else "#f6f9fc", "fg": "#e0eaf5" if dark else "#192d41",
                        "muted": "#a3b6c9" if dark else "#506578", "entry": "#111b27" if dark else "#f4f7fb",
                        "accent": "#09bfd6" if dark else "#087a9a"}
        p = self.palette
        colors = settings["text_colors"]
        available = {name.casefold(): name for name in font.families(self.root) if not name.startswith("@")}
        fallback = (self.cjk_font or self.system_font) if self.cjk else available.get("arial", self.system_font)
        family = available.get(settings["font_family_ko" if self.cjk else "font_family_en"].casefold(), fallback)
        if self.cjk and not is_korean_font(family):
            family = self.cjk_font or family
        size = int(settings["font_size"])
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            font.nametofont(name).configure(family=family, size=size)
        self.title_font.configure(family=family, size=size + 7)
        style = ttk.Style(self.root)
        style.configure(".", background=p["panel"], foreground=colors.get("body", p["fg"]), font="TkDefaultFont")
        for name in ("TFrame", "TLabelframe", "TNotebook", "TNotebook.Tab", "TPanedwindow"):
            style.configure(name, background=p["panel"])
        style.configure("TButton", background=p["panel"], foreground=colors.get("button", p["fg"]), padding=(7, 4), width=0)
        style.map("TButton", background=[("active", p["entry"])], foreground=[("disabled", p["muted"])])
        style.map("TButton", foreground=[("disabled", p["muted"]), ("active", colors.get("button", p["fg"]))])
        for name in ("TCheckbutton", "TRadiobutton"):
            style.configure(name, background=p["panel"], foreground=p["fg"], indicatorcolor=p["entry"])
            style.map(name, background=[("active", p["panel"])], foreground=[("disabled", p["muted"]), ("active", p["fg"])], indicatorcolor=[("selected", p["accent"]), ("!selected", p["entry"])])
        for name in ("TEntry", "TCombobox", "TSpinbox"):
            style.configure(name, fieldbackground=p["entry"], foreground=colors.get("input", p["fg"]), insertcolor=p["fg"])
            style.map(name, fieldbackground=[("readonly", p["entry"])], foreground=[("readonly", colors.get("input", p["fg"]))])
        style.configure("Treeview", background=p["entry"], fieldbackground=p["entry"], foreground=p["fg"], rowheight=max(14, font.nametofont("TkDefaultFont").metrics("linespace") + 1), borderwidth=0)
        style.configure("Treeview.Heading", background=p["panel"], foreground=p["muted"], padding=(3, 2))
        style.map("Treeview", background=[("selected", "#075c7c")], foreground=[("selected", "#ffffff")])
        style.map("TNotebook.Tab", background=[("selected", p["entry"])], foreground=[("selected", p["accent"])])
        self.root.configure(background=p["bg"])
        self.root.option_add("*TCombobox*Listbox.background", p["entry"])
        self.root.option_add("*TCombobox*Listbox.foreground", p["fg"])
        self.root.option_add("*TCombobox*Listbox.font", "TkDefaultFont")

        def walk(widget):
            if isinstance(widget, tk.Text):
                widget.configure(bg=p["entry"], fg=colors.get("input", p["fg"]), insertbackground=p["fg"], font="TkTextFont", selectbackground="#075c7c")
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=p["entry"], fg=p["fg"], selectbackground="#075c7c", selectforeground="#ffffff", highlightthickness=0, font="TkDefaultFont")
            elif isinstance(widget, tk.Scale):
                widget.configure(bg=p["panel"], fg=p["fg"], troughcolor=p["entry"], highlightthickness=0)
            elif isinstance(widget, tk.Canvas):
                widget.configure(bg=p["canvas"])
            for child in widget.winfo_children():
                walk(child)
        walk(parent or self.root)
        if hasattr(self, "status"):
            self.status.configure(background=p["entry"], foreground=colors.get("status", p["accent"]))
        if hasattr(self, "viewer"):
            self.viewer.configure(bg=settings["background"] or p["canvas"])
            self.viewer.atom_scale = settings["atom_scale"]
            self.viewer.bond_scale = settings["bond_scale"]
            self.viewer.element_colors = settings["element_colors"]
            self.viewer.selection_color = settings["selection"]
            self.viewer.label_color = colors.get("label", p["fg"])
            self.viewer.vector_color = "#ffd078" if dark else "#8c4b00"
            self.viewer.render()
        if hasattr(self, "plot"):
            self.plot.foreground = p["muted"]
            self.plot.accent = p["accent"]
            self.plot.render()
        if hasattr(self, "mo_graph"):
            self.draw_mo_graph()

    def settings(self):
        win = tk.Toplevel(self.root)
        win.title(self.words("표시 설정", "Display settings"))
        win.geometry("620x550")
        win.minsize(540, 480)
        before = copy.deepcopy(self.preferences)
        outer = ttk.Frame(win, padding=8)
        outer.pack(fill="both", expand=True)
        actions = ttk.Frame(outer)
        actions.pack(side="bottom", fill="x", pady=5)
        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)
        general, elements = ttk.Frame(notebook, padding=6), ttk.Frame(notebook, padding=6)
        notebook.add(general, text=self.words("글꼴 / 화면", "Font / display"))
        notebook.add(elements, text=self.words("원소별 색상", "Element colors"))
        variables = {key: tk.StringVar(value=str(self.preferences[key])) for key in ("font_family_ko", "font_family_en", "font_size", "theme", "atom_scale", "bond_scale")}
        families = sorted(name for name in set(font.families(self.root)) if not name.startswith("@"))
        entries = [("한글 글꼴", "Korean font", "font_family_ko", list(dict.fromkeys(["Malgun Gothic", "Gulim", *filter(is_korean_font, families)]))), ("영문 글꼴", "English font", "font_family_en", ["Arial", "Calibri"]), ("크기 pt", "Size pt", "font_size", list(range(8, 25))), ("모드", "Theme", "theme", ["dark", "light"]), ("원자 크기", "Atom scale", "atom_scale", ["0.5", "0.75", "1.0", "1.25", "1.5", "2.0"]), ("결합 굵기", "Bond scale", "bond_scale", ["0.5", "0.75", "1.0", "1.25", "1.5", "2.0"])]
        for row, (ko, en, key, values) in enumerate(entries):
            ttk.Label(general, text=self.words(ko, en)).grid(row=row, column=0, sticky="w", pady=2, padx=3)
            ttk.Combobox(general, textvariable=variables[key], values=values, width=30, state="readonly" if key.startswith("font_family") else "normal").grid(row=row, column=1, sticky="ew", pady=2)
        general.columnconfigure(1, weight=1)
        ttk.Label(general, text=self.words("Malgun Gothic = 맑은 고딕 · Gulim = 굴림\n글꼴은 실행 서버에 설치되어 있어야 합니다.", "Fonts must be installed on the native/X11 server.\nMissing fonts use an installed fallback."), wraplength=540).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        def choose_color(key):
            value = colorchooser.askcolor(parent=win, initialcolor=self.preferences["text_colors"].get(key, self.palette["fg"]))[1]
            if value:
                self.preferences["text_colors"][key] = value
                self.apply_appearance()

        for index, (key, ko, en) in enumerate([("body", "본문 색상", "Body color"), ("button", "버튼 글자색", "Button text color"), ("input", "입력 글자색", "Input text color"), ("status", "상태 글자색", "Status text color"), ("label", "3D 라벨 색상", "3D label color")]):
            ttk.Button(general, text=self.words(ko, en), command=lambda key=key: choose_color(key)).grid(row=7 + index // 2, column=index % 2, sticky="ew", padx=4, pady=4)

        def selection_color():
            value = colorchooser.askcolor(parent=win, initialcolor=self.preferences["selection"])[1]
            if value:
                self.preferences["selection"] = value
                self.apply_appearance()
        ttk.Button(general, text=self.words("선택 강조 색상", "Selection color"), command=selection_color).grid(row=8, column=1, sticky="ew", padx=4)
        def background_color():
            value = colorchooser.askcolor(parent=win, initialcolor=self.preferences["background"] or self.palette["canvas"])[1]
            if value:
                self.preferences["background"] = value
                self.apply_appearance()
        ttk.Button(general, text=self.words("뷰어 배경색", "Viewer background"), command=background_color).grid(row=10, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(general, text=self.words("테마 기본색 복원", "Reset theme colors"), command=lambda: (self.preferences.update(background="", text_colors={}), self.apply_appearance())).grid(row=10, column=1, sticky="ew", padx=4)
        tree = ttk.Treeview(elements, columns=("z", "element", "color"), show="headings", height=10)
        for key, label in [("z", "Z"), ("element", "Element"), ("color", "RGB")]:
            tree.heading(key, text=label)
            tree.column(key, width=150)
        tree.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(elements, command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        install_sorting(tree)

        def fill():
            tree.delete(*tree.get_children())
            for z, symbol in enumerate(ELEMENTS[1:], 1):
                tree.insert("", "end", iid=str(z), values=(z, symbol, self.preferences["element_colors"].get(str(z), COLORS.get(z, "#b1a3c7"))))

        def element_color():
            if not tree.selection():
                return
            z = tree.selection()[0]
            value = colorchooser.askcolor(parent=win, initialcolor=tree.set(z, "color"))[1]
            if value:
                self.preferences["element_colors"][z] = value
                fill()
                self.apply_appearance()
        ttk.Button(elements, text=self.words("선택 원소 색상", "Selected element color"), command=element_color).pack(fill="x", pady=4)
        ttk.Button(elements, text=self.words("원소 색상 초기화", "Reset element colors"), command=lambda: (self.preferences.update(element_colors={}), fill(), self.apply_appearance())).pack(fill="x")
        tree.bind("<Double-1>", lambda event: element_color())
        fill()

        def preview():
            size = int(variables["font_size"].get())
            if not 8 <= size <= 24:
                raise ValueError("Font size: 8–24 pt")
            if variables["theme"].get() not in ("dark", "light"):
                raise ValueError("Theme: dark / light")
            scales = {key: float(variables[key].get()) for key in ("atom_scale", "bond_scale")}
            if not all(math.isfinite(value) and .3 <= value <= 3 for value in scales.values()):
                raise ValueError("Atom / bond scales: 0.3–3.0")
            fonts = {key: variables[key].get().strip() for key in ("font_family_ko", "font_family_en")}
            if any(not value or value.startswith("@") for value in fonts.values()):
                raise ValueError("Choose a horizontal font family.")
            self.preferences.update(**fonts, font_size=size, theme=variables["theme"].get(), **scales)
            self.apply_appearance()

        def apply():
            preview()
            self.save_preferences()
            win.destroy()

        def cancel():
            self.preferences = before
            self.apply_appearance()
            win.destroy()
        ttk.Button(actions, text=self.words("적용 / 저장", "Apply / save"), command=self.safe(apply)).pack(side="right", padx=4)
        ttk.Button(actions, text=self.words("미리보기", "Preview"), command=self.safe(preview)).pack(side="right", padx=4)
        ttk.Button(actions, text=self.words("취소", "Cancel"), command=cancel).pack(side="right", padx=4)
        win.protocol("WM_DELETE_WINDOW", cancel)
        self.apply_appearance(win)
        install_tooltips(win, english=not self.cjk)
        return win
