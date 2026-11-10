from __future__ import annotations
from pathlib import Path
import numpy as np
from .model import Calculation


def from_smiles(smiles, conformers=12):
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("SMILES를 해석할 수 없습니다.")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 20261110
    ids = list(
        AllChem.EmbedMultipleConfs(mol, numConfs=max(1, min(40, int(conformers))), params=params)
    )
    if not ids:
        raise ValueError("3D conformer 생성에 실패했습니다.")
    energies = []
    method = "MMFF94"
    if AllChem.MMFFHasAllMoleculeParams(mol):
        results = AllChem.MMFFOptimizeMoleculeConfs(mol, maxIters=500)
    elif AllChem.UFFHasAllMoleculeParams(mol):
        method = "UFF"
        results = AllChem.UFFOptimizeMoleculeConfs(mol, maxIters=500)
    else:
        method = "ETKDG only"
        results = [(-1, float("inf"))] * len(ids)
    order = sorted(range(len(ids)), key=lambda k: results[k][1])
    frames = []
    for k in order:
        frames.append(
            {
                "coords": mol.GetConformer(ids[k]).GetPositions().tolist(),
                "step": len(frames) + 1,
                "forcefield_energy_kcal_mol": results[k][1] if np.isfinite(results[k][1]) else None,
                "forcefield_converged": results[k][0] == 0,
            }
        )
    c = Calculation(
        "SMILES / " + smiles,
        kind="builder",
        charge=Chem.GetFormalCharge(mol),
        multiplicity=1 + sum(a.GetNumRadicalElectrons() for a in mol.GetAtoms()),
        atoms=[a.GetAtomicNum() for a in mol.GetAtoms()],
        frames=frames,
    )
    c.properties.update(smiles=smiles, conformer_method=method)
    c.warnings.append("힘장 conformer입니다. Gaussian 에너지·DFT 최적화 결과가 아닙니다.")
    return c


def read_structure(path):
    from rdkit import Chem

    ext = path.suffix.lower()
    if ext == ".cif":
        from ase.io import read

        a = read(str(path))
        c = Calculation(
            path.name,
            str(path),
            kind="structure",
            atoms=a.numbers.tolist(),
            frames=[{"coords": a.positions.tolist(), "step": 1}],
        )
        c.properties["cell_A"] = a.cell.array.tolist()
        return [c]
    if ext == ".sdf":
        mols = [
            m
            for m in Chem.SDMolSupplier(str(path), removeHs=False, sanitize=False)
            if m is not None
        ]
    else:
        loaders = {
            ".mol": Chem.MolFromMolFile,
            ".mol2": Chem.MolFromMol2File,
            ".pdb": Chem.MolFromPDBFile,
        }
        mol = loaders[ext](str(path), removeHs=False, sanitize=False)
        mols = [mol] if mol else []
    if not mols:
        raise ValueError("구조 파일을 해석하지 못했습니다.")
    return [
        Calculation(
            f"{path.name} / {i+1}",
            str(path),
            kind="structure",
            atoms=[a.GetAtomicNum() for a in m.GetAtoms()],
            frames=[{"coords": m.GetConformer().GetPositions().tolist(), "step": 1}],
        )
        for i, m in enumerate(mols)
    ]


def gaussian_input(
    c,
    route="#p B3LYP/def2SVP Opt Freq",
    charge=None,
    multiplicity=None,
    memory="4GB",
    cores=4,
    checkpoint="molecule.chk",
    additional="",
    frame=-1,
    title="GaussLook generated structure",
):
    from .model import ELEMENTS

    q = c.charge if charge is None else int(charge)
    m = c.multiplicity if multiplicity is None else int(multiplicity)
    if q is None or m is None:
        raise ValueError("전하와 다중도를 지정하세요.")
    n = sum(c.atoms) - q
    if m < 1 or n < m - 1 or (n - (m - 1)) % 2:
        raise ValueError("전자 수와 spin multiplicity의 짝·홀수가 맞지 않습니다.")
    if not c.frames:
        raise ValueError("구조 좌표가 없습니다.")
    if not 1 <= int(cores) <= 4096:
        raise ValueError("core 수는 1~4096이어야 합니다.")
    for label, value in [("memory", memory), ("checkpoint", checkpoint), ("title", title)]:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(label + " 값을 입력하세요. / Value is required.")
        if "\n" in value or "\r" in value:
            raise ValueError(label + "에는 줄바꿈을 사용할 수 없습니다.")
    if not isinstance(route, str) or not route.strip() or "\n" in route or "\r" in route:
        raise ValueError("Route를 한 줄로 입력하세요. / Enter a one-line route.")
    if not route.lstrip().startswith("#"):
        route = "#p " + route
    geom = "\n".join(
        f"{ELEMENTS[z]} {x:.9f} {y:.9f} {v:.9f}"
        for z, (x, y, v) in zip(c.atoms, c.frames[frame]["coords"])
    )
    return f"%mem={memory}\n%nprocshared={int(cores)}\n%chk={checkpoint}\n{route}\n\n{title}\n\n{q} {m}\n{geom}\n\n{additional.rstrip()}\n\n"


def isotope_modes(path, masses):
    from scipy.linalg import null_space
    from .parser import fchk_records
    from .model import BOHR_ANG

    r = fchk_records(Path(path).read_text())
    z = r.get("Atomic numbers", [])
    n = len(z)
    masses = np.array(masses, float)
    if masses.shape != (n,) or np.any(masses <= 0):
        raise ValueError("모든 원자의 양수 동위원소 질량(amu)을 순서대로 입력하세요.")
    packed = r.get("Cartesian Force Constants", [])
    dim = 3 * n
    if len(packed) != dim * (dim + 1) // 2:
        raise ValueError("완전 Cartesian Hessian이 필요합니다.")
    h = np.zeros((dim, dim))
    h[np.tril_indices(dim)] = packed
    h = h + h.T - np.diag(np.diag(h))
    mw = np.repeat(np.sqrt(masses), 3)
    hm = h / mw[:, None] / mw[None, :]
    xyz = np.array(r["Current cartesian coordinates"]).reshape(-1, 3)
    xyz -= np.average(xyz, axis=0, weights=masses)
    vectors = []
    for axis in np.eye(3):
        vectors.append((np.tile(axis, (n, 1)) * np.sqrt(masses)[:, None]).reshape(-1))
    for axis in np.eye(3):
        vectors.append(
            (np.cross(np.tile(axis, (n, 1)), xyz) * np.sqrt(masses)[:, None]).reshape(-1)
        )
    basis = null_space(np.array(vectors), rcond=1e-8)
    ev, evec = np.linalg.eigh(basis.T @ hm @ basis)
    freq = (
        np.sign(ev)
        * np.sqrt(np.abs(ev) * 4.3597447222071e-18 / (5.29177210903e-11**2 * 1.66053906660e-27))
        / (2 * np.pi * 29979245800.0)
    )
    cart = (basis @ evec) / mw[:, None]
    cart /= np.maximum(np.linalg.norm(cart, axis=0), 1e-12)
    return [
        {"frequency_cm1": float(f), "displacements": cart[:, i].reshape(n, 3).tolist()}
        for i, f in enumerate(freq)
    ]
