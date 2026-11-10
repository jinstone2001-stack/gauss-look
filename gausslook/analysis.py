from __future__ import annotations
import math
import numpy as np
from .model import HARTREE_KJ, HARTREE_EV, BOHR_ANG

R = 8.31446261815324


def orbital_analysis(c):
    channels = {}
    for spin, o in c.orbitals.items():
        energy = o.get("energies_eV", [])
        occ = o.get("occupations", [])
        occupied = [i for i, v in enumerate(occ[: len(energy)]) if v > 1e-8]
        virtual = [i for i, v in enumerate(occ[: len(energy)]) if v <= 1e-8]
        homo = max(occupied) if occupied else None
        # LUMO is an unoccupied orbital above HOMO; unusual occupancies are retained.
        lumo = next((i for i in virtual if homo is None or i > homo), None)
        rows = []
        for i, e in enumerate(energy):
            label = ""
            if homo is not None and i <= homo:
                label = "HOMO" if i == homo else f"HOMO-{homo-i}"
            elif lumo is not None and i >= lumo:
                label = "LUMO" if i == lumo else f"LUMO+{i-lumo}"
            rows.append(
                {
                    "mo": i + 1,
                    "label": label,
                    "energy_eV": e,
                    "energy_hartree": e / HARTREE_EV,
                    "occupation": occ[i] if i < len(occ) else None,
                    "singly_occupied": bool(
                        len(c.orbitals) == 1 and i < len(occ) and abs(occ[i] - 1) < 1e-8
                    ),
                }
            )
        channels[spin] = {
            "rows": rows,
            "homo": rows[homo] if homo is not None else None,
            "lumo": rows[lumo] if lumo is not None else None,
            "gap_eV": (
                energy[lumo] - energy[homo] if homo is not None and lumo is not None else None
            ),
            "has_coefficients": o.get("has_coefficients", False),
            "representation": o.get(
                "representation", "spin orbitals" if len(c.orbitals) > 1 else "spatial orbitals"
            ),
        }
    return {
        "channels": channels,
        "note": "HOMO–LUMO gap is an orbital-energy difference, not an excitation energy or a guaranteed band gap.",
    }


def frame_analysis(c, index=-1):
    if not c.frames:
        return {"frame": None, "energy": None, "force": None}
    index = int(index)
    if index < 0:
        index += len(c.frames)
    if not 0 <= index < len(c.frames):
        raise ValueError("Frame 번호 범위를 확인하세요.")
    f = c.frames[index]
    value = f.get("energy_hartree")
    kind = f.get("energy_kind", "electronic energy")
    energy = (
        {"hartree": value, "eV": value * HARTREE_EV, "kind": kind} if value is not None else None
    )
    force = None
    ri = f.get("force_record")
    if ri is not None and 0 <= ri < len(c.force_records):
        record = c.force_records[ri]
        a = np.array(record["forces_hartree_bohr"], float)
        if a.shape == (len(c.atoms), 3):
            scale = HARTREE_EV / BOHR_ANG
            force = {
                "vectors_hartree_bohr": a.tolist(),
                "vectors_eV_A": (a * scale).tolist(),
                "norms_hartree_bohr": np.linalg.norm(a, axis=1).tolist(),
                "max_component_hartree_bohr": float(np.abs(a).max()),
                "rms_component_hartree_bohr": float(np.sqrt(np.mean(a * a))),
                "max_atom_norm_hartree_bohr": float(np.linalg.norm(a, axis=1).max()),
                "line": record.get("line"),
                "source": record.get("source"),
                "coordinate_system": record.get("coordinate_system"),
            }
    return {
        "frame": index,
        "energy": energy,
        "force": force,
        "geometry_line": f.get("line"),
        "note": "Cartesian force = -gradient. Cartesian max/RMS components are distinct from Gaussian internal-coordinate convergence criteria.",
    }


def polarizability_analysis(c):
    records = c.properties.get("polarizability_records", [])
    raw = c.properties.get("polarizability_au")
    if not records and raw is not None:
        records = [
            {
                "tensor_au": raw,
                "frequency_au": None,
                "source": "parsed polarizability",
                "orientation": "as reported",
            }
        ]
    rows = []
    for record in records:
        a = np.asarray(record["tensor_au"], float)
        if a.shape != (3, 3) or not np.isfinite(a).all():
            continue
        sym = (a + a.T) / 2
        mean = float(np.trace(sym) / 3)
        aniso = float(
            np.sqrt(
                0.5
                * (
                    (sym[0, 0] - sym[1, 1]) ** 2
                    + (sym[1, 1] - sym[2, 2]) ** 2
                    + (sym[2, 2] - sym[0, 0]) ** 2
                    + 6 * (sym[0, 1] ** 2 + sym[1, 2] ** 2 + sym[0, 2] ** 2)
                )
            )
        )
        rows.append(
            {
                **record,
                "tensor_au": a.tolist(),
                "mean_au": mean,
                "mean_A3": mean * 0.148184711472,
                "anisotropy_au": aniso,
                "eigenvalues_au": np.linalg.eigvalsh(sym).tolist(),
            }
        )
    static = [
        i
        for i, r in enumerate(rows)
        if r.get("frequency_au") is not None and abs(r["frequency_au"]) < 1e-12
    ]
    default = static[-1] if static else len(rows) - 1 if rows else None
    return {
        "records": rows,
        "default_index": default,
        "note": "Molecular polarizability. a.u.→Å³ converts polarizability volume; this is not polymer dielectric permittivity.",
    }


def quality(c):
    checks = []

    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    add(
        "계산 종료",
        c.status.get("termination", "unknown"),
        "정상 종료와 기하 수렴·정지점 종류는 별개입니다.",
    )
    add("SCF", c.status.get("scf", "unknown"), "해당 작업의 SCF 결과 레코드를 기준으로 표시합니다.")
    add("기하 최적화", c.status.get("optimization", "not_performed"), "최적화 작업에만 적용합니다.")
    fs = [m["frequency_cm1"] for m in c.modes if m.get("frequency_cm1") is not None]
    neg = [v for v in fs if v < 0]
    if not fs:
        add(
            "정지점 분류",
            "not_calculated",
            "frequency가 없습니다. imaginary 0개라는 뜻이 아닙니다.",
        )
    elif len(neg) == 0:
        add(
            "정지점 분류",
            "minimum_candidate",
            "음의 normal-mode 진동수 없음. gradient·제약·계산 조건 일치 확인 필요.",
        )
    elif len(neg) == 1:
        add(
            "정지점 분류",
            "ts_candidate",
            f"imaginary 1개 ({neg[0]:.3f} cm-1). 의도한 TS인지 모드와 양방향 IRC로 확인하세요.",
        )
    else:
        add(
            "정지점 분류",
            "higher_saddle",
            f"imaginary {len(neg)}개. 작은 음수도 자동 삭제하지 않습니다.",
        )
    if c.multiplicity is not None and "s2_before" in c.properties:
        s = (c.multiplicity - 1) / 2
        add(
            "Spin",
            "review",
            f"<S²>={c.properties['s2_before']:.5f}, S(S+1)={s*(s+1):.5f}. 방법별 해석 필요.",
        )
    add(
        "파동함수 안정성",
        "not_assessed",
        "정상 SCF 종료만으로 Stable 계산 통과를 추정하지 않습니다.",
    )
    return {
        "checks": checks,
        "imaginary_count": len(neg) if fs else None,
        "imaginary_frequencies": neg,
        "warnings": c.warnings,
    }


def capabilities(c, utilities=None):
    utilities = utilities or {}
    p = c.properties

    def entry(name, available, reason):
        return {
            "feature": name,
            "available": bool(available),
            "reason": "사용 가능" if available else reason,
        }

    return [
        entry("구조·측정", c.frames, "좌표가 필요합니다."),
        entry("에너지·수렴", c.energies, "계산 결과 로그가 필요합니다."),
        entry(
            "진동 애니메이션",
            any(len(m.get("displacements", [])) == len(c.atoms) and c.atoms for m in c.modes),
            "모드별 Cartesian 변위가 필요합니다.",
        ),
        entry("IR", any("ir_km_mol" in m for m in c.modes), "IR intensity가 필요합니다."),
        entry("Raman", any("raman_activity" in m for m in c.modes), "Raman activity가 필요합니다."),
        entry("UV-Vis", c.transitions, "여기 상태 에너지·oscillator strength가 필요합니다."),
        entry("NMR", p.get("nmr"), "NMR shielding이 필요합니다."),
        entry("MO diagram", c.orbitals, "MO 에너지·점유 데이터가 필요합니다."),
        entry(
            "cube 생성",
            utilities.get("cubegen") and c.source.lower().endswith((".fchk", ".fch")),
            "fchk 및 Gaussian cubegen 실행 환경이 필요합니다.",
        ),
        entry(
            "동위원소 재분석",
            utilities.get("freqchk") and p.get("has_hessian"),
            "Hessian을 저장한 checkpoint와 Gaussian freqchk가 필요합니다.",
        ),
        entry(
            "비조화·Vibronic·ROA 정량 표시",
            False,
            "현재 버전에서는 전용 parser가 검증되지 않았습니다. 원본 출력에서 확인하세요.",
        ),
    ]


def spectrum(
    c,
    kind="IR",
    scale=1.0,
    width=12.0,
    shape="gaussian",
    laser_nm=532.0,
    temperature=298.15,
    reference=0.0,
    points=1800,
):
    kind = kind.upper()
    scale = float(scale)
    width = float(width)
    if width <= 0 or scale <= 0 or temperature <= 0 or laser_nm <= 0:
        raise ValueError("선폭·배율·온도·레이저 파장은 양수여야 합니다.")
    sticks = []
    unit = "cm-1"
    yunit = "broadened relative intensity"
    if kind in ("IR", "RAMAN", "VCD"):
        key = {"IR": "ir_km_mol", "RAMAN": "raman_activity", "VCD": "vcd_strength"}[kind]
        for i, m in enumerate(c.modes):
            f = m["frequency_cm1"] * scale
            if f <= 0 or key not in m:
                continue
            y = float(m[key])
            if kind == "RAMAN":
                laser = 1e7 / laser_nm
                if f >= laser:
                    continue
                y *= ((laser - f) / 1e4) ** 4 / (f * (-math.expm1(-1.438776877 * f / temperature)))
            sticks.append({"x": f, "y": y, "index": i})
    elif kind in ("UV", "UV-VIS", "ECD"):
        unit = "eV"
        for i, t in enumerate(c.transitions):
            key = "oscillator_strength" if kind != "ECD" else "rotatory_strength"
            if key in t:
                sticks.append({"x": t["energy_eV"], "y": t[key], "index": i})
    elif kind == "NMR":
        unit = "ppm"
        for i, t in enumerate(c.properties.get("nmr", [])):
            sticks.append({"x": float(reference) - t["shielding_ppm"], "y": 1.0, "index": i})
    else:
        raise ValueError("지원 스펙트럼: IR, Raman, VCD, UV-Vis, ECD, NMR")
    if not sticks:
        raise ValueError(f"{kind} 생성에 필요한 강도/주파수 데이터가 없습니다.")
    xs = np.array([s["x"] for s in sticks])
    ys = np.array([s["y"] for s in sticks])
    padding = 4 * width
    x = np.linspace(
        float(xs.min() - padding), float(xs.max() + padding), max(100, min(6000, int(points)))
    )
    y = np.zeros_like(x)
    for xv, yv in zip(xs, ys):
        d = x - xv
        if shape == "lorentzian":
            y += yv * (width / 2) / np.pi / (d * d + (width / 2) ** 2)
        else:
            sigma = width / (2 * np.sqrt(2 * np.log(2)))
            y += yv * np.exp(-0.5 * (d / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
    return {
        "kind": kind,
        "x": x.tolist(),
        "y": y.tolist(),
        "sticks": sticks,
        "x_unit": unit,
        "y_unit": yunit,
        "settings": {
            "scale": scale,
            "FWHM": width,
            "shape": shape,
            "laser_nm": laser_nm,
            "temperature_K": temperature,
            "reference_ppm": reference,
        },
    }


def measure(coords, indices):
    p = np.asarray(coords, float)[list(map(int, indices))]
    if len(p) == 2:
        return {"value": float(np.linalg.norm(p[1] - p[0])), "unit": "Å"}
    if len(p) == 3:
        a, b = p[0] - p[1], p[2] - p[1]
        den = np.linalg.norm(a) * np.linalg.norm(b)
        if den < 1e-12:
            raise ValueError("0 길이 벡터의 각도는 정의되지 않습니다.")
        return {
            "value": float(np.degrees(np.arccos(np.clip(np.dot(a, b) / den, -1, 1)))),
            "unit": "degree",
        }
    if len(p) == 4:
        b0 = -(p[1] - p[0])
        b1 = p[2] - p[1]
        b2 = p[3] - p[2]
        if np.linalg.norm(b1) < 1e-12:
            raise ValueError("이면각 축 길이가 0입니다.")
        b1 /= np.linalg.norm(b1)
        v = b0 - np.dot(b0, b1) * b1
        w = b2 - np.dot(b2, b1) * b1
        if min(np.linalg.norm(v), np.linalg.norm(w)) < 1e-12:
            raise ValueError("공선 원자의 이면각은 정의되지 않습니다.")
        return {
            "value": float(np.degrees(np.arctan2(np.dot(np.cross(b1, v), w), np.dot(v, w)))),
            "unit": "degree",
        }
    raise ValueError("2~4개 원자를 선택하세요.")


def compare(calcs, energy_kind=None):
    rows = []
    for c in calcs:
        es = [e for e in c.energies if energy_kind is None or e["kind"] == energy_kind]
        e = es[-1] if es else None
        rows.append(
            {
                "name": c.name,
                "id": c.id,
                "energy_kind": e["kind"] if e else None,
                "hartree": e["hartree"] if e else None,
                "gibbs": c.thermo.get("gibbs"),
                "route": c.route,
                "charge": c.charge,
                "multiplicity": c.multiplicity,
                "formula": sorted(c.atoms),
            }
        )
    base = next((r for r in rows if r["hartree"] is not None), None)
    for r in rows:
        compatible = bool(
            base
            and r["formula"] == base["formula"]
            and r["charge"] == base["charge"]
            and r["multiplicity"] == base["multiplicity"]
            and r["route"] == base["route"]
            and r["energy_kind"] == base["energy_kind"]
        )
        r["compatible"] = compatible
        r["relative_kJ_mol"] = (
            (r["hartree"] - base["hartree"]) * HARTREE_KJ
            if compatible and r["hartree"] is not None
            else None
        )
    return rows


def thermochemistry_correction(
    c, cutoff=100.0, model="truhlar", temperature=None, concentration=None
):
    """Entropy-only low-frequency correction; original RRHO values are untouched."""
    if "gibbs" not in c.thermo:
        raise ValueError("Gaussian의 Gibbs free energy 결과가 필요합니다.")
    t = float(temperature or c.thermo.get("temperature_K", 298.15))
    reported = c.thermo.get("temperature_K")
    if reported is None or abs(t - reported) > 1e-6:
        raise ValueError(
            "이 보정은 출력 온도에서만 지원합니다. 다른 온도는 freqchk로 재분석하세요."
        )
    if cutoff <= 0:
        raise ValueError("cutoff는 양수여야 합니다.")
    h = 6.62607015e-34
    k = 1.380649e-23
    ds = 0.0

    def sho(f):
        x = 1.438776877 * f / t
        if x > 700:
            return 0.0
        return R * (x / math.expm1(x) - math.log(-math.expm1(-x)))

    for m in c.modes:
        f = m["frequency_cm1"]
        if f <= 0:
            continue
        if model == "truhlar":
            target = sho(max(f, cutoff))
        elif model == "grimme":
            mu = h / (8 * np.pi * np.pi * f * 29979245800.0)
            red = mu * 1e-44 / (mu + 1e-44)
            sfr = R * (0.5 + math.log(math.sqrt(8 * np.pi**3 * red * k * t / h**2)))
            w = 1 / (1 + (cutoff / f) ** 4)
            target = w * sho(f) + (1 - w) * sfr
        else:
            raise ValueError("model은 truhlar 또는 grimme입니다.")
        ds += target - sho(f)
    correction = -t * ds / 1000 / HARTREE_KJ
    standard = 0.0
    if concentration is not None:
        concentration = float(concentration)
        if concentration <= 0:
            raise ValueError("농도는 양수 mol/L여야 합니다.")
        pressure = c.thermo.get("pressure_atm")
        if not pressure:
            raise ValueError("원본 압력 정보가 필요합니다.")
        standard = (
            R * t * math.log(concentration * 1000 * R * t / (pressure * 101325)) / 1000 / HARTREE_KJ
        )
    return {
        "original_G_hartree": c.thermo["gibbs"],
        "corrected_G_hartree": c.thermo["gibbs"] + correction + standard,
        "entropy_change_J_mol_K": ds,
        "entropy_correction_hartree": correction,
        "standard_state_correction_hartree": standard,
        "temperature_K": t,
        "model": model,
        "cutoff_cm1": cutoff,
        "note": "엔트로피만 보정합니다. enthalpy는 원본 Gaussian 값을 유지하며 imaginary mode를 자동 수정하지 않습니다.",
    }


def alignment(a, b):
    if a.atoms != b.atoms:
        raise ValueError(
            "원소·원자 순서가 같아야 합니다. 자동 atom mapping으로 임의 변경하지 않습니다."
        )
    x = np.asarray(a.frames[-1]["coords"])
    y = np.asarray(b.frames[-1]["coords"])
    xc = x - x.mean(0)
    yc = y - y.mean(0)
    u, s, vt = np.linalg.svd(yc.T @ xc)
    d = np.linalg.det(u @ vt)
    rot = u @ np.diag([1, 1, d]) @ vt
    fitted = yc @ rot + x.mean(0)
    return {
        "rmsd_A": float(np.sqrt(np.mean(np.sum((fitted - x) ** 2, axis=1)))),
        "coords": fitted.tolist(),
        "rotation": rot.tolist(),
        "charge_match": a.charge == b.charge,
        "multiplicity_match": a.multiplicity == b.multiplicity,
    }
