"""Native path browser and structured Gaussian input form (no web dependency)."""
from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from .help_ui import Tooltip, install_tooltips


class PathFileDialog:
    """A server-side file picker with an editable path and explicit parent row."""

    def __init__(self, app, initial=None):
        self.app = app
        self.result = ()
        self.current = Path(initial or app.engine.root).expanduser().resolve()
        self.history = []
        self.win = tk.Toplevel(app.root)
        self.win.title(app.words("파일 열기 · 서버 경로", "Open files · server path"))
        self.win.geometry("820x560")
        self.win.transient(app.root)
        outer = ttk.Frame(self.win, padding=10)
        outer.pack(fill="both", expand=True)
        row = ttk.Frame(outer)
        row.pack(fill="x")
        self.back_button = ttk.Button(row, text=app.words("뒤로", "Back"), command=self.back)
        self.back_button.pack(side="left")
        ttk.Button(row, text=".. ↑", command=lambda: self.navigate(self.current.parent)).pack(side="left", padx=4)
        self.path = tk.StringVar(value=str(self.current))
        self.entry = ttk.Entry(row, textvariable=self.path)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.go)
        self.entry._help_tooltip = Tooltip(self.entry, app.words(
            "폴더 경로를 입력하거나 붙여넣고 Enter를 누릅니다. 파일 경로도 바로 열 수 있습니다.",
            "Type or paste a directory and press Enter. A full file path can also be opened directly."))
        ttk.Button(row, text=app.words("이동", "Go"), command=self.go).pack(side="left", padx=4)
        area = ttk.Frame(outer)
        area.pack(fill="both", expand=True, pady=8)
        self.tree = ttk.Treeview(area, columns=("name", "type", "size"), show="headings", selectmode="extended")
        for key, label, width in [("name", app.words("이름", "Name"), 470), ("type", app.words("종류", "Type"), 100), ("size", "Bytes", 100)]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(area, command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        dark = app.preferences["theme"] == "dark"
        for tag, color in {"folder": "#69c9ff" if dark else "#07568a", "log": "#88dbc2" if dark else "#14664c", "checkpoint": "#c9adff" if dark else "#6b36a6", "cube": "#edbd7c" if dark else "#86540a", "input": "#efb7cb" if dark else "#9e3152"}.items():
            self.tree.tag_configure(tag, foreground=color)
        self.tree.bind("<Double-1>", self.activate)
        self.tree.bind("<Return>", self.activate)
        self.note = ttk.Label(outer, wraplength=770)
        self.note.pack(fill="x")
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text=app.words("취소", "Cancel"), command=self.win.destroy).pack(side="right", padx=5)
        ttk.Button(actions, text=app.words("선택 파일 열기", "Open selected files"), command=self.accept).pack(side="right")
        self.navigate(self.current, remember=False)
        app.apply_appearance(self.win)
        install_tooltips(self.win, english=not app.cjk)
        self.win.grab_set()
        self.entry.focus_set()

    def navigate(self, target, remember=True):
        try:
            target = Path(target).expanduser().resolve()
            entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
        except (OSError, ValueError) as exc:
            messagebox.showerror("GaussLook", str(exc), parent=self.win)
            return False
        if remember and target != self.current:
            self.history.append(self.current)
        self.current = target
        self.path.set(str(target))
        self.tree.delete(*self.tree.get_children())
        self.paths = {"parent": target.parent}
        self.tree.insert("", "end", iid="parent", values=("..", self.app.words("상위 폴더", "Parent directory"), ""), tags=("folder",))
        for index, entry in enumerate(entries):
            iid = f"path-{index}"
            self.paths[iid] = entry
            try:
                directory = entry.is_dir()
                size = "" if directory else entry.stat().st_size
            except OSError:
                directory, size = False, "?"
            suffix = entry.suffix.lower()
            tag = "folder" if directory else {".log": "log", ".out": "log", ".chk": "checkpoint", ".fchk": "checkpoint", ".fch": "checkpoint", ".cube": "cube", ".cub": "cube", ".gjf": "input", ".com": "input"}.get(suffix, "")
            kind = self.app.words("폴더", "Directory") if directory else suffix or self.app.words("파일", "File")
            self.tree.insert("", "end", iid=iid, values=(("[+] " if directory else "") + entry.name, kind, size), tags=(tag,))
        self.back_button.configure(state="normal" if self.history else "disabled")
        self.note.configure(text=self.app.words("Ctrl / Shift: 여러 파일 선택 · 폴더 / .. 더블클릭: 이동", "Ctrl / Shift: select multiple files · Double-click a directory / .. to navigate"))
        return True

    def go(self, event=None):
        raw = os.path.expandvars(self.path.get().strip().strip('"'))
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = self.current / candidate
        if candidate.is_file():
            self.result = (str(candidate.resolve()),)
            self.win.destroy()
        else:
            self.navigate(candidate)
        return "break"

    def back(self):
        if self.history:
            previous = self.history[-1]
            if self.navigate(previous, remember=False):
                self.history.pop()
                self.back_button.configure(state="normal" if self.history else "disabled")

    def activate(self, event=None):
        selected = self.tree.selection()
        if len(selected) == 1 and self.paths[selected[0]].is_dir():
            self.navigate(self.paths[selected[0]])
        else:
            self.accept()
        return "break"

    def accept(self):
        selected = [self.paths[i] for i in self.tree.selection()]
        if len(selected) == 1 and selected[0].is_dir():
            self.navigate(selected[0])
            return
        files = [str(p) for p in selected if p.is_file()]
        if files:
            self.result = tuple(files)
            self.win.destroy()


def gaussian_dialog(app, parent=None):
    embedded = parent is not None
    if not embedded and (not app.calc or not app.calc.frames):
        raise ValueError(app.words("먼저 구조를 여세요.", "Open a structure first."))
    win = ttk.Frame(parent) if embedded else tk.Toplevel(app.root)
    if embedded:
        win.pack(fill="both", expand=True)
    else:
        win.transient(app.root)
        win.title(app.words("Gaussian 16 입력 설정", "Gaussian 16 input settings"))
        win.geometry("810x670")
        win.minsize(650, 570)
    outer = ttk.Frame(win, padding=4)
    outer.pack(fill="both", expand=True)
    actions = ttk.Frame(outer)
    actions.pack(side="bottom", fill="x", pady=4)
    notebook = ttk.Notebook(outer)
    notebook.pack(fill="both", expand=True)
    form, advanced, preview_frame = [ttk.Frame(notebook, padding=4) for _ in range(3)]
    for panel, label in [(form, app.words("계산 / 방법", "Calculation / method")), (advanced, app.words("고급 / 추가 입력", "Advanced / additional")), (preview_frame, app.words("입력 미리보기", "Input preview"))]:
        notebook.add(panel, text=label)
    defaults = {"title": app.calc.name if app.calc else "GaussLook", "checkpoint": "gausslook.chk", "memory": "4GB", "cores": "4", "charge": "0", "multiplicity": "1", "method": "B3LYP", "basis": "def2SVP", "job": "Opt Freq", "scf": "XQC", "grid": "UltraFine", "dispersion": "None", "solvent": "None", "extra": "", "route": "#p B3LYP/def2SVP Opt Freq"}
    defaults.update(getattr(app, "input_options", {}))
    if app.calc and defaults.pop("_calculation_id", None) != app.calc.id:
        defaults["title"] = app.calc.name
    if not embedded:
        defaults["charge"], defaults["multiplicity"], defaults["route"] = app.charge.get(), app.mult.get(), app.route.get()
    override = tk.BooleanVar(value=bool(defaults.pop("_override", False)))
    variables = {key: tk.StringVar(value=value) for key, value in defaults.items() if not key.startswith("_")}
    fields = [("제목", "Title", "title", None), ("Checkpoint", "Checkpoint", "checkpoint", None), ("메모리", "Memory", "memory", None), ("CPU 코어", "CPU cores", "cores", None), ("전하", "Charge", "charge", None), ("다중도", "Multiplicity", "multiplicity", None), ("계산 종류", "Job type", "job", ["SP", "Opt", "Freq", "Opt Freq", "Opt=(TS,CalcFC) Freq", "IRC=(CalcFC)", "TD(NStates=10)"]), ("계산 방법", "Method", "method", ["HF", "B3LYP", "PBE1PBE", "M062X", "wB97XD", "MP2", "CCSD(T)"]), ("기저함수", "Basis set", "basis", ["def2SVP", "def2TZVP", "6-31G(d)", "6-311++G(d,p)", "cc-pVDZ", "Gen", "GenECP"]), ("SCF 보조", "SCF aid", "scf", ["None", "XQC", "QC", "Tight", "VeryTight"]), ("적분격자", "Integration grid", "grid", ["None", "UltraFine", "SuperFineGrid", "FineGrid"]), ("분산 보정", "Dispersion", "dispersion", ["None", "GD3", "GD3BJ"]), ("용매 (SMD)", "Solvent (SMD)", "solvent", ["None", "Water", "Acetonitrile", "Toluene", "DMSO", "THF", "Chloroform", "Dichloromethane"])]
    for row, (ko, en, key, choices) in enumerate(fields):
        ttk.Label(form, text=app.words(ko, en)).grid(row=row, column=0, sticky="w", padx=3, pady=2)
        widget = ttk.Combobox(form, textvariable=variables[key], values=choices) if choices else ttk.Entry(form, textvariable=variables[key])
        widget.grid(row=row, column=1, sticky="ew", padx=3, pady=2)
        if embedded and key in ("charge", "multiplicity"):
            setattr(app, "charge" if key == "charge" else "mult", widget)
    form.columnconfigure(1, weight=1)
    ttk.Label(form, text=app.words("현재 frame 좌표 · Gen / GenECP: 고급 탭", "Selected frame · Gen / GenECP: Advanced tab"), wraplength=360 if embedded else 650).grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=4)
    ttk.Label(advanced, text=app.words("추가 route 키워드", "Additional route keywords")).pack(anchor="w")
    ttk.Entry(advanced, textvariable=variables["extra"]).pack(fill="x", pady=4)
    ttk.Checkbutton(advanced, text=app.words("전체 route 직접 지정 (위의 방법 설정 대신 사용)", "Override complete route (replaces method settings above)"), variable=override).pack(anchor="w", pady=8)
    route_entry = ttk.Entry(advanced, textvariable=variables["route"])
    route_entry.pack(fill="x")
    if embedded:
        app.route = route_entry
    ttk.Label(advanced, text=app.words("좌표 뒤에 추가할 입력 블록", "Input blocks after coordinates")).pack(anchor="w", pady=(12, 4))
    additional = tk.Text(advanced, height=12, width=36 if embedded else 80, wrap="none", font="TkTextFont")
    additional.pack(fill="both", expand=True)
    additional.insert("1.0", defaults.get("additional", "" if embedded else app.additional.get("1.0", "end-1c")))
    if embedded:
        app.additional = additional
    preview = tk.Text(preview_frame, width=36 if embedded else 80, wrap="none", font="TkTextFont")
    preview.pack(fill="both", expand=True)

    def gather():
        if not app.calc or not app.calc.frames:
            raise ValueError(app.words("먼저 구조를 여세요.", "Open a structure first."))
        values = {key: variable.get().strip() for key, variable in variables.items()}
        if override.get():
            route = values["route"]
        else:
            if not values["method"] or not values["basis"]:
                raise ValueError(app.words("방법과 기저함수를 입력하세요.", "Enter a method and basis set."))
            parts = ["#p", f'{values["method"]}/{values["basis"]}', "" if values["job"] == "SP" else values["job"]]
            for key, pattern in [("scf", "SCF={}"), ("grid", "Integral={}"), ("dispersion", "EmpiricalDispersion={}"), ("solvent", "SCRF=(SMD,Solvent={})")]:
                if values[key] and values[key] != "None" and (key != "grid" or values["method"] not in ("HF", "MP2", "CCSD(T)")):
                    parts.append(pattern.format(values[key]))
            parts.append(values["extra"])
            route = " ".join(p for p in parts if p)
        app.input_options = {**values, "additional": additional.get("1.0", "end-1c"), "_override": override.get(), "_calculation_id": app.calc.id}
        return dict(route=route, title=values["title"], memory=values["memory"], cores=int(values["cores"]), checkpoint=values["checkpoint"], charge=int(values["charge"]), multiplicity=int(values["multiplicity"]), additional=additional.get("1.0", "end-1c"), frame=app.frame)

    def generate():
        params = gather()
        result = app.engine.action("input", app.calc.id, **params)
        if not embedded:
            for key, value in app.input_options.items():
                if key in app.gaussian_ui["variables"]:
                    app.gaussian_ui["variables"][key].set(value)
            app.gaussian_ui["override"].set(override.get())
            for entry, key in [(app.route, "route"), (app.charge, "charge"), (app.mult, "multiplicity")]:
                entry.delete(0, "end")
                entry.insert(0, str(params[key]))
            app.additional.delete("1.0", "end")
            app.additional.insert("1.0", params["additional"])
        preview.delete("1.0", "end")
        preview.insert("1.0", result["text"])
        notebook.select(preview_frame)
        return result["text"]

    def save_input():
        text = generate()
        app.save("Gaussian input", ".gjf", text)

    ttk.Button(actions, text=app.words("입력 미리보기", "Input preview"), command=app.safe(generate)).pack(side="left", padx=2)
    ttk.Button(actions, text=app.words("Gaussian 입력 저장", "Save Gaussian input"), command=app.safe(save_input)).pack(side="left", padx=2)
    if not embedded:
        ttk.Button(actions, text=app.words("닫기", "Close"), command=win.destroy).pack(side="right")
    win.gaussian_ui = {"variables": variables, "gather": gather, "generate": generate, "notebook": notebook, "preview": preview, "additional": additional, "override": override}
    if embedded:
        app.gaussian_ui = win.gaussian_ui
    else:
        app.apply_appearance(win)
        install_tooltips(win, english=not app.cjk)
        win.grab_set()
    return win
