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
            calc.frames
            + calc.energies
            + calc.modes
            + calc.convergence
            + calc.transitions
            + calc.force_records
        ):
            if record.get("line") is not None:
                record["line"] += offset
        for record in calc.properties.get("polarizability_records", []):
            if record.get("line") is not None:
                record["line"] += offset
        for record in calc.force_records:
            if record.get("input_geometry_line") is not None:
                record["input_geometry_line"] += offset
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
        electron_counts = re.search(r"(\d+)\s+alpha electrons\s+(\d+)\s+beta electrons", line)
        if electron_counts:
            c.properties["alpha_electrons"], c.properties["beta_electrons"] = map(
                int, electron_counts.groups()
            )
        if re.search(r"Forces\s*\(Hartrees/Bohr\)", line, re.I):
            force_rows = []
            for offset, row in enumerate(lines[i + 1 :]):
                cells = row.split()
                if len(cells) == 5 and cells[0].isdigit() and cells[1].lstrip("-").isdigit():
                    values = nums(" ".join(cells[2:]))
                    if len(values) != 3:
                        break
                    force_rows.append(values)
                elif force_rows:
                    break
                elif offset >= 4:
                    break
            if force_rows:
                c.force_records.append(
                    {
                        "forces_hartree_bohr": force_rows,
                        "line": i + 1,
                        "source": "Gaussian Cartesian force table",
                        "coordinate_system": "as printed in log",
                    }
                )
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
            (
                "CCD" if re.search(r"\bccd\b", c.route, re.I) else "CCSD",
                r"E\([Cc][Oo][Rr][Rr]\)\s*=\s*(" + FLOAT + ")",
            ),
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
                c.properties.setdefault("polarizability_records", []).append(
                    {
                        "tensor_au": c.properties["polarizability_au"],
                        "frequency_au": 0.0,
                        "line": i + 1,
                        "source": "Exact polarizability (printed precision)",
                        "orientation": "as printed",
                    }
                )
        if re.match(r"\s*Polarizability\s*=", line):
            values = nums(line.split("=", 1)[1])
            j = i + 1
            while len(values) < 6 and j < len(lines) and j < i + 4:
                if re.search(r"[A-CF-Za-cf-z]", re.sub(r"[DEde][-+]?\d+", "", lines[j])):
                    break
                values += nums(lines[j])
                j += 1
            if len(values) == 6:
                a = values
                tensor = [[a[0], a[1], a[3]], [a[1], a[2], a[4]], [a[3], a[4], a[5]]]
                c.properties["polarizability_au"] = tensor
                c.properties.setdefault("polarizability_records", []).append(
                    {
                        "tensor_au": tensor,
                        "frequency_au": 0.0,
                        "line": i + 1,
                        "source": "Gaussian polarizability archive (higher precision)",
                        "orientation": "as printed",
                    }
                )
        if "SCF Polarizability for W=" in line:
            tensor = np.zeros((3, 3))
            seen = set()
            for row in lines[i + 1 : i + 12]:
                values = nums(row)
                if values and values[0] in (1, 2, 3) and len(values) in (int(values[0]) + 1, 4):
                    k = int(values[0]) - 1
                    for col, value in enumerate(values[1:]):
                        tensor[k, col] = value
                        tensor[col, k] = value
                    seen.add(k)
                    if len(seen) == 3:
                        break
            if len(seen) == 3:
                frequency = nums(line.split("W=", 1)[1])[0]
                c.properties.setdefault("polarizability_records", []).append(
                    {
                        "tensor_au": tensor.tolist(),
                        "frequency_au": frequency,
                        "line": i + 1,
                        "source": "SCF response polarizability",
                        "orientation": "as printed",
                    }
                )
                if abs(frequency) < 1e-12:
                    c.properties["polarizability_au"] = tensor.tolist()
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
        candidates = [
            j
            for j, record in enumerate(c.force_records)
            if g["line"] <= record["line"] < end
            and len(record["forces_hartree_bohr"]) == len(g["atoms"])
        ]
        if candidates:
            c.frames[-1]["force_record"] = candidates[-1]
            record = c.force_records[candidates[-1]]
            # Gaussian Cartesian forces use input axes; the preferred viewer geometry
            # is usually standard orientation. Rotate vectors, never their magnitudes.
            inputs = [
                v
                for v in geometries
                if not v["standard"] and v["line"] <= g["line"] and v["atoms"] == g["atoms"]
            ]
            if g["standard"] and inputs:
                raw = np.asarray(inputs[-1]["coords"])
                target = np.asarray(g["coords"])
                a = raw - raw.mean(0)
                b = target - target.mean(0)
                u, _, vt = np.linalg.svd(a.T @ b)
                rotation = u @ np.diag([1, 1, np.linalg.det(u @ vt)]) @ vt
                rmsd = float(np.sqrt(np.mean(np.sum((a @ rotation - b) ** 2, axis=1))))
                if rmsd < 0.0001:
                    record["raw_forces_hartree_bohr"] = record["forces_hartree_bohr"]
                    record["forces_hartree_bohr"] = (
                        np.asarray(record["forces_hartree_bohr"]) @ rotation
                    ).tolist()
                    record["coordinate_system"] = "standard orientation (rotated from input axes)"
                    record["input_geometry_line"] = inputs[-1]["line"]
                    record["orientation_rmsd_A"] = rmsd
        if es:
            c.frames[-1]["energy_kind"] = es[-1]["kind"]
    if preferred:
        c.atoms = preferred[-1]["atoms"]
    # Canonical alpha/beta occupations for unrestricted output are one electron each.
    if "beta" in c.orbitals:
        for o in c.orbitals.values():
            o["occupations"] = [min(1, v) for v in o["occupations"]]
    _cclib_enrich(c, text)
    for mode in c.modes:
        preceding = [
            k
            for k, f in enumerate(c.frames)
            if f.get("line", 0) <= mode.get("line", len(lines) + 1)
        ]
        mode["reference_frame"] = preceding[-1] if preceding else max(0, len(c.frames) - 1)
    if (
        len(c.orbitals) == 1
        and c.properties.get("alpha_electrons") is not None
        and c.properties.get("beta_electrons") is not None
    ):
        na, nb = c.properties["alpha_electrons"], c.properties["beta_electrons"]
        o = next(iter(c.orbitals.values()))
        o["occupations"] = [
            2 if k < min(na, nb) else 1 if k < max(na, nb) else 0
            for k in range(len(o["energies_eV"]))
        ]
        o["representation"] = "spatial orbitals (restricted/open-shell as applicable)"
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
        from cclib.parser.utils import convertor

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
                if c.orbitals.get(["alpha", "beta"][i], {}).get("energies_eV"):
                    continue
                ne = int(d.homos[i]) + 1
                factor = 1 if len(d.moenergies) == 2 else 2
                c.orbitals[["alpha", "beta"][i]] = {
                    "energies_eV": ev.tolist(),
                    "occupations": [factor if k < ne else 0 for k in range(len(ev))],
                }
        if hasattr(d, "mpenergies") and not any(
            e["kind"] in ("CCD", "CCSD", "CCSD(T)", "Composite", "ONIOM", "Excited total")
            for e in c.energies
        ):
            for order, value in enumerate(d.mpenergies[-1], 2):
                kind = "MP" + str(order)
                if not any(e["kind"] == kind for e in c.energies):
                    c.energies.append(
                        {
                            "kind": kind,
                            "hartree": float(convertor(value, "eV", "hartree")),
                            "line": None,
                        }
                    )
        if (
            hasattr(d, "ccenergies")
            and len(d.ccenergies)
            and not any(e["kind"] in ("CCD", "CCSD", "CCSD(T)") for e in c.energies)
        ):
            c.energies.append(
                {
                    "kind": "CC (cclib final)",
                    "hartree": float(convertor(d.ccenergies[-1], "eV", "hartree")),
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


FCHK_HEADER = re.compile(r"^(.{40}) {3}([IRCHL])\s+(?:N=\s*(\d+)\s*|(.*))$")


def fchk_records(text):
    lines = text.splitlines()
    r = {}
    i = 2
    while i < len(lines):
        line = lines[i]
        i += 1
        m = FCHK_HEADER.match(line)
        if not m:
            continue
        key, typ, count, scalar = m.groups()
        key = key.strip()
        if count:
            n = int(count)
            v = []
            if typ in ("C", "H"):
                width, per_line = (12, 5) if typ == "C" else (8, 9)
                while len(v) < n:
                    if i >= len(lines) or FCHK_HEADER.match(lines[i]):
                        raise ValueError(f"fchk 문자열 배열이 잘렸습니다: {key}")
                    row = lines[i]
                    i += 1
                    take = min(per_line, n - len(v))
                    if row[take * width :].strip():
                        raise ValueError(f"fchk 문자열 레코드 폭 오류: {key}")
                    row = row.ljust(take * width)
                    v.extend(row[j * width : (j + 1) * width] for j in range(take))
                r[key] = v
                continue
            while len(v) < n and i < len(lines):
                if FCHK_HEADER.match(lines[i]):
                    break
                if typ in ("R", "I"):
                    tokens = lines[i].split()
                    if any(re.fullmatch(FLOAT, t) is None for t in tokens):
                        # Full-width negative E16.8 fields may touch without a space.
                        width = 16 if typ == "R" else 12
                        row = lines[i]
                        tokens = [row[j : j + width].strip() for j in range(0, len(row), width)]
                        if any(re.fullmatch(FLOAT, t) is None for t in tokens):
                            raise ValueError(f"fchk 숫자 배열 형식 오류: {key}")
                    v += nums(lines[i])
                else:
                    flags = "".join(lines[i].split()).replace(".", "").upper()
                    if any(t not in "TF" for t in flags):
                        raise ValueError(f"fchk logical 배열 형식 오류: {key}")
                    v += [t == "T" for t in flags]
                i += 1
            if len(v) != n:
                raise ValueError(f"fchk 배열 길이 불일치: {key} ({len(v)}/{n})")
            r[key] = v
        else:
            v = (
                nums(scalar or "")
                if typ in ("R", "I")
                else ([str(scalar).strip().upper() in ("T", ".TRUE.")] if typ == "L" else [scalar])
            )
            if v:
                r[key] = v[0]
    return r


def parse_fchk(text, name, source):
    r = fchk_records(text)
    c = Calculation(name, source, kind="checkpoint")
    zs = r.get("Atomic numbers", [])
    xyz = r.get("Current cartesian coordinates", r.get("Current Cartesian Coordinates", []))
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
    c.properties["formatted_checkpoint"] = source
    c.properties["checkpoint_method_header"] = text.splitlines()[1]
    for label in ["Full title", "Full Title", "Route"]:
        if label in r:
            c.properties["full_title" if label.lower() == "full title" else "checkpoint_route"] = (
                "".join(r[label]).rstrip() if isinstance(r[label], list) else r[label]
            )
    for key in ["SCF Energy", "MP2 Energy", "Cluster Energy", "Total Energy"]:
        if key in r:
            c.energies.append({"kind": key, "hartree": r[key], "line": None})
    if c.energies:
        c.frames[0].update(
            energy_hartree=c.energies[-1]["hartree"], energy_kind=c.energies[-1]["kind"]
        )
    na = int(r.get("Number of alpha electrons", 0))
    nb = int(r.get("Number of beta electrons", na))
    c.properties.update(alpha_electrons=na, beta_electrons=nb)
    for spin in ["Alpha", "Beta"]:
        if spin + " Orbital Energies" in r:
            ev = [v * HARTREE_EV for v in r[spin + " Orbital Energies"]]
            ne = int(r.get("Number of " + spin.lower() + " electrons", 0))
            factor = 1 if "Beta Orbital Energies" in r else 2
            c.orbitals[spin.lower()] = {
                "energies_eV": ev,
                "occupations": (
                    [factor if k < ne else 0 for k in range(len(ev))]
                    if factor == 1
                    else [
                        2 if k < min(na, nb) else 1 if k < max(na, nb) else 0
                        for k in range(len(ev))
                    ]
                ),
                "has_coefficients": bool(r.get(spin + " MO coefficients")),
            }
            coefficients = r.get(spin + " MO coefficients")
            nbasis = r.get("Number of basis functions")
            if (
                coefficients is not None
                and nbasis is not None
                and len(coefficients) != int(nbasis) * len(ev)
            ):
                raise ValueError(
                    f"fchk MO 계수 행렬 길이 불일치: {spin} ({len(coefficients)}/{int(nbasis)*len(ev)})"
                )
    for label, sign in [("Cartesian Gradient", -1.0), ("Cartesian Forces", 1.0)]:
        if label in r and len(r[label]) == 3 * len(zs):
            c.force_records = [
                {
                    "forces_hartree_bohr": (sign * np.asarray(r[label]).reshape(-1, 3)).tolist(),
                    "line": None,
                    "source": label + (" (force = -gradient)" if sign < 0 else ""),
                    "coordinate_system": "checkpoint standard orientation",
                }
            ]
            c.frames[0]["force_record"] = 0
            break
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
        c.properties["polarizability_records"] = [
            {
                "tensor_au": c.properties["polarizability_au"],
                "frequency_au": 0.0,
                "line": None,
                "source": "fchk Polarizability",
                "orientation": "checkpoint standard orientation",
            }
        ]
    n = int(r.get("Number of Normal Modes", r.get("Number of normal modes", 0)))
    vib = r.get("Vib-E2", [])
    disp = r.get("Vib-Modes", [])
    for k in range(n):
        m = {
            "frequency_cm1": vib[k] if k < len(vib) else None,
            "displacements": [],
            "reference_frame": 0,
        }
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
