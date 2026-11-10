"""Focused native analysis panels; all numerical work is shared with the web API."""

from __future__ import annotations
import csv
import io
import tkinter as tk
from tkinter import ttk
import numpy as np
from .analysis import orbital_analysis, frame_analysis, polarizability_analysis
from .model import ELEMENTS, HARTREE_EV, BOHR_ANG
from .help_ui import Manual


class CorePanels:
    def words(self, ko, en):
        return ko if self.cjk else en

    def select_panel(self, name):
        self.notebook.select(self.panels[name])
        self.panel_select.set(self.panel_names.get(name, name))

    def show_help(self, event=None):
        self.select_panel("도움말")
        return "break"

    def build_core_panels(self):
        self.manual = Manual(self.panels["도움말"], english=not self.cjk)
        self.manual.pack(fill="both", expand=True)
        f = self.panels["에너지·Force"]
        self.force_summary = ttk.Label(f, wraplength=440, justify="left")
        self.force_summary.pack(fill="x", pady=6)
        r = ttk.Frame(f)
        r.pack(fill="x")
        self.force_unit = ttk.Combobox(
            r, values=["Eh/Bohr", "eV/Angstrom"], state="readonly", width=14
        )
        self.force_unit.set("Eh/Bohr")
        self.force_unit.pack(side="left")
        self.force_unit.bind("<<ComboboxSelected>>", lambda e: self.update_frame_analysis())
        self.force_arrows = tk.BooleanVar()
        ttk.Checkbutton(
            r,
            text=self.words("Force 벡터", "Force vectors"),
            variable=self.force_arrows,
            command=self.update_force_arrows,
        ).pack(side="left")
        ttk.Button(
            r,
            text=self.words("에너지·Force CSV", "Energy / Force CSV"),
            command=self.safe(self.export_forces),
        ).pack(side="left")
        self.force_table = self.core_table(f, ("Atom", "Fx", "Fy", "Fz", "|F|"), 10)
        self.force_table.bind("<<TreeviewSelect>>", self.force_pick)
        ttk.Label(
            f,
            text=self.words(
                "Cartesian force = −gradient. 아래의 최적화 수렴 기준값과 구분합니다.",
                "Cartesian force = -gradient. Optimization criteria below may use internal coordinates.",
            ),
            wraplength=440,
        ).pack(fill="x", pady=6)
        self.force_criteria = ttk.Label(f, wraplength=440, justify="left")
        self.force_criteria.pack(fill="x")
        ttk.Button(
            f, text=self.words("에너지 경로 그리기", "Plot energy path"), command=self.path_plot
        ).pack(fill="x", pady=5)
        self.frame_table = self.core_table(f, ("Frame", "Energy / Eh", "Force"), 5)
        self.frame_table.bind("<<TreeviewSelect>>", self.frame_pick)
        f = self.panels["분극률"]
        self.polar_source = ttk.Combobox(f, state="readonly")
        self.polar_source.pack(fill="x")
        self.polar_source.bind("<<ComboboxSelected>>", lambda e: self.update_polar())
        self.polar_summary = ttk.Label(f, wraplength=440, justify="left")
        self.polar_summary.pack(fill="x", pady=10)
        self.polar_table = self.core_table(f, ("a.u.", "X", "Y", "Z"), 4)
        self.polar_note = ttk.Label(f, wraplength=440, justify="left")
        self.polar_note.pack(fill="x", pady=10)
        ttk.Button(
            f, text=self.words("분극률 CSV", "Polar CSV"), command=self.safe(self.export_polar)
        ).pack(fill="x")
        ttk.Label(
            f,
            text=self.words(
                "분자 분극률 α와 고분자의 1 GHz 복소 유전율은 다른 물성입니다.",
                "Molecular polarizability is not polymer complex permittivity at 1 GHz.",
            ),
            wraplength=440,
        ).pack(fill="x", pady=12)

    def core_table(self, parent, columns, height):
        area = ttk.Frame(parent)
        area.pack(fill="both", expand=True, pady=5)
        tree = ttk.Treeview(area, columns=columns, show="headings", height=height)
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=85, minwidth=48, stretch=True)
        scroll = ttk.Scrollbar(area, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def build_vibration_panel(self, f):
        self.mode_summary = ttk.Label(f, wraplength=440)
        self.mode_summary.pack(fill="x", pady=5)
        row = ttk.Frame(f)
        row.pack(fill="x")
        self.imaginary_only = tk.BooleanVar()
        ttk.Checkbutton(
            row,
            text=self.words("Imaginary만", "Imaginary only"),
            variable=self.imaginary_only,
            command=self.fill_modes,
        ).pack(side="left")
        ttk.Button(
            row, text=self.words("재생", "Play mode"), command=self.safe(self.play_selected_mode)
        ).pack(side="left")
        ttk.Button(row, text=self.words("정지", "Stop"), command=self.stop).pack(side="left")
        ttk.Button(row, text=self.words("평형 구조", "Equilibrium"), command=self.equilibrium).pack(
            side="left"
        )
        self.mode_table = self.core_table(f, ("Mode", "cm-1", "IR", "Raman"), 10)
        self.mode_table.tag_configure("imaginary", foreground="#b82442")
        self.mode_table.bind("<<TreeviewSelect>>", self.mode_pick)
        r = ttk.Frame(f)
        r.pack(fill="x")
        ttk.Label(r, text=self.words("진폭", "Amplitude")).pack(side="left")
        self.amp = ttk.Entry(r, width=6)
        self.amp.insert(0, ".5")
        self.amp.pack(side="left")
        ttk.Label(r, text=self.words("속도", "Speed")).pack(side="left")
        self.speed = ttk.Combobox(r, values=["0.5", "1", "2", "4"], width=5, state="readonly")
        self.speed.set("1")
        self.speed.pack(side="left")
        self.mode_arrows = tk.BooleanVar()
        ttk.Checkbutton(
            r,
            text=self.words("변위 벡터", "Displacement vectors"),
            variable=self.mode_arrows,
            command=self.update_mode_arrows,
        ).pack(side="left")
        ttk.Button(r, text="± XYZ", command=self.safe(self.export_displacement)).pack(side="left")
        ttk.Label(
            f,
            text=self.words(
                "진폭·속도는 시각화 설정입니다. 실제 열진동·시간축이 아닙니다.",
                "Amplitude and speed are visual settings, not thermal amplitudes or physical time.",
            ),
            wraplength=440,
        ).pack(fill="x", pady=6)
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
        ttk.Label(row, text=self.words("배율", "Scale")).pack(side="left")
        self.freqscale = ttk.Entry(row, width=6)
        self.freqscale.insert(0, "1")
        self.freqscale.pack(side="left")
        ttk.Button(row, text="Plot", command=self.safe(self.make_spectrum)).pack(side="left")
        self.spec.bind("<<ComboboxSelected>>", lambda e: self.set_width())

    def fill_modes(self):
        self.mode_table.delete(*self.mode_table.get_children())
        if not self.calc:
            return
        fs = [m["frequency_cm1"] for m in self.calc.modes]
        self.mode_summary.configure(
            text=self.words(
                (
                    f"{len(fs)}개 모드 · imaginary {sum(v<0 for v in fs)}개"
                    if fs
                    else "진동수 미계산 / 미출력"
                ),
                (
                    f"{len(fs)} modes / {sum(v<0 for v in fs)} imaginary"
                    if fs
                    else "Frequencies not calculated / not printed"
                ),
            )
        )
        for i, m in enumerate(self.calc.modes):
            if self.imaginary_only.get() and m["frequency_cm1"] >= 0:
                continue
            self.mode_table.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    i + 1,
                    m["frequency_cm1"],
                    m.get("ir_km_mol", "—"),
                    m.get("raman_activity", "—"),
                ),
                tags=("imaginary",) if m["frequency_cm1"] < 0 else (),
            )

    def play_selected_mode(self):
        ids = self.mode_table.selection()
        if not ids:
            raise ValueError(self.words("모드 행을 선택하세요.", "Select a mode row."))
        self.play_mode(int(ids[0]))

    def equilibrium(self):
        self.stop()
        if self.calc and self.mode_index is not None:
            self.frame = self.calc.modes[self.mode_index].get(
                "reference_frame", len(self.calc.frames) - 1
            )
            self.scale.set(self.frame)
        self.draw()

    def update_mode_arrows(self):
        self.viewer.vectors = None
        if self.calc and self.mode_index is not None and self.mode_arrows.get():
            self.viewer.vectors = self.calc.modes[self.mode_index].get("displacements")
        self.viewer.render()

    def build_mo_panel(self, f):
        self.mo_summary = ttk.Label(f, wraplength=440, justify="left")
        self.mo_summary.pack(fill="x", pady=4)
        r = ttk.Frame(f)
        r.pack(fill="x")
        self.spin = ttk.Combobox(r, values=["alpha"], width=7, state="readonly")
        self.spin.set("alpha")
        self.spin.pack(side="left")
        self.spin.bind("<<ComboboxSelected>>", lambda e: self.fill_mos())
        for label in ["HOMO", "LUMO"]:
            ttk.Button(r, text=label, command=lambda s=label: self.select_frontier(s)).pack(
                side="left"
            )
        self.mo = ttk.Entry(r, width=5)
        self.mo.insert(0, "1")
        self.mo.pack(side="left")
        self.mo_graph = tk.Canvas(f, height=130, bg="#101b2b", highlightthickness=0)
        self.mo_graph.pack(fill="x", pady=4)
        self.mo_graph.bind("<Configure>", lambda e: self.draw_mo_graph())
        self.mo_table = self.core_table(f, ("MO", "Label", "eV", "Occupation"), 7)
        self.mo_table.bind("<<TreeviewSelect>>", self.mo_pick)
        r = ttk.Frame(f)
        r.pack(fill="x")
        ttk.Label(r, text=self.words("등치값", "Isovalue")).pack(side="left")
        self.level = ttk.Entry(r, width=7)
        self.level.insert(0, ".03")
        self.level.pack(side="left")
        self.mo_grid = ttk.Combobox(
            r, values=["coarse", "medium", "fine"], width=8, state="readonly"
        )
        self.mo_grid.set("coarse")
        self.mo_grid.pack(side="left")
        ttk.Button(
            r,
            text=self.words("선택 MO ±표면", "Selected MO +/-"),
            command=self.safe(self.selected_mo_surface),
        ).pack(side="left")
        ttk.Button(r, text=self.words("숨기기", "Hide"), command=self.hide_surface).pack(
            side="left"
        )
        self.mo_ready = ttk.Label(f, wraplength=440)
        self.mo_ready.pack(fill="x", pady=6)
        r = ttk.Frame(f)
        r.pack(fill="x")
        self.checkpoint_combo = ttk.Combobox(r, state="readonly", width=26)
        self.checkpoint_combo.pack(side="left", fill="x", expand=True)
        ttk.Button(
            r,
            text=self.words("로그·chk 연결", "Link log + checkpoint"),
            command=self.safe(self.link_checkpoint),
        ).pack(side="left")
        ttk.Separator(f).pack(fill="x", pady=6)
        self.field_combo = ttk.Combobox(f, state="readonly")
        self.field_combo.pack(fill="x")
        r = ttk.Frame(f)
        r.pack(fill="x")
        ttk.Button(r, text="+ 표면", command=self.safe(lambda: self.surface(1))).pack(side="left")
        ttk.Button(r, text="− 표면", command=self.safe(lambda: self.surface(-1))).pack(side="left")
        self.field_kind = ttk.Combobox(
            r, values=["mo", "density", "potential", "spin"], width=9, state="readonly"
        )
        self.field_kind.set("density")
        self.field_kind.pack(side="left")
        ttk.Button(r, text="cubegen", command=self.safe(self.generate)).pack(side="left")

    def fill_mos(self):
        if not self.calc:
            return
        channels = orbital_analysis(self.calc)["channels"]
        sp = self.spin.get()
        self.spin["values"] = list(channels) or ["alpha"]
        if sp not in channels:
            self.spin.set(next(iter(channels), "alpha"))
        o = channels.get(self.spin.get(), {})
        self.mo_table.delete(*self.mo_table.get_children())
        for row in o.get("rows", []):
            self.mo_table.insert(
                "",
                "end",
                iid=str(row["mo"]),
                values=(row["mo"], row["label"], f"{row['energy_eV']:.6f}", row["occupation"]),
            )

        def frontier(name):
            r = o.get(name)
            return f"MO {r['mo']}: {r['energy_eV']:.6f} eV" if r else "—"

        gap = o.get("gap_eV")
        self.mo_summary.configure(
            text=(
                f"HOMO {frontier('homo')}\nLUMO {frontier('lumo')}\nGap: {gap:.6f} eV"
                if gap is not None
                else self.words(
                    "MO 에너지 미출력 또는 frontier 점유 정보 없음",
                    "MO energies / frontier occupations unavailable",
                )
            )
        )
        d = self.engine.detail(self.calc.id)
        self.mo_ready.configure(
            text=self.words(
                "±색은 오비탈의 위상입니다. Gap은 여기 에너지와 다릅니다. ",
                "+/- colors show orbital phase. Gap is not excitation energy. ",
            )
            + (
                self.words("표면 생성 준비됨.", "Surface generation ready.")
                if d["orbital_surface_ready"]
                else self.words(
                    "표면: chk/fchk + Gaussian cubegen 필요. log에는 주로 에너지만 있습니다.",
                    "Surface: open chk/fchk with MO coefficients and configure Gaussian cubegen.",
                )
            )
        )
        self.checkpoint_ids = [
            r["id"]
            for r in self.engine.listing()
            if r["kind"] == "checkpoint" and r["checkpoint_linked"]
        ]
        self.checkpoint_combo["values"] = [self.engine.get(cid).name for cid in self.checkpoint_ids]
        if self.checkpoint_ids:
            self.checkpoint_combo.current(0)
        if o.get("homo"):
            self.select_frontier("HOMO")
        self.draw_mo_graph()

    def select_frontier(self, name):
        if not self.calc:
            return
        row = orbital_analysis(self.calc)["channels"].get(self.spin.get(), {}).get(name.lower())
        if not row:
            return
        self.mo.delete(0, "end")
        self.mo.insert(0, str(row["mo"]))
        self.mo_table.selection_set(str(row["mo"]))
        self.mo_table.see(str(row["mo"]))
        self.draw_mo_graph()

    def mo_pick(self, event):
        ids = self.mo_table.selection()
        if ids:
            self.mo.delete(0, "end")
            self.mo.insert(0, ids[0])
            self.draw_mo_graph()

    def draw_mo_graph(self):
        self.mo_graph.delete("all")
        if not self.calc:
            return
        o = orbital_analysis(self.calc)["channels"].get(self.spin.get(), {})
        rows = o.get("rows", [])
        try:
            selected = int(self.mo.get())
        except ValueError:
            selected = 1
        h = (o.get("homo") or {}).get("mo", selected)
        indices = sorted(
            set(range(max(1, h - 2), min(len(rows), h + 3) + 1))
            | ({selected} if 1 <= selected <= len(rows) else set())
        )
        rows = [rows[i - 1] for i in indices]
        if not rows:
            return
        energies = [r["energy_eV"] for r in rows]
        lo = min(energies)
        span = max(1, max(energies) - lo)
        width = max(300, self.mo_graph.winfo_width())
        for k, row in enumerate(rows):
            y = 110 - (row["energy_eV"] - lo) / span * 90
            x = 55 + k * (width - 90) / max(1, len(rows))
            color = (
                "#57d1c9"
                if row["mo"] == selected
                else "#f29eb0" if not row["occupation"] else "#65bafa"
            )
            tag = "mo" + str(row["mo"])
            self.mo_graph.create_line(x, y, x + 35, y, fill=color, width=4, tags=tag)
            self.mo_graph.create_text(
                x + 17,
                y - 10,
                text=f"{row['mo']} {row['label']}",
                fill=color,
                font=("Arial", 8),
                tags=tag,
            )
            self.mo_graph.create_text(
                x + 17,
                y + 12,
                text=f"{row['energy_eV']:.2f}",
                fill="#c5d3e4",
                font=("Arial", 8),
                tags=tag,
            )
            self.mo_graph.tag_bind(
                tag, "<Button-1>", lambda e, n=row["mo"]: self.mo_table.selection_set(str(n))
            )

    def selected_mo_surface(self):
        if self.calc:
            self.accept(
                self.engine.action(
                    "orbital_surface",
                    self.calc.id,
                    spin=self.spin.get(),
                    orbital=int(self.mo.get()),
                    grid=self.mo_grid.get(),
                    level=float(self.level.get()),
                )
            )

    def link_checkpoint(self):
        i = self.checkpoint_combo.current()
        if self.calc and i >= 0:
            self.accept(
                self.engine.action(
                    "link_checkpoint", self.calc.id, checkpoint_id=self.checkpoint_ids[i]
                )
            )
        else:
            raise ValueError(
                self.words("log와 chk/fchk를 모두 여세요.", "Open both a log and its chk/fchk.")
            )

    def update_frame_analysis(self):
        if not self.calc or not self.calc.frames:
            return
        d = frame_analysis(self.calc, self.frame)
        e = d["energy"]
        force = d["force"]
        factor = HARTREE_EV / BOHR_ANG if self.force_unit.get() == "eV/Angstrom" else 1
        summary = f"Frame {self.frame+1}/{len(self.calc.frames)}\n"
        summary += (
            f"{e['kind']}\n{e['hartree']:.12f} Eh / {e['eV']:.8f} eV"
            if e
            else self.words("에너지 미출력", "Energy not printed")
        )
        self.force_table.delete(*self.force_table.get_children())
        if force:
            summary += f"\nMax component {force['max_component_hartree_bohr']*factor:.7g} / RMS {force['rms_component_hartree_bohr']*factor:.7g} {self.force_unit.get()}\n{force['source']} / line {force.get('line') or '—'}"
            for i, (v, n) in enumerate(
                zip(force["vectors_hartree_bohr"], force["norms_hartree_bohr"])
            ):
                self.force_table.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(
                        f"{i+1} {ELEMENTS[self.calc.atoms[i]]}",
                        *[f"{x*factor:.7g}" for x in v],
                        f"{n*factor:.7g}",
                    ),
                )
        else:
            summary += "\n" + self.words(
                "원자별 Force 미출력 (0을 뜻하지 않음)", "Atomic forces not printed (not zero)"
            )
        self.force_summary.configure(text=summary)
        criteria = [
            v
            for v in self.calc.convergence
            if (v.get("line") or 0) >= (self.calc.frames[self.frame].get("line") or 0)
            and (
                self.frame + 1 == len(self.calc.frames)
                or (v.get("line") or 0) < (self.calc.frames[self.frame + 1].get("line") or 0)
            )
        ]
        self.force_criteria.configure(
            text="\n".join(
                f"{v['item']}: {v['value']} / {v['threshold']} / {'YES' if v['passed'] else 'NO'}"
                for v in criteria[-4:]
            )
        )
        self.update_force_arrows()

    def update_force_arrows(self):
        self.viewer.vectors = None
        if self.calc and self.force_arrows.get():
            force = frame_analysis(self.calc, self.frame)["force"]
            if force:
                self.viewer.vectors = force["vectors_hartree_bohr"]
        self.viewer.render()

    def force_pick(self, event):
        ids = self.force_table.selection()
        if ids:
            self.viewer.selected = [int(ids[0])]
            self.viewer.render()
            self.selected([int(ids[0])])

    def frame_pick(self, event):
        ids = self.frame_table.selection()
        if ids:
            self.stop()
            self.frame = int(ids[0])
            self.scale.set(self.frame)
            self.draw()
            self.update_frame_analysis()

    def fill_frame_table(self):
        self.frame_table.delete(*self.frame_table.get_children())
        for i, f in enumerate(self.calc.frames):
            self.frame_table.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    i + 1,
                    f"{f['energy_hartree']:.10f}" if f.get("energy_hartree") is not None else "—",
                    "yes" if f.get("force_record") is not None else "—",
                ),
            )

    def fill_polar(self):
        data = polarizability_analysis(self.calc)
        self.polar_records = data["records"]
        self.polar_source["values"] = [
            f"{r['source']} / W={r.get('frequency_au','?')}" for r in self.polar_records
        ]
        if data["default_index"] is not None:
            self.polar_source.current(data["default_index"])
        else:
            self.polar_source.set("")
        self.update_polar()

    def update_polar(self):
        self.polar_table.delete(*self.polar_table.get_children())
        i = self.polar_source.current()
        if not 0 <= i < len(getattr(self, "polar_records", [])):
            self.polar_summary.configure(
                text=self.words(
                    "분극률 미계산 / 미출력. Gaussian Polar 결과 또는 해당 fchk가 필요합니다.",
                    "Polarizability not calculated / not printed. Open a Polar result or its checkpoint.",
                )
            )
            self.polar_note.configure(text="")
            return
        r = self.polar_records[i]
        self.polar_summary.configure(
            text=f"Isotropic mean: {r['mean_au']:.8f} a.u.\nPolarizability volume: {r['mean_A3']:.8f} A^3\nAnisotropy: {r['anisotropy_au']:.8f} a.u.\nEigenvalues: "
            + ", ".join(f"{v:.7f}" for v in r["eigenvalues_au"])
        )
        for j, row in enumerate(r["tensor_au"]):
            self.polar_table.insert("", "end", values=("XYZ"[j], *[f"{v:.8f}" for v in row]))
        w = r.get("frequency_au")
        self.polar_note.configure(
            text=f"Source: {r['source']}\nLine: {r.get('line') or '—'}\nOrientation: {r.get('orientation','as reported')}\nW: {w if w is not None else 'unknown'} a.u. / {'static' if w==0 else 'response / unspecified'}\n1 a.u. = 0.148184711472 A^3"
        )

    def export_forces(self):
        if not self.calc:
            return
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(
            [
                "Frame",
                "Energy kind",
                "Energy / Eh",
                "Atom",
                "Element",
                "Fx / Eh/Bohr",
                "Fy / Eh/Bohr",
                "Fz / Eh/Bohr",
                "Norm / Eh/Bohr",
            ]
        )
        for i in range(len(self.calc.frames)):
            d = frame_analysis(self.calc, i)
            e = d["energy"] or {}
            force = d["force"]
            if force:
                for j, (v, n) in enumerate(
                    zip(force["vectors_hartree_bohr"], force["norms_hartree_bohr"])
                ):
                    w.writerow(
                        [
                            i + 1,
                            e.get("kind"),
                            e.get("hartree"),
                            j + 1,
                            ELEMENTS[self.calc.atoms[j]],
                            *v,
                            n,
                        ]
                    )
            else:
                w.writerow([i + 1, e.get("kind"), e.get("hartree")])
        self.save("Energy and forces", ".csv", out.getvalue())

    def export_polar(self):
        i = self.polar_source.current()
        if not 0 <= i < len(self.polar_records):
            return
        r = self.polar_records[i]
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["Source", r["source"]])
        w.writerow(["Frequency / a.u.", r.get("frequency_au")])
        w.writerow(["Tensor / a.u.", "X", "Y", "Z"])
        for j, row in enumerate(r["tensor_au"]):
            w.writerow(["XYZ"[j], *row])
        for k in ["mean_au", "mean_A3", "anisotropy_au"]:
            w.writerow([k, r[k]])
        self.save("Polarizability", ".csv", out.getvalue())
