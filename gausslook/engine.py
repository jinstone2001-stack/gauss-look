from __future__ import annotations
import copy, csv, io, json, os, re, shutil, subprocess, tempfile, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from .model import Calculation, clean, digest, xyz_text, HARTREE_KJ
from .parser import parse_file
from .fields import read_cube, isosurface, field_operation, integrate, sample, contour, Field
from .analysis import (
    quality,
    capabilities,
    spectrum,
    compare,
    alignment,
    measure,
    thermochemistry_correction,
    orbital_analysis,
    frame_analysis,
    polarizability_analysis,
)


class Engine:
    def __init__(self, root=None, gaussian_dir=None):
        self.root = Path(root or Path.cwd()).resolve()
        self.calcs = {}
        self.fields = {}
        self.tasks = {}
        self.checkpoints = {}
        self.reload_sources = {}
        self.orbital_cache = {}
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.lock = threading.RLock()
        self.work = Path(tempfile.mkdtemp(prefix="gausslook-"))
        self.gaussian_dir = Path(gaussian_dir).resolve() if gaussian_dir else None
        self.utilities = {
            n: self._find(n) for n in ["formchk", "cubegen", "freqchk", "testrt", "g16"]
        }

    def _find(self, n):
        p = self.gaussian_dir / n if self.gaussian_dir else None
        return str(p) if p and p.is_file() and os.access(p, os.X_OK) else shutil.which(n)

    def close(self):
        for task in list(self.tasks.values()):
            if task.get("_process") is not None and task["_process"].poll() is None:
                task["_process"].terminate()
        self.pool.shutdown(wait=False, cancel_futures=True)

    def add(self, c):
        c.id = uuid.uuid4().hex[:12]
        with self.lock:
            self.calcs[c.id] = c
        return c.id

    def load(self, path, restricted=False):
        path = Path(path).expanduser().resolve()
        if restricted and not path.is_relative_to(self.root):
            raise ValueError("서버 --root 폴더 안의 파일만 열 수 있습니다.")
        if not path.is_file():
            raise ValueError("파일을 찾을 수 없습니다.")
        if path.suffix.lower() == ".chk":
            return {"task": self.submit("formchk", lambda t: self.convert_checkpoint(path, t))}
        if path.suffix.lower() in (".cube", ".cub"):
            f = read_cube(path)
            fid = uuid.uuid4().hex[:12]
            self.fields[fid] = f
            cid = self.add(
                Calculation(
                    f.name,
                    str(path),
                    kind="cube",
                    atoms=f.atoms,
                    frames=[{"coords": f.coords, "step": 1}],
                    properties={"field_id": fid},
                )
            )
            return {"ids": [cid], "field_id": fid}
        if path.suffix.lower() == ".glproj":
            return self.load_project(json.loads(path.read_text()))
        cs = parse_file(path)
        ids = [self.add(c) for c in cs]
        for cid in ids:
            self.reload_sources[cid] = str(path)
        if path.suffix.lower() in (".fchk", ".fch"):
            for cid in ids:
                self.checkpoints[cid] = str(path)
        return {"ids": ids}

    def upload(self, name, data):
        if len(data) > 256 * 1024 * 1024:
            raise ValueError("업로드 한도는 파일당 256 MiB입니다.")
        name = Path(name.replace("\\", "/")).name
        if not name or name in (".", ".."):
            raise ValueError("잘못된 파일명")
        d = self.work / uuid.uuid4().hex
        d.mkdir()
        p = d / name
        p.write_bytes(data)
        return self.load(p)

    def listing(self):
        with self.lock:
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "kind": c.kind,
                    "atoms": len(c.atoms),
                    "frames": len(c.frames),
                    "source": c.source,
                    "status": c.status,
                    "checkpoint_linked": bool(self.checkpoints.get(c.id)),
                }
                for c in self.calcs.values()
            ]

    def get(self, cid):
        if cid not in self.calcs:
            raise ValueError("계산을 찾을 수 없습니다.")
        return self.calcs[cid]

    def detail(self, cid):
        c = self.get(cid)
        d = c.public()
        d["quality"] = quality(c)
        d["capabilities"] = capabilities(c, self.utilities)
        d["orbital_analysis"] = orbital_analysis(c)
        d["polarizability_analysis"] = polarizability_analysis(c)
        d["final_frame_analysis"] = frame_analysis(c)
        d["orbital_surface_ready"] = bool(
            self.checkpoints.get(cid) and self.utilities.get("cubegen")
        )
        d["checkpoint_linked"] = bool(self.checkpoints.get(cid))
        for entry in d["capabilities"]:
            if entry["feature"] == "cube 생성":
                entry["available"] = bool(
                    self.checkpoints.get(cid) and self.utilities.get("cubegen")
                )
                entry["reason"] = (
                    "사용 가능"
                    if entry["available"]
                    else "chk/fchk와 Gaussian cubegen이 필요합니다."
                )
        if "polarizability_au" in c.properties:
            a = np.asarray(c.properties["polarizability_au"])
            d["properties"]["polarizability_mean_au"] = float(np.trace(a) / 3)
            d["properties"]["polarizability_mean_A3"] = float(np.trace(a) / 3 * 0.148184711472)
            d["properties"]["polarizability_eigenvalues_au"] = np.linalg.eigvalsh(a).tolist()
        return clean(d)

    def submit(self, title, fn):
        tid = uuid.uuid4().hex[:12]
        task = {
            "id": tid,
            "title": title,
            "status": "queued",
            "progress": 0,
            "cancel": False,
            "started": time.time(),
        }
        self.tasks[tid] = task

        def run():
            if task["cancel"]:
                task["status"] = "cancelled"
                return
            task["status"] = "running"
            try:
                result = fn(task)
                if task["cancel"]:
                    task["status"] = "cancelled"
                else:
                    task.update(status="done", progress=100, result=clean(result))
            except Exception as exc:
                task.update(status="cancelled" if task["cancel"] else "error", error=str(exc))

        task["_future"] = self.pool.submit(run)
        return tid

    def task(self, tid):
        return clean({k: v for k, v in self.tasks[tid].items() if not k.startswith("_")})

    def cancel(self, tid):
        t = self.tasks[tid]
        t["cancel"] = True
        p = t.get("_process")
        if p is not None and p.poll() is None:
            p.terminate()
        return self.task(tid)

    def utility(self, name, args, task, stdin=None, timeout=300):
        exe = self.utilities.get(name)
        if not exe:
            raise ValueError(
                f"Gaussian {name}를 찾지 못했습니다. Gaussian 환경을 먼저 source하거나 --gaussian-dir를 지정하세요."
            )
        p = subprocess.Popen(
            [exe, *map(str, args)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.work,
        )
        task["_process"] = p
        try:
            out, _ = p.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            out, _ = p.communicate()
            raise ValueError(f"{name} 제한 시간 초과. 실행 환경/입력을 확인하세요.\n" + out[-2000:])
        task["output"] = out[-15000:]
        if task["cancel"]:
            raise ValueError("사용자 취소")
        if p.returncode != 0:
            raise ValueError(f"{name} 실패 ({p.returncode})\n" + out[-3000:])
        return out

    def convert_checkpoint(self, path, task):
        target = self.work / uuid.uuid4().hex
        target.mkdir()
        chk = target / "source.chk"
        shutil.copy2(path, chk)
        fchk = target / (path.stem + ".fchk")
        task["progress"] = 15
        self.utility("formchk", [chk, fchk], task)
        if not fchk.is_file():
            raise ValueError("formchk가 fchk를 생성하지 않았습니다.")
        task["progress"] = 80
        result = self.load(fchk)
        for cid in result["ids"]:
            c = self.get(cid)
            c.properties["checkpoint_file"] = str(path)
            c.properties["converted_from_chk"] = True
            self.reload_sources[cid] = str(path)
        return result

    def reload_source(self, cid):
        source = self.reload_sources.get(cid)
        if not source:
            raise ValueError("원본 경로가 없는 snapshot입니다. 원본 log/chk/fchk를 다시 여세요.")
        return self.load(source)

    def generate(self, cid, kind, orbital, spin, grid, task):
        c = self.get(cid)
        source = self.checkpoints.get(cid)
        if not source:
            raise ValueError(
                "MO 표면에는 fchk 또는 변환 가능한 chk가 필요합니다. 로그와 chk를 모두 연 뒤 연결할 수도 있습니다."
            )
        if kind == "mo":
            if spin not in ("alpha", "beta") or not 1 <= int(orbital) <= 100000:
                raise ValueError("spin과 1부터 시작하는 MO 번호를 확인하세요.")
            channel = c.orbitals.get(spin)
            if channel is None or int(orbital) > len(channel.get("energies_eV", [])):
                raise ValueError("선택한 spin/MO 번호가 checkpoint의 오비탈 범위를 벗어납니다.")
            if not channel.get("has_coefficients", False):
                raise ValueError(
                    "이 checkpoint에 선택한 MO 계수가 없습니다. MO coefficient를 저장한 chk/fchk가 필요합니다."
                )
            spec = ("AMO=" if spin == "alpha" else "BMO=") + str(int(orbital))
        elif kind in ("density", "potential", "spin"):
            spec = {"density": "Density=SCF", "potential": "Potential=SCF", "spin": "Spin=SCF"}[
                kind
            ]
        else:
            raise ValueError("지원 field: mo, density, potential, spin")
        if grid not in ("coarse", "medium", "fine"):
            raise ValueError("grid는 coarse/medium/fine입니다.")
        out = self.work / (uuid.uuid4().hex + ".cube")
        task["progress"] = 10
        self.utility(
            "cubegen",
            ["0", spec, source, out, {"coarse": "-2", "medium": "-3", "fine": "-4"}[grid], "h"],
            task,
        )
        task["progress"] = 85
        return self.load(out)

    def orbital_surface(self, cid, spin, orbital, grid, level, task):
        c = self.get(cid)
        level = abs(float(level))
        if level <= 0:
            raise ValueError("MO 등치값은 양수여야 합니다.")
        source = self.checkpoints.get(cid)
        if not source:
            raise ValueError("chk/fchk를 먼저 여세요. log만으로 MO 등치면을 생성할 수 없습니다.")
        stat = Path(source).stat()
        key = (source, stat.st_size, stat.st_mtime_ns, spin, int(orbital), grid)
        fid = self.orbital_cache.get(key)
        if fid not in self.fields:
            result = self.generate(cid, "mo", int(orbital), spin, grid, task)
            fid = result["field_id"]
            self.orbital_cache[key] = fid
        f = self.fields[fid]
        meshes = []
        for signed in (level, -level):
            if f.values[:, :, :, 0].min() < signed < f.values[:, :, :, 0].max():
                meshes.append(isosurface(f, level=signed, max_faces=45000))
        if not meshes:
            raise ValueError(
                "선택 등치값에서 MO 표면이 없습니다. 등치값을 줄이거나 격자를 확인하세요."
            )
        task["progress"] = 95
        return {
            "orbital_surface": True,
            "calculation_id": cid,
            "field_id": fid,
            "orbital": int(orbital),
            "spin": spin,
            "meshes": meshes,
            "reference_coords": f.coords,
            "note": "± colors indicate orbital phase, not positive/negative charge.",
        }

    def link_checkpoint(self, log_id, checkpoint_id):
        log = self.get(log_id)
        chk = self.get(checkpoint_id)
        if not self.checkpoints.get(checkpoint_id):
            raise ValueError("연결 대상은 열린 chk/fchk여야 합니다.")
        if log.kind in ("checkpoint", "cube", "input", "builder", "structure"):
            raise ValueError("로그 계산을 먼저 선택한 뒤 chk/fchk를 연결하세요.")
        if log.atoms != chk.atoms or not log.frames or not chk.frames:
            raise ValueError("원자 종류·순서·구조가 일치해야 합니다.")
        if (log.charge is not None and chk.charge is not None and log.charge != chk.charge) or (
            log.multiplicity is not None
            and chk.multiplicity is not None
            and log.multiplicity != chk.multiplicity
        ):
            raise ValueError("전하/다중도가 다릅니다. 다른 계산 파일을 연결할 수 없습니다.")
        fitted = alignment(log, chk)
        if fitted["rmsd_A"] > 0.002:
            raise ValueError(
                f"최종 구조가 다릅니다 (정렬 RMSD {fitted['rmsd_A']:.6f} Å). 같은 구조의 파일만 연결하세요."
            )
        # The merged viewer uses checkpoint axes, so cubegen meshes overlay correctly.
        rotation = np.asarray(fitted["rotation"])
        x = np.asarray(log.frames[-1]["coords"])
        y = np.asarray(chk.frames[-1]["coords"])
        new = copy.deepcopy(log)
        new.name = log.name + " + checkpoint"
        new.properties["linked_sources"] = [log.source, chk.source]
        new.properties["formatted_checkpoint"] = self.checkpoints[checkpoint_id]
        new.properties["link_rmsd_A"] = fitted["rmsd_A"]
        for f in new.frames:
            f["coords"] = ((np.asarray(f["coords"]) - x.mean(0)) @ rotation.T + y.mean(0)).tolist()
        for record in new.force_records:
            record["forces_hartree_bohr"] = (
                np.asarray(record["forces_hartree_bohr"]) @ rotation.T
            ).tolist()
            record["coordinate_system"] = "aligned to checkpoint axes"
        for mode in new.modes:
            if len(mode.get("displacements", [])) == len(log.atoms):
                mode["displacements"] = (np.asarray(mode["displacements"]) @ rotation.T).tolist()
        new.orbitals = copy.deepcopy(chk.orbitals)
        if (
            new.frames[-1].get("force_record") is None
            and chk.frames[-1].get("force_record") is not None
        ):
            new.frames[-1]["force_record"] = len(new.force_records)
            new.force_records.append(
                copy.deepcopy(chk.force_records[chk.frames[-1]["force_record"]])
            )
        if (
            new.frames[-1].get("energy_hartree") is None
            and chk.frames[-1].get("energy_hartree") is not None
        ):
            new.frames[-1]["energy_hartree"] = chk.frames[-1]["energy_hartree"]
            new.frames[-1]["energy_kind"] = "checkpoint / " + chk.frames[-1].get(
                "energy_kind", "Total Energy"
            )
        if not new.modes:
            new.modes = copy.deepcopy(chk.modes)
            for mode in new.modes:
                mode["reference_frame"] = len(new.frames) - 1
        if "polarizability_au" in chk.properties:
            new.properties["polarizability_au"] = copy.deepcopy(chk.properties["polarizability_au"])
            new.properties.setdefault("polarizability_records", []).extend(
                copy.deepcopy(chk.properties.get("polarizability_records", []))
            )
        new.properties["checkpoint_link_note"] = (
            "Geometry, atom order, charge and spin validated. Method/state consistency still requires the original calculation inputs."
        )
        new.warnings.append(
            "연결 전후 method/basis/전자 상태가 같은지 원본 입력을 확인하세요. 구조는 checkpoint 좌표계로 정렬했습니다."
        )
        cid = self.add(new)
        self.checkpoints[cid] = self.checkpoints[checkpoint_id]
        if log_id in self.reload_sources:
            self.reload_sources[cid] = self.reload_sources[log_id]
        return {"ids": [cid]}

    def action(self, name, cid=None, **p):
        c = self.get(cid) if cid else None
        if name == "reload_source":
            return self.reload_source(cid)
        if name == "frame_analysis":
            return clean(frame_analysis(c, int(p.get("frame", -1))))
        if name == "orbital_analysis":
            return orbital_analysis(c)
        if name == "link_checkpoint":
            return self.link_checkpoint(cid, p["checkpoint_id"])
        if name == "orbital_surface":
            return {
                "task": self.submit(
                    "MO surface",
                    lambda t: self.orbital_surface(
                        cid,
                        p.get("spin", "alpha"),
                        p["orbital"],
                        p.get("grid", "coarse"),
                        p.get("level", 0.03),
                        t,
                    ),
                )
            }
        if name == "spectrum":
            return spectrum(c, **p)
        if name == "measure":
            return measure(c.frames[int(p.get("frame", -1))]["coords"], p["indices"])
        if name == "compare":
            return compare(
                [self.get(i) for i in p.get("ids", list(self.calcs))], p.get("energy_kind")
            )
        if name == "align":
            return alignment(c, self.get(p["other_id"]))
        if name == "thermo":
            return thermochemistry_correction(c, **p)
        if name == "field_info":
            return self.fields[p["field_id"]].info()
        if name == "mesh":
            f = self.fields[p.pop("field_id")]
            mapped = p.pop("mapped_field", None)
            mesh = isosurface(f, **p)
            if mapped:
                mesh["mapped_values"] = clean(
                    sample(self.fields[mapped], mesh["vertices"]).tolist()
                )
            return mesh
        if name == "contour":
            return clean(contour(self.fields[p.pop("field_id")], **p))
        if name == "integrate":
            return integrate(self.fields[p["field_id"]], int(p.get("channel", 0)))
        if name == "field_operation":
            a = self.fields[p["field_id"]]
            b = self.fields[p["other_id"]] if p.get("other_id") else None
            f = field_operation(a, p["operation"], b, float(p.get("factor", 1)))
            fid = uuid.uuid4().hex[:12]
            self.fields[fid] = f
            return {"field_id": fid, "info": f.info()}
        if name == "generate_cube":
            return {
                "task": self.submit(
                    "cubegen",
                    lambda t: self.generate(
                        cid,
                        p.get("kind", "mo"),
                        p.get("orbital", 1),
                        p.get("spin", "alpha"),
                        p.get("grid", "coarse"),
                        t,
                    ),
                )
            }
        if name == "smiles":
            from .chemistry import from_smiles

            return {
                "task": self.submit(
                    "SMILES conformers",
                    lambda t: {
                        "ids": [self.add(from_smiles(p["smiles"], p.get("conformers", 12)))]
                    },
                )
            }
        if name == "isotope":
            from .chemistry import isotope_modes

            def run(t):
                modes = isotope_modes(c.source, p["masses"])
                new = copy.deepcopy(c)
                new.name += " / isotope"
                new.modes = modes
                new.energies = []
                new.thermo = {}
                new.orbitals = {}
                new.properties = {"isotope_masses": p["masses"]}
                new.warnings = [
                    "동위원소 Hessian 재분석: 진동수·변위만 계산. 기존 IR/Raman 강도를 재사용하지 않습니다."
                ]
                return {"ids": [self.add(new)]}

            return {"task": self.submit("Isotope Hessian analysis", run)}
        if name == "input":
            from .chemistry import gaussian_input

            return {"text": gaussian_input(c, **p), "filename": "gausslook.gjf"}
        if name == "edit":
            new = Calculation(
                c.name + " / edited",
                kind="builder",
                charge=c.charge,
                multiplicity=c.multiplicity,
                atoms=list(c.atoms),
                frames=[
                    {
                        "coords": copy.deepcopy(c.frames[int(p.get("frame", -1))]["coords"]),
                        "step": 1,
                    }
                ],
            )
            ids = sorted(set(map(int, p.get("indices", []))))
            if any(i < 0 or i >= len(new.atoms) for i in ids):
                raise ValueError("원자 번호 범위를 확인하세요.")
            if p["operation"] == "delete":
                new.atoms = [z for i, z in enumerate(new.atoms) if i not in ids]
                new.frames[0]["coords"] = [
                    v for i, v in enumerate(new.frames[0]["coords"]) if i not in ids
                ]
            elif p["operation"] == "translate":
                shift = np.asarray(p["vector"], float)
                if shift.shape != (3,):
                    raise ValueError("이동 벡터는 3개 성분이 필요합니다.")
                for i in ids:
                    new.frames[0]["coords"][i] = (
                        np.asarray(new.frames[0]["coords"][i]) + shift
                    ).tolist()
            elif p["operation"] == "coordinate":
                new.frames[0]["coords"][ids[0]] = list(map(float, p["coords"]))
            else:
                raise ValueError("편집: delete/translate/coordinate")
            if not new.atoms:
                raise ValueError("모든 원자를 삭제할 수 없습니다.")
            new.warnings = ["편집된 새 구조: 기존 에너지·모드·오비탈 결과의 연결을 해제했습니다."]
            return {"ids": [self.add(new)]}
        if name == "reaction":
            rows = []
            total = 0.0
            for row in p["terms"]:
                item = self.get(row["id"])
                field = row.get("energy", "gibbs")
                e = (
                    item.thermo.get("gibbs")
                    if field == "gibbs"
                    else (item.energies[-1]["hartree"] if item.energies else None)
                )
                if e is None:
                    raise ValueError(item.name + "에 요청 에너지가 없습니다.")
                coefficient = float(row["coefficient"])
                total += coefficient * e
                rows.append(
                    {
                        "id": item.id,
                        "coefficient": coefficient,
                        "energy": field,
                        "hartree": e,
                        "route": item.route,
                        "temperature_K": item.thermo.get("temperature_K"),
                    }
                )
            return {
                "delta_hartree": total,
                "delta_kJ_mol": total * HARTREE_KJ,
                "terms": rows,
                "note": "화학양론·계산 수준·용매·온도·표준상태 일치 여부를 확인하세요.",
            }
        if name == "xyz":
            return {"text": xyz_text(c, int(p.get("frame", -1))), "filename": "structure.xyz"}
        if name == "source":
            if not c.source or not Path(c.source).is_file():
                raise ValueError("원본 파일이 없습니다.")
            data = Path(c.source).read_bytes()
            if b"\x00" in data[:1024]:
                raise ValueError("바이너리 파일은 원문 텍스트로 표시하지 않습니다.")
            start = max(0, int(p.get("start_line", 1)) - 1)
            rows = data.decode("utf-8", errors="replace").splitlines()
            return {
                "start_line": start + 1,
                "total_lines": len(rows),
                "text": "\n".join(rows[start : start + min(3000, int(p.get("count", 500)))]),
            }
        raise ValueError("지원되지 않는 작업: " + name)

    def project(self):
        return {
            "format": "GaussLook project",
            "version": 1,
            "calculations": [c.public() for c in self.calcs.values()],
            "note": "계산 snapshot을 포함합니다. 공간장 원본·파동함수는 별도 보관하세요.",
        }

    def load_project(self, data):
        if data.get("format") != "GaussLook project" or data.get("version") != 1:
            raise ValueError("지원하지 않는 프로젝트 형식")
        allowed = set(Calculation.__dataclass_fields__)
        ids = []
        for row in data["calculations"]:
            c = Calculation(**{k: v for k, v in row.items() if k in allowed})
            # A project file is a snapshot, not permission to read arbitrary host paths.
            c.source = ""
            for key in ["formatted_checkpoint", "checkpoint_file", "linked_sources"]:
                c.properties.pop(key, None)
            c.properties.pop("field_id", None)
            c.warnings.append("프로젝트 snapshot: 공간장·원본 파일은 다시 연결해야 합니다.")
            ids.append(self.add(c))
        return {"ids": ids}

    def demo(self):
        c = Calculation(
            "DEMO · water (synthetic UI fixture)",
            kind="demonstration",
            charge=0,
            multiplicity=1,
            atoms=[8, 1, 1],
            frames=[{"coords": [[0, 0, 0], [0.7586, 0, 0.5043], [-0.7586, 0, 0.5043]], "step": 1}],
        )
        c.modes = [
            {"frequency_cm1": f, "ir_km_mol": i, "raman_activity": a, "displacements": d}
            for f, i, a, d in [
                (1595.0, 32.0, 8.0, [[0, 0, 0.1], [0.2, 0, -0.1], [-0.2, 0, -0.1]]),
                (3657.0, 2.0, 70.0, [[0, 0, -0.1], [0.2, 0, 0.2], [-0.2, 0, 0.2]]),
                (3756.0, 45.0, 30.0, [[0.1, 0, 0], [0.2, 0, 0.2], [0.2, 0, -0.2]]),
            ]
        ]
        c.orbitals = {
            "alpha": {
                "energies_eV": [-20.0, -14.0, -8.0, -6.0, -4.0, 2.0, 4.0],
                "occupations": [2, 2, 2, 2, 2, 0, 0],
            }
        }
        c.properties["charges"] = {"Demo charges": [-0.8, 0.4, 0.4]}
        c.properties["demo"] = True
        c.warnings = ["화면 시연용 합성 자료입니다. 실제 Gaussian 계산값이 아닙니다."]
        cid = self.add(c)
        grid = np.linspace(-3, 3, 38)
        x, y, z = np.meshgrid(grid, grid, grid, indexing="ij")
        vals = x * np.exp(-(x * x + y * y + z * z))
        f = Field(
            "DEMO analytic field",
            np.array([-3, -3, -3.0]),
            np.eye(3) * (6 / 37),
            vals[:, :, :, None],
            c.atoms,
            c.frames[0]["coords"],
        )
        fid = uuid.uuid4().hex[:12]
        self.fields[fid] = f
        c.properties["field_id"] = fid
        return {"ids": [cid], "field_id": fid}
