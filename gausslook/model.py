from __future__ import annotations
from dataclasses import dataclass, field, asdict
import hashlib
import math
import numpy as np

HARTREE_EV = 27.211386245988
HARTREE_KJ = 2625.4996394799
BOHR_ANG = 0.529177210903
ELEMENTS = (
    "X H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og"
).split()
RADII = {
    1: 0.31,
    6: 0.76,
    7: 0.71,
    8: 0.66,
    9: 0.57,
    14: 1.11,
    15: 1.07,
    16: 1.05,
    17: 1.02,
    35: 1.20,
    50: 1.39,
    53: 1.39,
    78: 1.36,
}
COLORS = {
    1: "#dce5ee",
    6: "#64748b",
    7: "#547bff",
    8: "#f05c69",
    9: "#53cf93",
    15: "#f3a94c",
    16: "#e6cc4d",
    17: "#53cf93",
    50: "#a0b9cf",
    78: "#b7c6dd",
}


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


@dataclass
class Calculation:
    name: str
    source: str = ""
    source_hash: str = ""
    kind: str = "unknown"
    route: str = ""
    charge: int | None = None
    multiplicity: int | None = None
    atoms: list = field(default_factory=list)
    frames: list = field(default_factory=list)
    energies: list = field(default_factory=list)
    modes: list = field(default_factory=list)
    orbitals: dict = field(default_factory=dict)
    properties: dict = field(default_factory=dict)
    thermo: dict = field(default_factory=dict)
    transitions: list = field(default_factory=list)
    convergence: list = field(default_factory=list)
    force_records: list = field(default_factory=list)
    status: dict = field(
        default_factory=lambda: {
            "termination": "unknown",
            "scf": "unknown",
            "optimization": "not_performed",
        }
    )
    warnings: list = field(default_factory=list)
    id: str = ""

    def public(self):
        return clean(asdict(self))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bonds(atoms, coords, scale=1.22):
    if not len(coords):
        return []
    xyz = np.asarray(coords, float)
    result = []
    for i in range(len(atoms)):
        d = np.linalg.norm(xyz[i + 1 :] - xyz[i], axis=1)
        for j, v in enumerate(d, i + 1):
            if (
                atoms[i] > 0
                and atoms[j] > 0
                and 0.2 < v < scale * (RADII.get(atoms[i], 1.4) + RADII.get(atoms[j], 1.4))
            ):
                result.append([i, j])
    return result


def xyz_text(calc, frame=-1, coords=None):
    xyz = coords if coords is not None else calc.frames[frame]["coords"]
    return (
        str(len(calc.atoms))
        + "\n"
        + calc.name
        + "\n"
        + "\n".join(
            f'{ELEMENTS[z] if 0<=z<len(ELEMENTS) else "X"} {x:.9f} {y:.9f} {v:.9f}'
            for z, (x, y, v) in zip(calc.atoms, xyz)
        )
        + "\n"
    )
