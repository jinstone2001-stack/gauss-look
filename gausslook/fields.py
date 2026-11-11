from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
from .model import BOHR_ANG, Calculation


@dataclass
class Field:
    name: str
    origin: np.ndarray
    axes: np.ndarray
    values: np.ndarray
    atoms: list
    coords: list
    source: str = ""
    field_ids: list | None = None

    def info(self):
        return {
            "name": self.name,
            "shape": list(self.values.shape),
            "origin_A": self.origin.tolist(),
            "axes_A": self.axes.tolist(),
            "minimum": float(self.values.min()),
            "maximum": float(self.values.max()),
            "field_ids": self.field_ids,
            "source": self.source,
        }


def read_cube(path):
    path = Path(path)
    with path.open(encoding="utf-8", errors="replace") as stream:
        comments = [stream.readline(), stream.readline()]
        header = stream.readline().split()
        if not all(comments) or len(header) < 4:
            raise ValueError("cube header가 불완전합니다.")
        nat = int(header[0])
        origin = np.array(list(map(float, header[1:4])))
        sizes, axes = [], []
        for _ in range(3):
            row = stream.readline().split()
            if len(row) < 4:
                raise ValueError("cube 격자 header가 불완전합니다.")
            sizes.append(int(row[0]))
            axes.append(list(map(float, row[1:4])))
        if 0 in sizes or len(set(np.sign(sizes))) != 1:
            raise ValueError("cube 축 크기는 0이 아니고 단위 부호가 같아야 합니다.")
        unit = BOHR_ANG if sizes[0] > 0 else 1.0
        axes = np.array(axes) * unit
        origin *= unit
        if not np.isfinite(axes).all() or not np.isfinite(origin).all():
            raise ValueError("cube 격자에 NaN/Inf가 있습니다.")
        if abs(np.linalg.det(axes)) < 1e-18:
            raise ValueError("cube 격자 축이 선형 종속입니다.")
        atoms, coords = [], []
        for _ in range(abs(nat)):
            row = stream.readline().split()
            if len(row) < 5:
                raise ValueError("cube 원자 레코드가 불완전합니다.")
            atoms.append(int(row[0]))
            coords.append((np.array(list(map(float, row[2:5]))) * unit).tolist())
        if not np.isfinite(coords).all():
            raise ValueError("cube 좌표에 NaN/Inf가 있습니다.")
        payload = stream.read()
    nfield = int(header[4]) if len(header) > 4 else 1
    ids = None
    if nat < 0:
        record = payload.split(None, 1)
        if not record:
            raise ValueError("cube orbital ID 레코드가 없습니다.")
        nfield = int(record[0])
        if nfield <= 0:
            raise ValueError("cube field 수는 양수여야 합니다.")
        record = record[1].split(None, nfield) if len(record) > 1 else []
        if len(record) <= nfield:
            raise ValueError("cube orbital ID/값 레코드가 불완전합니다.")
        ids = list(map(int, record[:nfield]))
        payload = record[nfield]
    if nfield <= 0:
        raise ValueError("cube field 수는 양수여야 합니다.")
    shape = tuple(abs(s) for s in sizes) + (nfield,)
    tokens = payload.replace("D", "E").replace("d", "e").split()
    expected = math.prod(shape)
    if len(tokens) != expected:
        raise ValueError(f"cube 값 개수 불일치: {len(tokens)} / {expected}")
    try:
        data = np.asarray(tokens, dtype=float)
    except ValueError as exc:
        raise ValueError("cube 숫자 데이터 형식 오류") from exc
    if not np.isfinite(data).all():
        raise ValueError("cube에 NaN/Inf가 있습니다.")
    return Field(path.name, origin, axes, data.reshape(shape), atoms, coords, str(path), ids)


def isosurface(field, level=0.03, channel=0, max_faces=80000):
    from skimage.measure import marching_cubes

    v = field.values[:, :, :, int(channel)]
    level = float(level)
    if not float(v.min()) < level < float(v.max()):
        raise ValueError(
            f"등치값 {level:g}가 데이터 범위 ({v.min():g}, {v.max():g}) 안에 없습니다."
        )
    verts, faces, normals, _ = marching_cubes(v, level=level, allow_degenerate=False)
    verts = field.origin + verts @ field.axes
    normals = normals @ np.linalg.inv(field.axes).T
    normals /= np.maximum(1e-12, np.linalg.norm(normals, axis=1))[:, None]
    # Preview face sampling is explicit; original grid is retained for export/rebuild.
    stride = max(1, int(np.ceil(len(faces) / max_faces)))
    faces = faces[::stride]
    used, inv = np.unique(faces.reshape(-1), return_inverse=True)
    return {
        "vertices": verts[used].tolist(),
        "faces": inv.reshape(-1, 3).tolist(),
        "normals": normals[used].tolist(),
        "level": level,
        "channel": channel,
        "preview_stride": stride,
        "bounds_A": [verts.min(0).tolist(), verts.max(0).tolist()],
    }


def sample(field, coords, channel=0):
    from scipy.ndimage import map_coordinates

    idx = (np.asarray(coords) - field.origin) @ np.linalg.inv(field.axes)
    return map_coordinates(
        field.values[:, :, :, int(channel)], idx.T, order=1, mode="constant", cval=np.nan
    )


def contour(field, origin, normal, size=8.0, resolution=120, channel=0):
    n = np.asarray(normal, float)
    if np.linalg.norm(n) < 1e-12:
        raise ValueError("평면 법선은 0 벡터일 수 없습니다.")
    n /= np.linalg.norm(n)
    seed = np.eye(3)[np.argmin(np.abs(n))]
    u = np.cross(n, seed)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    x = np.linspace(-size / 2, size / 2, max(10, min(350, int(resolution))))
    xx, yy = np.meshgrid(x, x)
    points = np.asarray(origin) + xx[:, :, None] * u + yy[:, :, None] * v
    z = sample(field, points.reshape(-1, 3), channel).reshape(xx.shape)
    return {
        "axis_A": x.tolist(),
        "values": z.tolist(),
        "origin_A": list(origin),
        "u": u.tolist(),
        "v": v.tolist(),
    }


def field_operation(a, operation, b=None, factor=1.0):
    if b is not None and (
        a.values.shape != b.values.shape
        or not np.allclose(a.axes, b.axes)
        or not np.allclose(a.origin, b.origin)
        or a.atoms != b.atoms
        or not np.allclose(a.coords, b.coords)
    ):
        raise ValueError(
            "cube 연산은 같은 구조·원점·격자·field 수가 필요합니다. 자동 보간하지 않습니다."
        )
    if operation == "scale":
        values = a.values * factor
    elif operation == "square":
        values = a.values**2
    elif operation == "add" and b is not None:
        values = a.values + b.values
    elif operation == "subtract" and b is not None:
        values = a.values - b.values
    else:
        raise ValueError("지원 연산: scale, square, add, subtract")
    return Field(
        a.name + " " + operation, a.origin.copy(), a.axes.copy(), values, a.atoms, a.coords
    )


def integrate(f, channel=0):
    # Cube scalar units are not described by the file format; caller must select them.
    val = float(f.values[:, :, :, channel].sum() * abs(np.linalg.det(f.axes)))
    return {
        "integral_value_times_A3": val,
        "if_density_in_e_bohr3_electrons": val / BOHR_ANG**3,
        "note": "전자수 해석은 실제 field가 e/bohr^3 밀도인지 확인한 경우에만 유효합니다. ECP/full/frozen-core 정의를 확인하세요.",
    }
