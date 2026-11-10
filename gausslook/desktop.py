"""Native X11 frontend. CPU canvas avoids forwarding a remote OpenGL context."""

from __future__ import annotations
import json, math, traceback
from pathlib import Path
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
from .model import ELEMENTS, COLORS, bonds, xyz_text
from .analysis import measure


class MoleculeCanvas(tk.Canvas):
    def __init__(self, parent, callback):
        super().__init__(parent, bg="#101b2b", highlightthickness=0)
        self.callback = callback
        self.atoms = []
        self.coords = np.zeros((0, 3))
        self.selected = []
        self.angle = [-0.2, 0.2]
        self.zoom = 1.0
        self.screen = []
        self.mesh = None
        self.labels = False
        self.style = "ball"
        self.show_h = True
        self.dragged = False
        self.bind("<Configure>", lambda e: self.render())
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<B1-Motion>", self.move)
        self.bind("<ButtonRelease-1>", self.release)
        self.bind("<MouseWheel>", lambda e: self.wheel(1.12 if e.delta > 0 else 1 / 1.12))
        self.bind("<Button-4>", lambda e: self.wheel(1.12))
        self.bind("<Button-5>", lambda e: self.wheel(1 / 1.12))

    def press(self, e):
        self.last = (e.x, e.y)
        self.dragged = False

    def move(self, e):
        dx, dy = e.x - self.last[0], e.y - self.last[1]
        if abs(dx) + abs(dy) > 2:
            self.dragged = True
        self.angle[0] += dx * 0.012
        self.angle[1] += dy * 0.012
        self.last = (e.x, e.y)
        self.render()

    def release(self, e):
        if self.dragged:
            return
        candidates = [
            (float(np.linalg.norm(np.array([e.x, e.y]) - s[:2])), i)
            for i, s in enumerate(self.screen)
            if self.show_h or self.atoms[i] != 1
        ]
        if candidates:
            d, i = min(candidates)
            if d < 22:
                if i in self.selected:
                    self.selected.remove(i)
                else:
                    self.selected.append(i)
                self.render()
                self.callback(self.selected)

    def wheel(self, factor):
        self.zoom = max(0.08, min(15, self.zoom * factor))
        self.render()

    def set_structure(self, atoms, coords, reset=False):
        self.atoms = atoms
        self.coords = np.asarray(coords, float)
        if reset:
            self.zoom = 1.0
            self.selected = []
            self.mesh = None
        self.render()

    def render(self):
        self.delete("all")
        if not len(self.coords):
            self.create_text(
                max(100, self.winfo_width() / 2),
                max(80, self.winfo_height() / 2),
                text="GaussLook  /  파일 열기 또는 데모",
                fill="#94a9c0",
                font=("Arial", 13),
            )
            return
        x, y = self.angle
        ry = np.array([[np.cos(x), 0, np.sin(x)], [0, 1, 0], [-np.sin(x), 0, np.cos(x)]])
        rx = np.array([[1, 0, 0], [0, np.cos(y), -np.sin(y)], [0, np.sin(y), np.cos(y)]])
        rot = ry @ rx
        center = self.coords.mean(0)
        span = max(2.5, float(np.linalg.norm(np.ptp(self.coords, axis=0))))
        scale = min(self.winfo_width(), self.winfo_height()) * 0.7 / span * self.zoom

        def project(v):
            p = (v - center) @ rot
            return np.column_stack(
                [
                    p[:, 0] * scale + self.winfo_width() / 2,
                    -p[:, 1] * scale + self.winfo_height() / 2,
                    p[:, 2],
                ]
            )

        p = project(self.coords)
        self.screen = p
        if self.mesh:
            verts = project(np.asarray(self.mesh["vertices"]))
            faces = self.mesh["faces"]
            step = max(1, len(faces) // 2200)
            draw = []
            for f in faces[::step]:
                points = verts[f]
                draw.append((float(points[:, 2].mean()), points))
            for depth, points in sorted(draw, key=lambda v: v[0]):
                self.create_polygon(
                    points[:, :2].reshape(-1).tolist(),
                    fill="#366e92" if self.mesh["level"] > 0 else "#9c526b",
                    outline="",
                    stipple="gray50",
                )
        if self.style != "sphere":
            for i, j in bonds(self.atoms, self.coords):
                if not self.show_h and (self.atoms[i] == 1 or self.atoms[j] == 1):
                    continue
                self.create_line(
                    *p[i, :2],
                    *p[j, :2],
                    fill="#71859d",
                    width=1 if self.style == "line" else max(2, min(9, scale * 0.09)),
                )
        for i in np.argsort(p[:, 2]):
            z = self.atoms[i]
            if z == 1 and not self.show_h:
                continue
            r = 2 if self.style == "line" else max(4, min(23, (0.25 if z == 1 else 0.39) * scale))
            if self.style == "sphere":
                r *= 2.2
            color = "#57d1c9" if i in self.selected else COLORS.get(z, "#b1a3c7")
            self.create_oval(
                p[i, 0] - r,
                p[i, 1] - r,
                p[i, 0] + r,
                p[i, 1] + r,
                fill=color,
                outline="#c8f6f2" if i in self.selected else "#152238",
                width=2,
            )
            if self.labels:
                self.create_text(
                    p[i, 0] + r + 7,
                    p[i, 1] - r,
                    text=f"{i+1} {ELEMENTS[z]}",
                    fill="#e6edf5",
                    font=("Arial", 10),
                )


class PlotCanvas(tk.Canvas):
    def __init__(self, parent, callback):
        super().__init__(parent, bg="#101b2b", height=175, highlightthickness=0)
        self.data = None
        self.callback = callback
        self.bind("<Configure>", lambda e: self.render())
        self.bind("<Button-1>", self.click)

    def set_data(self, d):
        self.data = d
        self.render()

    def render(self):
        self.delete("all")
        d = self.data
        if not d or not d.get("x"):
            self.create_text(100, 40, text="스펙트럼 / 경로", fill="#94a9c0")
            return
        x = np.array(d["x"])
        y = np.array(d["y"])
        w = self.winfo_width()
        h = self.winfo_height()
        self.bounds = (float(x.min()), float(x.max()), float(y.min()), float(y.max()))
        a, b, c, e = self.bounds
        px = 45 + (x - a) / (b - a or 1) * (w - 60)
        py = h - 30 - (y - c) / (e - c or 1) * (h - 50)
        self.create_rectangle(45, 15, w - 15, h - 30, outline="#344b66")
        if len(x) > 1:
            self.create_line(
                np.column_stack([px, py]).reshape(-1).tolist(), fill="#57d1c9", width=1.5
            )
        else:
            self.create_oval(px[0] - 3, py[0] - 3, px[0] + 3, py[0] + 3, fill="#57d1c9")
        self.create_text(
            45, h - 12, text=f'{a:.3f} {d.get("x_unit","")}', anchor="w", fill="#94a9c0"
        )
        self.create_text(w - 15, h - 12, text=f"{b:.3f}", anchor="e", fill="#94a9c0")
        self.create_text(3, 15, text=f"{e:.5g}", anchor="w", fill="#94a9c0")

    def click(self, event):
        if not self.data or not self.data.get("sticks"):
            return
        a, b, _, _ = self.bounds
        x = a + (event.x - 45) / (self.winfo_width() - 60) * (b - a)
        s = min(self.data["sticks"], key=lambda s: abs(s["x"] - x))
        self.callback(self.data["kind"], s["index"])


class App:
    def __init__(self, engine, quit_after=None):
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("GaussLook 1.0 · Gaussian 16 Analysis Studio")
        self.root.geometry("1440x900")
        self.root.minsize(1050, 700)
        self.calc = None
        self.frame = 0
        self.animation = None
        self.tick = 0
        self.mode_index = None
        self.rows = []
        families = set(font.families(self.root))
        chosen = next(
            (
                f
                for f in ["Malgun Gothic", "Noto Sans CJK KR", "NanumGothic", "Gulim", "Arial"]
                if f in families
            ),
            "Arial",
        )
        self.cjk = any(
            any(k in f.lower() for k in ["gothic", "cjk", "gulim", "nanum", "malgun"])
            for f in families
        )
        self.cjk = self.cjk and any(
            f in families for f in ["Malgun Gothic", "Noto Sans CJK KR", "NanumGothic", "Gulim"]
        )
        font.nametofont("TkDefaultFont").configure(family=chosen, size=10)
        font.nametofont("TkTextFont").configure(family=chosen, size=10)
        theme = ttk.Style()
        theme.theme_use("clam")
        theme.configure("Treeview", rowheight=25)
        theme.configure("TButton", padding=6)
        bar = ttk.Frame(self.root, padding=8)
        bar.pack(fill="x")
        for label, fn in [
            ("파일 열기", self.open_files),
            ("데모", lambda: self.accept(engine.demo())),
            ("원본 새로고침", self.reload),
            ("프로젝트 저장", self.save_project),
            ("XYZ", self.export_xyz),
            ("보고서 JSON", self.export_report),
            ("표시 설정", self.settings),
        ]:
            ttk.Button(bar, text=label, command=self.safe(fn)).pack(side="left", padx=3)
        ttk.Label(bar, text="GaussLook 1.0", font=(chosen, 17, "bold")).pack(side="right", padx=12)
        panes = ttk.Panedwindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=4)
        left = ttk.Frame(panes, width=225)
        panes.add(left, weight=0)
        ttk.Label(left, text="PROJECT EXPLORER").pack(anchor="w", pady=8)
        self.list = tk.Listbox(left, width=29, exportselection=False)
        self.list.pack(fill="both", expand=True)
        self.list.bind("<<ListboxSelect>>", self.pick)
        mid = ttk.Frame(panes)
        panes.add(mid, weight=3)
        self.status = ttk.Label(
            mid,
            text="파일을 열거나 데모를 선택하세요.",
            wraplength=620,
            padding=8,
            background="#d7f1ed",
        )
        self.status.pack(fill="x")
        controls = ttk.Frame(mid)
        controls.pack(fill="x", pady=5)
        self.style = ttk.Combobox(
            controls, values=["ball", "stick", "line", "sphere"], width=9, state="readonly"
        )
        self.style.set("ball")
        self.style.pack(side="left")
        self.style.bind("<<ComboboxSelected>>", lambda e: self.apply_style())
        self.label_var = tk.BooleanVar()
        self.h_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls, text="번호", variable=self.label_var, command=self.apply_style
        ).pack(side="left")
        ttk.Checkbutton(controls, text="H", variable=self.h_var, command=self.apply_style).pack(
            side="left"
        )
        ttk.Button(controls, text="중심", command=lambda: self.center()).pack(side="left")
        ttk.Button(controls, text="선택 해제", command=self.clear_selection).pack(side="left")
        self.selection = ttk.Label(controls, text="")
        self.selection.pack(side="left", padx=8)
        self.viewer = MoleculeCanvas(mid, self.selected)
        self.viewer.pack(fill="both", expand=True)
        timebar = ttk.Frame(mid)
        timebar.pack(fill="x")
        ttk.Button(timebar, text="▶ 경로", command=self.play_path).pack(side="left")
        self.scale = tk.Scale(
            timebar, from_=0, to=0, orient="horizontal", showvalue=False, command=self.slider
        )
        self.scale.pack(side="left", fill="x", expand=True)
        self.frame_label = ttk.Label(timebar, text="")
        self.frame_label.pack(side="left")
        ttk.Button(timebar, text="정지", command=self.stop).pack(side="left")
        self.plot = PlotCanvas(mid, self.plot_pick)
        self.plot.pack(fill="x", pady=6)
        ttk.Button(mid, text="현재 plot CSV 저장", command=self.safe(self.export_plot)).pack(
            anchor="e"
        )
        right = ttk.Frame(panes, width=470)
        panes.add(right, weight=2)
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)
        self.panels = {}
        for title in ["개요", "수렴·TS", "진동", "MO·표면", "물성", "구조·입력", "도구"]:
            f = ttk.Frame(self.notebook, padding=8)
            self.notebook.add(f, text=title)
            self.panels[title] = f
        ttk.Button(bar, text="Cancel task", command=self.cancel_task).pack(side="left", padx=3)
        self.current_task = None
        self.build_panels()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()
        if not self.cjk:
            self.english_labels()
            self.status.configure(
                text="English fallback: CJK font is unavailable in this Tk/X11 build. Web mode supports Korean."
            )
        if self.engine.calcs:
            self.load(next(iter(self.engine.calcs)))
        if quit_after:
            self.root.after(int(quit_after), self.close)

    def safe(self, fn):
        def run(*args):
            try:
                return fn(*args)
            except Exception as e:
                self.status.configure(text=str(e))
                messagebox.showerror("GaussLook", str(e), parent=self.root)

        return run

    def build_panels(self):
        self.texts = {}
        for name in ["개요", "수렴·TS", "물성"]:
            frame = self.panels[name]
            text = tk.Text(frame, wrap="word", font=("Arial", 10), width=48)
            scroll = ttk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            text.pack(fill="both", expand=True)
            self.texts[name] = text
        f = self.panels["진동"]
        row = ttk.Frame(f)
        row.pack(fill="x")
        self.spec = ttk.Combobox(
            row, values=["IR", "Raman", "VCD", "UV-Vis", "ECD", "NMR"], width=8, state="readonly"
        )
        self.spec.set("IR")
        self.spec.pack(side="left")
        ttk.Label(row, text="FWHM").pack(side="left")
        self.width = ttk.Entry(row, width=7)
        self.width.insert(0, "12")
        self.width.pack(side="left")
        ttk.Button(row, text="Plot", command=self.safe(self.make_spectrum)).pack(side="left")
        self.spec.bind("<<ComboboxSelected>>", lambda e: self.set_width())
        r = ttk.Frame(f)
        r.pack(fill="x", pady=6)
        ttk.Label(r, text="배율").pack(side="left")
        self.freqscale = ttk.Entry(r, width=6)
        self.freqscale.insert(0, "1")
        self.freqscale.pack(side="left")
        ttk.Label(r, text="진폭").pack(side="left")
        self.amp = ttk.Entry(r, width=6)
        self.amp.insert(0, ".5")
        self.amp.pack(side="left")
        ttk.Button(r, text="정지", command=self.stop).pack(side="left")
        ttk.Button(r, text="± XYZ", command=self.safe(self.export_displacement)).pack(side="left")
        self.mode_table = ttk.Treeview(
            f, columns=("frequency", "IR", "Raman"), show="headings", height=16
        )
        for key in ("frequency", "IR", "Raman"):
            self.mode_table.heading(key, text=key)
            self.mode_table.column(key, width=95, stretch=True)
        self.mode_table.pack(fill="both", expand=True)
        self.mode_table.bind("<<TreeviewSelect>>", self.mode_pick)
        f = self.panels["MO·표면"]
        self.mo_text = tk.Text(f, height=12, wrap="none", width=48)
        self.mo_text.pack(fill="both", expand=True)
        r = ttk.Frame(f)
        r.pack(fill="x", pady=5)
        self.spin = ttk.Combobox(r, values=["alpha", "beta"], width=7, state="readonly")
        self.spin.set("alpha")
        self.spin.pack(side="left")
        self.mo = ttk.Entry(r, width=5)
        self.mo.insert(0, "1")
        self.mo.pack(side="left")
        self.field_kind = ttk.Combobox(
            r, values=["mo", "density", "potential", "spin"], width=9, state="readonly"
        )
        self.field_kind.set("mo")
        self.field_kind.pack(side="left")
        ttk.Button(r, text="cubegen", command=self.safe(self.generate)).pack(side="left")
        self.field_combo = ttk.Combobox(f, state="readonly")
        self.field_combo.pack(fill="x")
        r = ttk.Frame(f)
        r.pack(fill="x")
        self.level = ttk.Entry(r, width=9)
        self.level.insert(0, ".03")
        self.level.pack(side="left")
        ttk.Button(r, text="+ 표면", command=self.safe(lambda: self.surface(1))).pack(side="left")
        ttk.Button(r, text="− 표면", command=self.safe(lambda: self.surface(-1))).pack(side="left")
        ttk.Button(r, text="숨기기", command=lambda: self.hide_surface()).pack(side="left")
        ttk.Label(
            f,
            text="X11 표면은 CPU preview입니다. 복잡한 표면은 웹 모드를 권장합니다.",
            wraplength=420,
        ).pack(fill="x", pady=8)
        f = self.panels["구조·입력"]
        self.smiles = ttk.Entry(f)
        self.smiles.insert(0, "c1ccccc1")
        self.smiles.pack(fill="x")
        ttk.Button(
            f,
            text="SMILES → conformer (RDKit)",
            command=self.safe(
                lambda: self.accept(self.engine.action("smiles", smiles=self.smiles.get()))
            ),
        ).pack(fill="x", pady=4)
        ttk.Label(f, text="Gaussian route").pack(anchor="w")
        self.route = ttk.Entry(f)
        self.route.insert(0, "#p B3LYP/def2SVP Opt Freq")
        self.route.pack(fill="x")
        r = ttk.Frame(f)
        r.pack(fill="x", pady=5)
        self.charge = ttk.Entry(r, width=5)
        self.charge.insert(0, "0")
        self.charge.pack(side="left")
        self.mult = ttk.Entry(r, width=5)
        self.mult.insert(0, "1")
        self.mult.pack(side="left")
        ttk.Label(r, text="Charge / Multiplicity").pack(side="left")
        self.additional = tk.Text(f, height=8, width=48)
        self.additional.pack(fill="both", expand=True)
        ttk.Button(f, text="Gaussian 입력 저장", command=self.safe(self.export_input)).pack(
            fill="x", pady=4
        )
        ttk.Button(f, text="선택 원자 삭제 → 새 구조", command=self.safe(self.delete_atoms)).pack(
            fill="x"
        )
        f = self.panels["도구"]
        ttk.Label(f, text="공통 엔진 JSON 분석", font=("Arial", 12, "bold")).pack(anchor="w")
        self.request = tk.Text(f, height=10, width=48)
        self.request.insert("1.0", '{\n  "action": "compare"\n}')
        self.request.pack(fill="x")
        ttk.Button(f, text="실행", command=self.safe(self.advanced)).pack(fill="x", pady=5)
        self.output = tk.Text(f, height=15, width=48, wrap="word")
        self.output.pack(fill="both", expand=True)
        ttk.Button(f, text="원본 출력", command=self.safe(self.source)).pack(fill="x")
        ttk.Button(f, text="지원 범위", command=self.safe(self.catalog)).pack(fill="x")

    def refresh(self):
        self.rows = self.engine.listing()
        self.list.delete(0, "end")
        for r in self.rows:
            self.list.insert("end", r["name"])
        self.field_ids = list(self.engine.fields)
        self.field_combo["values"] = [self.engine.fields[k].name for k in self.field_ids]
        if self.field_ids:
            self.field_combo.current(len(self.field_ids) - 1)

    def pick(self, e):
        if self.list.curselection():
            self.load(self.rows[self.list.curselection()[0]]["id"])

    def load(self, cid):
        self.stop()
        self.calc = self.engine.get(cid)
        self.frame = max(0, len(self.calc.frames) - 1)
        self.mode_index = None
        self.scale.configure(to=max(0, len(self.calc.frames) - 1))
        self.scale.set(self.frame)
        self.draw(True)
        data = self.engine.detail(cid)
        overview = {
            k: v
            for k, v in data.items()
            if k not in ["frames", "modes", "orbitals", "properties", "capabilities", "quality"]
        }
        quality_data = {"quality": data["quality"], "convergence": data["convergence"][-4:]}
        if not self.cjk:
            overview["warnings"] = (
                ["Source-specific caveats apply. See original output or Korean web UI."]
                if overview["warnings"]
                else []
            )
            quality_data = {
                "termination": data["status"],
                "imaginary_count": data["quality"]["imaginary_count"],
                "imaginary_frequencies": data["quality"]["imaginary_frequencies"],
                "convergence": data["convergence"][-4:],
                "note": "Normal termination does not prove geometry convergence. A TS candidate needs mode and IRC validation.",
            }
        for name, value in [
            ("개요", overview),
            ("수렴·TS", quality_data),
            ("물성", data["properties"]),
        ]:
            self.set_text(self.texts[name], json.dumps(value, ensure_ascii=not self.cjk, indent=2))
        self.mode_table.delete(*self.mode_table.get_children())
        for i, m in enumerate(self.calc.modes):
            self.mode_table.insert(
                "",
                "end",
                iid=str(i),
                values=(m["frequency_cm1"], m.get("ir_km_mol", "—"), m.get("raman_activity", "—")),
            )
        rows = []
        for spin, o in self.calc.orbitals.items():
            rows.append(spin + "    MO      eV       occupation")
            rows.extend(
                f'{i+1:5d} {v:12.5f} {o["occupations"][i]:6.2f}'
                for i, v in enumerate(o["energies_eV"])
            )
        self.set_text(self.mo_text, "\n".join(rows))
        self.charge.delete(0, "end")
        self.charge.insert(0, str(self.calc.charge or 0))
        self.mult.delete(0, "end")
        self.mult.insert(0, str(self.calc.multiplicity or 1))
        self.status.configure(text=self.calc.name + " · " + self.calc.status["termination"])
        self.path_plot()

    def set_text(self, t, value):
        t.delete("1.0", "end")
        t.insert("1.0", value)

    def draw(self, reset=False, coords=None):
        if self.calc and self.calc.frames:
            self.viewer.set_structure(
                self.calc.atoms,
                coords if coords is not None else self.calc.frames[self.frame]["coords"],
                reset,
            )
            self.frame_label.configure(text=f"{self.frame+1} / {len(self.calc.frames)}")

    def selected(self, ids):
        text = ", ".join(str(i + 1) for i in ids)
        if self.calc and 2 <= len(ids) <= 4:
            try:
                d = measure(self.calc.frames[self.frame]["coords"], ids)
                text += f' · {d["value"]:.4f} {d["unit"]}'
            except ValueError as e:
                text += " · " + str(e)
        self.selection.configure(text=text)

    def clear_selection(self):
        self.viewer.selected = []
        self.viewer.render()
        self.selection.configure(text="")

    def apply_style(self):
        self.viewer.style = self.style.get()
        self.viewer.labels = self.label_var.get()
        self.viewer.show_h = self.h_var.get()
        self.viewer.render()

    def center(self):
        self.viewer.zoom = 1.0
        self.viewer.render()

    def slider(self, value):
        if self.calc:
            self.frame = min(len(self.calc.frames) - 1, int(float(value)))
            self.draw()

    def stop(self):
        if self.animation:
            self.root.after_cancel(self.animation)
            self.animation = None

    def play_path(self):
        self.stop()
        if not self.calc or not self.calc.frames:
            return

        def step():
            self.frame = (self.frame + 1) % len(self.calc.frames)
            self.scale.set(self.frame)
            self.draw()
            self.animation = self.root.after(160, step)

        step()

    def mode_pick(self, event):
        ids = self.mode_table.selection()
        if ids:
            self.safe(lambda: self.play_mode(int(ids[0])))()

    def play_mode(self, index):
        self.stop()
        self.mode_index = index
        m = self.calc.modes[index]
        if len(m.get("displacements", [])) != len(self.calc.atoms):
            raise ValueError("변위 데이터가 없습니다.")
        self.tick = 0

        def step():
            a = float(self.amp.get()) * math.sin(self.tick * 0.2)
            self.tick += 1
            coords = np.array(self.calc.frames[self.frame]["coords"]) + a * np.array(
                m["displacements"]
            )
            self.draw(coords=coords)
            self.animation = self.root.after(70, step)

        step()
        self.status.configure(text=f'{m["frequency_cm1"]} cm-1 · visual normal-mode displacement')

    def plot_pick(self, kind, index):
        if kind == "Energy path":
            self.stop()
            self.frame = index
            self.scale.set(index)
            self.draw()
        elif kind in ("IR", "RAMAN", "VCD"):
            self.safe(lambda: self.play_mode(index))()

    def set_width(self):
        self.width.delete(0, "end")
        self.width.insert(
            0,
            (
                ".25"
                if self.spec.get() in ("UV-Vis", "ECD")
                else ".05" if self.spec.get() == "NMR" else "12"
            ),
        )

    def make_spectrum(self):
        if not self.calc:
            return
        p = {
            "kind": self.spec.get(),
            "width": float(self.width.get()),
            "scale": float(self.freqscale.get()),
        }
        if p["kind"] == "Raman":
            laser = simpledialog.askfloat(
                "Raman", "레이저 파장 nm", initialvalue=532, parent=self.root
            )
            if laser is None:
                return
            p["laser_nm"] = laser
        if p["kind"] == "NMR":
            ref = simpledialog.askfloat(
                "NMR", "Reference shielding ppm", initialvalue=0, parent=self.root
            )
            if ref is None:
                return
            p["reference"] = ref
        self.plot.set_data(self.engine.action("spectrum", self.calc.id, **p))

    def path_plot(self):
        rows = [
            {"x": i + 1, "y": f["energy_hartree"], "index": i}
            for i, f in enumerate(self.calc.frames)
            if f.get("energy_hartree") is not None
        ]
        self.plot.set_data(
            {
                "kind": "Energy path",
                "x": [r["x"] for r in rows],
                "y": [r["y"] for r in rows],
                "sticks": rows,
                "x_unit": "frame",
                "y_unit": "Hartree",
            }
        )

    def accept(self, result):
        if result.get("task"):
            self.watch(result["task"])
            return
        self.refresh()
        if result.get("ids"):
            self.load(result["ids"][0])

    def watch(self, tid):
        self.current_task = tid

        def poll():
            t = self.engine.task(tid)
            self.status.configure(text=f'{t["title"]} · {t["status"]} · {t["progress"]}%')
            if t["status"] == "done":
                self.accept(t.get("result", {}))
                return
            if t["status"] in ("error", "cancelled"):
                self.safe(lambda: (_ for _ in ()).throw(ValueError(t.get("error", "취소"))))()
                return
            self.animation_task = self.root.after(250, poll)

        poll()

    def cancel_task(self):
        if self.current_task and self.current_task in self.engine.tasks:
            self.engine.cancel(self.current_task)
            self.status.configure(text="Task cancellation requested.")

    def open_files(self):
        paths = filedialog.askopenfilenames(
            parent=self.root,
            title="Gaussian 결과 / 구조 / cube",
            filetypes=[
                (
                    "Gaussian and structures",
                    "*.log *.out *.chk *.fchk *.fch *.cube *.cub *.gjf *.com *.xyz *.sdf *.mol *.pdb *.glproj",
                ),
                ("All", "*"),
            ],
        )
        if paths:

            def run(t):
                ids = []
                for p in paths:
                    r = self.engine.load(p)
                    if r.get("task"):
                        self.root.after(0, lambda tid=r["task"]: self.watch(tid))
                    ids.extend(r.get("ids", []))
                return {"ids": ids}

            self.watch(self.engine.submit("파일 읽기", run))

    def reload(self):
        if self.calc and self.calc.source:
            self.watch(self.engine.submit("새로고침", lambda t: self.engine.load(self.calc.source)))

    def save(self, title, ext, text):
        p = filedialog.asksaveasfilename(parent=self.root, title=title, defaultextension=ext)
        if p:
            Path(p).write_text(text, encoding="utf-8")

    def save_project(self):
        self.save(
            "프로젝트 저장",
            ".glproj",
            json.dumps(self.engine.project(), ensure_ascii=False, indent=2),
        )

    def export_xyz(self):
        if self.calc:
            self.save("XYZ", ".xyz", xyz_text(self.calc, self.frame))

    def export_report(self):
        if self.calc:
            self.save(
                "분석 snapshot",
                ".json",
                json.dumps(self.engine.detail(self.calc.id), ensure_ascii=False, indent=2),
            )

    def export_plot(self):
        import csv, io

        d = self.plot.data
        if not d:
            return
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow([d.get("x_unit", "x"), d.get("y_unit", "y")])
        w.writerows(zip(d["x"], d["y"]))
        self.save("Plot data", ".csv", out.getvalue())

    def export_displacement(self):
        if self.mode_index is None:
            raise ValueError("모드를 먼저 선택하세요.")
        a = simpledialog.askfloat(
            "모드 변위", "진폭: 음수/양수 모두 가능", initialvalue=0.5, parent=self.root
        )
        if a is None:
            return
        coords = np.array(self.calc.frames[self.frame]["coords"]) + a * np.array(
            self.calc.modes[self.mode_index]["displacements"]
        )
        self.save("모드 변위 XYZ", ".xyz", xyz_text(self.calc, coords=coords))

    def generate(self):
        if self.calc:
            self.accept(
                self.engine.action(
                    "generate_cube",
                    self.calc.id,
                    kind=self.field_kind.get(),
                    orbital=int(self.mo.get()),
                    spin=self.spin.get(),
                    grid="coarse",
                )
            )

    def surface(self, sign):
        index = self.field_combo.current()
        if index < 0:
            raise ValueError("cube를 먼저 여세요.")
        fid = self.field_ids[index]
        level = sign * abs(float(self.level.get()))

        def run(t):
            return {"mesh": self.engine.action("mesh", field_id=fid, level=level, max_faces=12000)}

        tid = self.engine.submit("표면 생성", run)

        def poll():
            t = self.engine.task(tid)
            if t["status"] == "done":
                self.viewer.mesh = t["result"]["mesh"]
                self.viewer.render()
                self.status.configure(text="CPU surface preview · 최대 약 2200 faces 표시")
                return
            if t["status"] == "error":
                self.status.configure(text=t["error"])
                return
            self.root.after(200, poll)

        poll()

    def hide_surface(self):
        self.viewer.mesh = None
        self.viewer.render()

    def export_input(self):
        if self.calc:
            d = self.engine.action(
                "input",
                self.calc.id,
                route=self.route.get(),
                charge=int(self.charge.get()),
                multiplicity=int(self.mult.get()),
                additional=self.additional.get("1.0", "end"),
                frame=self.frame,
            )
            self.save("Gaussian input", ".gjf", d["text"])

    def delete_atoms(self):
        if not self.calc or not self.viewer.selected:
            raise ValueError("원자를 먼저 선택하세요.")
        self.accept(
            self.engine.action(
                "edit",
                self.calc.id,
                operation="delete",
                indices=self.viewer.selected,
                frame=self.frame,
            )
        )

    def advanced(self):
        args = json.loads(self.request.get("1.0", "end"))
        name = args.pop("action")
        cid = args.pop("id", self.calc.id if self.calc else None)
        d = self.engine.action(name, cid, **args)
        if d and isinstance(d, dict) and (d.get("ids") or d.get("task")):
            self.accept(d)
        self.set_text(self.output, json.dumps(d, ensure_ascii=not self.cjk, indent=2))

    def source(self):
        if self.calc:
            self.set_text(self.output, self.engine.action("source", self.calc.id)["text"])

    def catalog(self):
        self.set_text(
            self.output,
            (Path(__file__).resolve().parent.parent / "docs/FEATURE_STATUS.md").read_text(),
        )
        self.notebook.select(self.panels["도구"])

    def settings(self):
        win = tk.Toplevel(self.root)
        win.title("표시 설정")
        ttk.Label(win, text="폰트").pack()
        families = sorted(font.families(self.root))
        f = ttk.Combobox(win, values=families, width=35)
        f.set(font.nametofont("TkDefaultFont").actual("family"))
        f.pack()
        ttk.Label(win, text="글자 크기").pack()
        size = ttk.Spinbox(win, from_=8, to=24, width=7)
        size.set(10)
        size.pack()

        def apply():
            for name in ["TkDefaultFont", "TkTextFont"]:
                font.nametofont(name).configure(family=f.get(), size=int(size.get()))
            win.destroy()

        ttk.Button(win, text="적용", command=self.safe(apply)).pack(pady=10)
        if not self.cjk:
            self.english_labels(win)

    def english_labels(self, parent=None):
        mapping = {
            "파일 열기": "Open files",
            "데모": "Demo",
            "원본 새로고침": "Reload source",
            "프로젝트 저장": "Save project",
            "보고서 JSON": "Report JSON",
            "표시 설정": "Display settings",
            "번호": "Labels",
            "중심": "Center",
            "선택 해제": "Clear selection",
            "▶ 경로": "Play path",
            "정지": "Stop",
            "현재 plot CSV 저장": "Save plot CSV",
            "배율": "Scale",
            "진폭": "Amplitude",
            "± XYZ": "Mode XYZ",
            "+ 표면": "+ Surface",
            "− 표면": "- Surface",
            "숨기기": "Hide",
            "실행": "Run",
            "원본 출력": "Source output",
            "지원 범위": "Feature status",
            "Gaussian 입력 저장": "Save Gaussian input",
            "선택 원자 삭제 → 새 구조": "Delete selected / new model",
            "SMILES → conformer (RDKit)": "SMILES to conformers (RDKit)",
            "공통 엔진 JSON 분석": "Shared analysis engine / JSON",
            "폰트": "Font",
            "글자 크기": "Font size",
            "적용": "Apply",
            "X11 표면은 CPU preview입니다. 복잡한 표면은 웹 모드를 권장합니다.": "CPU surface preview. Use web mode for complex surfaces.",
        }
        for widget in (parent or self.root).winfo_children():
            try:
                value = widget.cget("text")
                if value in mapping:
                    widget.configure(text=mapping[value])
            except tk.TclError:
                pass
            self.english_labels(widget)
        if parent is None:
            for name, label in zip(
                self.panels,
                [
                    "Summary",
                    "Quality / TS",
                    "Vibrations",
                    "MO / Fields",
                    "Properties",
                    "Build / Input",
                    "Tools",
                ],
            ):
                self.notebook.tab(self.panels[name], text=label)

    def close(self):
        self.stop()
        self.engine.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
