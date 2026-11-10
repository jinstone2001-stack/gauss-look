"""Loss-aware parsers. No missing numerical result is silently converted to zero."""

from __future__ import annotations
import re
from pathlib import Path
import numpy as np
from .model import Calculation, ELEMENTS, HARTREE_EV, BOHR_ANG, digest

FLOAT = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[DEde][-+]?\d+)?"


def nums(text):
    return [float(v.replace("D", "E").replace("d", "e")) for v in re.findall(FLOAT, text)]


def parse_log(text, name, source):
    chunks = re.split(
        r"(?m)^\s*(?:--Link1--|Link1:\s+Proceeding to internal job step number[^\n]*)\s*$", text
    )
    # Independent concatenated Gaussian runs can lack an explicit Link1 marker.
    expanded = []
    for chunk in chunks:
        expanded.extend(re.split(r"(?m)(?=^\s*Initial command:)", chunk))
    result = []
    cursor = 0
    for chunk in expanded:
        if not re.search(r"SCF Done:|orientation:|Frequencies --|#\s*\w|Excited State\s+\d", chunk):
            continue
        start = text.find(chunk, cursor)
        cursor = max(cursor, start + len(chunk))
        offset = text[: max(0, start)].count("\n")
        calc = _parse_section(chunk, f"{name} / job {len(result)+1}", source)
        for record in (
            calc.frames + calc.energies + calc.modes + calc.convergence + calc.transitions
        ):
            if record.get("line") is not None:
                record["line"] += offset
        result.append(calc)
    if not result:
        raise ValueError(
            "Gaussian 결과 레코드를 찾지 못했습니다. 전체 .log/.out 파일을 확인하세요."
        )
    return result


def _parse_section(text, name, source):
    c = Calculation(name, source)
    lines = text.splitlines()
    geometries = []
    current_modes = []
    c.status["termination"] = (
        "normal"
        if "Normal termination of Gaussian" in text
        else ("error" if "Error termination" in text else "incomplete")
    )
    routes = re.findall(r"(?ms)^\s*(#[^\n]*(?:\n(?!\s*-{5,})[^\n]+)*)\n\s*-{5,}", text)
    if routes:
        c.route = " ".join(routes[0].split())
    else:
        route = next((x.strip() for x in lines if x.strip().startswith("#")), "")
        c.route = route
    if re.search(r"\bopt\b", c.route, re.I) or (
        not c.route and "Optimization completed" in text and "Frequencies --" not in text
    ):
        c.kind = "optimization"
        c.status["optimization"] = (
            "converged"
            if "Optimization completed" in text or "Stationary point found" in text
            else "incomplete"
        )
    for token, kind in [
        ("irc", "irc"),
        ("scan", "scan"),
        ("bomd", "trajectory"),
        ("admp", "trajectory"),
    ]:
        if re.search(r"\b" + token + r"\b", c.route, re.I):
            c.kind = kind
    if "freq" in c.route.lower():
        c.properties["frequency_requested"] = True
    if c.kind == "unknown":
        c.kind = "frequency" if "freq" in c.route.lower() else "single_point"
    charge = re.search(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", text)
    if charge:
        c.charge, c.multiplicity = map(int, charge.groups())
    for i, line in enumerate(lines):
        if re.search(r"(?:Standard|Input|Z-Matrix) orientation:", line):
            j = i + 1
            dashes = 0
            rows = []
            zs = []
            while j < len(lines) and j < i + 20 and dashes < 2:
                if re.match(r"\s*-{5,}", lines[j]):
                    dashes += 1
                j += 1
            while j < len(lines) and not re.match(r"\s*-{5,}", lines[j]):
                fields = lines[j].split()
                if len(fields) >= 6:
                    try:
                        zs.append(int(fields[1]))
                        rows.append([float(x.replace("D", "E")) for x in fields[3:6]])
                    except ValueError:
                        break
                j += 1
            if rows:
                geometries.append(
                    {"coords": rows, "atoms": zs, "line": i + 1, "standard": "Standard" in line}
                )
        m = re.search(r"SCF Done:\s+E\((.*?)\)\s*=\s*(" + FLOAT + ")", line)
        if m:
            c.energies.append({"kind": "SCF " + m[1], "hartree": nums(m[2])[0], "line": i + 1})
            c.status["scf"] = "converged"
        patterns = [
            ("MP2", r"EUMP2\s*=\s*(" + FLOAT + ")"),
            ("CCSD(T)", r"CCSD\(T\)\s*=\s*(" + FLOAT + ")"),
            ("CCSD", r"E\(CORR\)\s*=\s*(" + FLOAT + ")"),
            ("ONIOM", r"ONIOM: extrapolated energy\s*=\s*(" + FLOAT + ")"),
            ("Excited total", r"Total Energy, E\([^)]*\)\s*=\s*(" + FLOAT + ")"),
            ("Composite", r"G[234]\([^)]*\)\s*=\s*(" + FLOAT + ")"),
        ]
        for kind, pattern in patterns:
            m = re.search(pattern, line)
            if m:
                c.energies.append({"kind": kind, "hartree": nums(m[1])[0], "line": i + 1})
        if "Convergence failure" in line:
            c.status["scf"] = "failed"
        m = re.match(
            r"\s*(Maximum Force|RMS\s+Force|Maximum Displacement|RMS\s+Displacement)\s+("
            + FLOAT
            + r")\s+("
            + FLOAT
            + r")\s+(YES|NO)",
            line,
        )
        if m:
            c.convergence.append(
                {
                    "item": " ".join(m[1].split()),
                    "value": nums(m[2])[0],
                    "threshold": nums(m[3])[0],
                    "passed": m[4] == "YES",
                    "line": i + 1,
                }
            )
        if "Frequencies --" in line:
            current_modes = []
            for f in nums(line.split("--", 1)[1]):
                mode = {"frequency_cm1": f, "line": i + 1, "displacements": []}
                c.modes.append(mode)
                current_modes.append(mode)
        for label, key in [
            ("Red. masses", "reduced_mass_amu"),
            ("Frc consts", "force_constant"),
            ("IR Inten", "ir_km_mol"),
            ("Raman Activ", "raman_activity"),
            ("Rot. str.", "vcd_strength"),
            ("Depolar (P)", "depolarization"),
        ]:
            if label in line and "--" in line:
                for mode, v in zip(current_modes, nums(line.split("--", 1)[1])):
                    mode[key] = v
        if re.match(r"\s*Atom\s+AN\s+X", line) and current_modes:
            j = i + 1
            while j < len(lines):
                cells = lines[j].split()
                if len(cells) < 2 + 3 * len(current_modes) or not cells[0].isdigit():
                    break
                values = nums(" ".join(cells[2:]))
                for k, mode in enumerate(current_modes):
                    mode["displacements"].append(values[3 * k : 3 * k + 3])
                j += 1
        terms = {
            "Zero-point correction=": "zpe_correction",
            "Thermal correction to Energy=": "energy_correction",
            "Thermal correction to Enthalpy=": "enthalpy_correction",
            "Thermal correction to Gibbs Free Energy=": "gibbs_correction",
            "Sum of electronic and zero-point Energies=": "electronic_zpe",
            "Sum of electronic and thermal Energies=": "electronic_thermal",
            "Sum of electronic and thermal Enthalpies=": "enthalpy",
            "Sum of electronic and thermal Free Energies=": "gibbs",
        }
        for label, key in terms.items():
            if label in line:
                v = nums(line.split("=", 1)[1])
                if v:
                    c.thermo[key] = v[0]
        m = re.search(
            r"Temperature\s+(" + FLOAT + r")\s+Kelvin.\s+Pressure\s+(" + FLOAT + r")\s+Atm", line
        )
        if m:
            c.thermo.update(temperature_K=nums(m[1])[0], pressure_atm=nums(m[2])[0])
        if "Dipole moment (field-independent basis" in line and i + 1 < len(lines):
            m = re.search(
                r"X=\s*("
                + FLOAT
                + r")\s+Y=\s*("
                + FLOAT
                + r")\s+Z=\s*("
                + FLOAT
                + r")\s+Tot=\s*("
                + FLOAT
                + r")",
                lines[i + 1],
            )
            if m:
                c.properties["dipole_debye"] = list(map(lambda x: nums(x)[0], m.groups()))
        if "Exact polarizability:" in line:
            v = nums(line.split(":", 1)[1])
            if len(v) == 6:
                c.properties["polarizability_au"] = [
                    [v[0], v[1], v[3]],
                    [v[1], v[2], v[4]],
                    [v[3], v[4], v[5]],
                ]
        m = re.search(r"S\*\*2 before annihilation\s*(" + FLOAT + r")", line)
        if m:
            c.properties["s2_before"] = nums(m[1])[0]
        m = re.search(
            r"Excited State\s+(\d+):\s+(.*?)\s+("
            + FLOAT
            + r")\s+eV\s+("
            + FLOAT
            + r")\s+nm\s+f=\s*("
            + FLOAT
            + ")",
            line,
        )
        if m:
            c.transitions.append(
                {
                    "state": int(m[1]),
                    "symmetry": m[2],
                    "energy_eV": nums(m[3])[0],
                    "wavelength_nm": nums(m[4])[0],
                    "oscillator_strength": nums(m[5])[0],
                    "line": i + 1,
                }
            )
        m = re.search(
            r"\b(\d+)\s+([A-Za-z]+)\s+Isotropic\s*=\s*("
            + FLOAT
            + r")\s+Anisotropy\s*=\s*("
            + FLOAT
            + ")",
            line,
        )
        if m:
            c.properties.setdefault("nmr", []).append(
                {
                    "atom": int(m[1]),
                    "element": m[2],
                    "shielding_ppm": nums(m[3])[0],
                    "anisotropy_ppm": nums(m[4])[0],
                }
            )
        if re.match(r"\s*(?:Mulliken|APT|ESP|Hirshfeld|Natural Population).*charges", line, re.I):
            label = line.strip().rstrip(":")
            rows = []
            for nxt in lines[i + 1 : i + 100000]:
                cells = nxt.split()
                if re.match(r"\s*Sum of", nxt):
                    break
                if len(cells) >= 3 and cells[0].isdigit() and cells[1] in ELEMENTS:
                    try:
                        rows.append(float(cells[2].replace("D", "E")))
                    except ValueError:
                        break
                elif rows:
                    break
                elif len(rows) == 0 and nxt.strip() and not re.match(r"^\s*\d+\s*$", nxt):
                    if nxt != lines[i + 1]:
                        break
            if rows:
                c.properties.setdefault("charges", {})[label] = rows
        m = re.match(r"\s*(Alpha|Beta)\s+(occ\.|virt\.) eigenvalues --(.*)", line)
        if m:
            spin = m[1].lower()
            orb = c.orbitals.setdefault(spin, {"energies_eV": [], "occupations": []})
            # A new occupied block after virtuals denotes the next geometry.
            if m[2] == "occ." and orb.get("_virtual"):
                orb.update(energies_eV=[], occupations=[])
                orb["_virtual"] = False
            vals = nums(m[3])
            orb["energies_eV"] += [v * HARTREE_EV for v in vals]
            orb["occupations"] += [2 if m[2] == "occ." else 0] * len(vals)
            if m[2] == "virt.":
                orb["_virtual"] = True
    preferred = [g for g in geometries if g["standard"]] or geometries
    for k, g in enumerate(preferred):
        end = preferred[k + 1]["line"] if k + 1 < len(preferred) else len(lines) + 1
        es = [e for e in c.energies if g["line"] <= e["line"] < end]
        c.frames.append(
            {
                "coords": g["coords"],
                "energy_hartree": es[-1]["hartree"] if es else None,
                "line": g["line"],
                "step": k + 1,
            }
        )
    if preferred:
        c.atoms = preferred[-1]["atoms"]
    # Canonical alpha/beta occupations for unrestricted output are one electron each.
    if "beta" in c.orbitals:
        for o in c.orbitals.values():
            o["occupations"] = [min(1, v) for v in o["occupations"]]
    _cclib_enrich(c, text)
    if c.status["termination"] == "incomplete":
        c.warnings.append("미완성/실행 중 로그: 마지막 구조와 결과가 최종값이 아닐 수 있습니다.")
    if "Anharmonic" in text or "Duschinsky" in text:
        c.warnings.append(
            "비조화/vibronic 상세 항목은 원본 보기에서 확인하세요. 일반 모드 표와 혼합하지 않습니다."
        )
    return c


def _cclib_enrich(c, text):
    """Use cclib per job, never across unrelated Link1 calculations."""
    if not ("Gaussian, Inc." in text or "Gaussian 16:" in text or "Gaussian 09:" in text):
        return
    try:
        import io, logging
        from cclib.parser import Gaussian

        d = Gaussian(io.StringIO(text), loglevel=logging.CRITICAL).parse()
        c.properties["parser"] = "GaussLook + cclib"
        if hasattr(d, "atomnos") and not c.atoms:
            c.atoms = d.atomnos.tolist()
        if not c.frames and hasattr(d, "atomcoords"):
            c.frames = [{"coords": v.tolist(), "step": i + 1} for i, v in enumerate(d.atomcoords)]
        for attr, key in [("charge", "charge"), ("mult", "multiplicity")]:
            if getattr(c, key) is None and hasattr(d, attr):
                setattr(c, key, int(getattr(d, attr)))
        for kind, values in getattr(d, "atomcharges", {}).items():
            c.properties.setdefault("charges", {})[kind] = values.tolist()
        if hasattr(d, "atomspins"):
            c.properties["atomic_spin_density"] = {k: v.tolist() for k, v in d.atomspins.items()}
        if (
            hasattr(d, "polarizabilities")
            and len(d.polarizabilities)
            and "polarizability_au" not in c.properties
        ):
            c.properties["polarizability_au"] = d.polarizabilities[-1].tolist()
        if hasattr(d, "nmrtensors") and not c.properties.get("nmr"):
            c.properties["nmr"] = [
                {
                    "atom": int(i) + 1,
                    "element": ELEMENTS[c.atoms[int(i)]],
                    "shielding_ppm": float(np.trace(v["total"]) / 3),
                    "tensor": v["total"].tolist(),
                }
                for i, v in d.nmrtensors.items()
                if "total" in v
            ]
        if hasattr(d, "nmrcouplingtensors"):
            c.properties["nmr_coupling_tensors"] = {
                str(k): {
                    str(j): {a: b.tolist() if hasattr(b, "tolist") else b for a, b in t.items()}
                    for j, t in v.items()
                }
                for k, v in d.nmrcouplingtensors.items()
            }
        if hasattr(d, "moenergies"):
            for i, ev in enumerate(d.moenergies):
                ne = int(d.homos[i]) + 1
                factor = 1 if len(d.moenergies) == 2 else 2
                c.orbitals[["alpha", "beta"][i]] = {
                    "energies_eV": ev.tolist(),
                    "occupations": [factor if k < ne else 0 for k in range(len(ev))],
                }
        if hasattr(d, "mpenergies"):
            for order, value in enumerate(d.mpenergies[-1], 2):
                c.energies.append(
                    {"kind": "MP" + str(order), "hartree": float(value / HARTREE_EV), "line": None}
                )
        if hasattr(d, "ccenergies") and len(d.ccenergies):
            c.energies.append(
                {
                    "kind": "CC (cclib final)",
                    "hartree": float(d.ccenergies[-1] / HARTREE_EV),
                    "line": None,
                }
            )
        if not c.modes and hasattr(d, "vibfreqs"):
            for i, f in enumerate(d.vibfreqs):
                m = {
                    "frequency_cm1": float(f),
                    "displacements": d.vibdisps[i].tolist() if hasattr(d, "vibdisps") else [],
                }
                for attr, key in [("vibirs", "ir_km_mol"), ("vibramans", "raman_activity")]:
                    if hasattr(d, attr):
                        m[key] = float(getattr(d, attr)[i])
                c.modes.append(m)
        if hasattr(d, "etrotats"):
            for t, r in zip(c.transitions, d.etrotats):
                t["rotatory_strength"] = float(r)
    except Exception as exc:
        # Built-in parser remains usable for partial and new revision output.
        c.properties["cclib_fallback_reason"] = type(exc).__name__


def fchk_records(text):
    lines = text.splitlines()
    r = {}
    i = 2
    while i < len(lines):
        line = lines[i]
        i += 1
        m = re.match(r"^(.{1,43}?)\s+([IRCL])\s+(?:N=\s*(\d+)|(.*))$", line)
        if not m:
            continue
        key, typ, count, scalar = m.groups()
        key = key.strip()
        if count:
            n = int(count)
            v = []
            while len(v) < n and i < len(lines):
                if typ in ("R", "I"):
                    v += nums(lines[i])
                else:
                    v += lines[i].split()
                i += 1
            if len(v) != n:
                raise ValueError(f"fchk 배열 길이 불일치: {key} ({len(v)}/{n})")
            r[key] = v
        else:
            v = nums(scalar or "") if typ in ("R", "I") else [scalar]
            if v:
                r[key] = v[0]
    return r


def parse_fchk(text, name, source):
    r = fchk_records(text)
    c = Calculation(name, source, kind="checkpoint")
    zs = r.get("Atomic numbers", [])
    xyz = r.get("Current cartesian coordinates", [])
    if not zs or len(xyz) != 3 * len(zs):
        raise ValueError("fchk의 원자번호/Cartesian 좌표가 없거나 길이가 다릅니다.")
    c.atoms = list(map(int, zs))
    c.frames = [
        {"coords": (np.asarray(xyz).reshape(-1, 3) * BOHR_ANG).tolist(), "step": 1, "line": 1}
    ]
    c.charge = int(r["Charge"]) if "Charge" in r else None
    c.multiplicity = int(r["Multiplicity"]) if "Multiplicity" in r else None
    c.route = " ".join(text.splitlines()[:2])
    c.properties["basis_functions"] = r.get("Number of basis functions")
    for key in ["Total Energy", "SCF Energy", "MP2 Energy", "Cluster Energy"]:
        if key in r:
            c.energies.append({"kind": key, "hartree": r[key], "line": None})
    for spin in ["Alpha", "Beta"]:
        if spin + " Orbital Energies" in r:
            ev = [v * HARTREE_EV for v in r[spin + " Orbital Energies"]]
            ne = int(r.get("Number of " + spin.lower() + " electrons", 0))
            factor = 1 if "Beta Orbital Energies" in r else 2
            c.orbitals[spin.lower()] = {
                "energies_eV": ev,
                "occupations": [factor if k < ne else 0 for k in range(len(ev))],
            }
    for key in [
        "Mulliken Charges",
        "ESP Charges",
        "NPA Charges",
        "Hirshfeld Charges",
        "CM5 Charges",
    ]:
        if key in r:
            c.properties.setdefault("charges", {})[key] = r[key]
    if "Dipole Moment" in r:
        v = np.asarray(r["Dipole Moment"]) * 2.541746473
        c.properties["dipole_debye"] = v.tolist() + [float(np.linalg.norm(v))]
    if "Polarizability" in r and len(r["Polarizability"]) == 6:
        a = r["Polarizability"]
        c.properties["polarizability_au"] = [
            [a[0], a[1], a[3]],
            [a[1], a[2], a[4]],
            [a[3], a[4], a[5]],
        ]
    n = int(r.get("Number of Normal Modes", r.get("Number of normal modes", 0)))
    vib = r.get("Vib-E2", [])
    disp = r.get("Vib-Modes", [])
    for k in range(n):
        m = {"frequency_cm1": vib[k] if k < len(vib) else None, "displacements": []}
        for block, key in [
            (1, "reduced_mass_amu"),
            (2, "force_constant"),
            (3, "ir_km_mol"),
            (4, "raman_activity"),
        ]:
            if len(vib) > block * n + k:
                m[key] = vib[block * n + k]
        if len(disp) >= (k + 1) * 3 * len(zs):
            m["displacements"] = (
                np.asarray(disp[k * 3 * len(zs) : (k + 1) * 3 * len(zs)]).reshape(-1, 3).tolist()
            )
        if m["frequency_cm1"] is not None:
            c.modes.append(m)
    c.properties["has_hessian"] = "Cartesian Force Constants" in r
    c.properties["fchk_records"] = list(r)
    c.warnings.append("checkpoint에는 정상 종료·기하 수렴을 증명할 전체 로그가 없습니다.")
    return [c]


def parse_input(text, name, source):
    parts = re.split(r"(?mi)^\s*--Link1--\s*$", text)
    result = []
    for part in parts:
        c = Calculation(name, source, kind="input")
        lines = part.splitlines()
        route = []
        xyz = []
        for i, line in enumerate(lines):
            if line.strip().startswith("#"):
                j = i
                while j < len(lines) and lines[j].strip():
                    route.append(lines[j].strip())
                    j += 1
            if re.match(r"^\s*-?\d+\s+\d+\s*$", line):
                c.charge, c.multiplicity = map(int, line.split())
                for row in lines[i + 1 :]:
                    if not row.strip():
                        break
                    f = row.replace(",", " ").split()
                    if len(f) < 4:
                        raise ValueError(
                            "Z-matrix/복합 원자 지정은 원문 보존만 지원합니다. Cartesian 입력으로 변환하세요."
                        )
                    sym = f[0].split("(")[0]
                    z = (
                        int(sym)
                        if sym.isdigit()
                        else ELEMENTS.index(sym.capitalize()) if sym.capitalize() in ELEMENTS else 0
                    )
                    coords = nums(" ".join(f[-3:]))
                    if len(coords) != 3:
                        raise ValueError("Cartesian 좌표 형식을 확인하세요.")
                    c.atoms.append(z)
                    xyz.append(coords)
                break
        c.route = " ".join(route)
        if xyz:
            c.frames = [{"coords": xyz, "step": 1}]
        c.properties["input_original"] = part
        c.warnings.append("입력 구조입니다. 계산 결과·수렴 정보가 아닙니다.")
        result.append(c)
    return result


def parse_xyz(text, name, source):
    rows = text.splitlines()
    i = 0
    frames = []
    atoms = None
    while i < len(rows):
        if not rows[i].strip():
            i += 1
            continue
        n = int(rows[i])
        xyz = []
        zs = []
        for row in rows[i + 2 : i + 2 + n]:
            f = row.split()
            zs.append(ELEMENTS.index(f[0]) if f[0] in ELEMENTS else int(f[0]))
            xyz.append(list(map(float, f[1:4])))
        if len(xyz) != n or any(len(x) != 3 for x in xyz):
            raise ValueError("XYZ 원자 수/좌표 불일치")
        if atoms is not None and atoms != zs:
            raise ValueError("XYZ frame마다 원소 순서가 다릅니다.")
        atoms = zs
        frames.append({"coords": xyz, "step": len(frames) + 1})
        i += n + 2
    return [Calculation(name, source, kind="structure", atoms=atoms or [], frames=frames)]


def parse_file(path):
    p = Path(path)
    data = p.read_bytes()
    if len(data) > 512 * 1024 * 1024:
        raise ValueError("512 MiB 이상 파일은 분리하거나 CLI로 필요한 결과를 추출하세요.")
    text = data.decode("utf-8", errors="replace")
    ext = p.suffix.lower()
    if ext in (".fchk", ".fch"):
        cs = parse_fchk(text, p.name, str(p))
    elif ext in (".com", ".gjf"):
        cs = parse_input(text, p.name, str(p))
    elif ext == ".xyz":
        cs = parse_xyz(text, p.name, str(p))
    elif ext in (".sdf", ".mol", ".mol2", ".pdb", ".cif"):
        from .chemistry import read_structure

        cs = read_structure(p)
    else:
        cs = parse_log(text, p.name, str(p))
    for c in cs:
        c.source_hash = digest(data)
    return cs
