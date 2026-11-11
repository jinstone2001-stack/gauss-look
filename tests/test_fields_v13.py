"""Cube parser regression checks for the streamed-header NumPy payload path."""

import numpy as np
import pytest
from gausslook.fields import read_cube
from gausslook.model import BOHR_ANG


def cube(tmp_path, payload, *, nat=1, sizes=(2, 2, 2), nfield=1):
    path = tmp_path / "field.cube"
    path.write_text(
        f"synthetic\nparser test\n{nat} 0.5 0 0 {nfield}\n"
        f"{sizes[0]} 1 0 0\n{sizes[1]} 0 1 0\n{sizes[2]} 0 0 1\n"
        + ("6 0 1 2 3\n" if nat else "") + payload,
        encoding="utf-8",
    )
    return path


def test_cube_payload_preserves_units_channels_and_orbital_ids(tmp_path):
    payload = "2 17\n23 " + " ".join(f"{i}D-1" for i in range(16))
    field = read_cube(cube(tmp_path, payload, nat=-1))
    assert field.field_ids == [17, 23]
    assert field.values.shape == (2, 2, 2, 2)
    np.testing.assert_allclose(field.values.ravel(), np.arange(16) / 10)
    np.testing.assert_allclose(field.axes, np.eye(3) * BOHR_ANG)
    np.testing.assert_allclose(field.origin, [0.5 * BOHR_ANG, 0, 0])
    np.testing.assert_allclose(field.coords, [[BOHR_ANG, 2 * BOHR_ANG, 3 * BOHR_ANG]])
    assert field.source.endswith("field.cube")
    angstrom = read_cube(cube(tmp_path, "0 1 2 3 4 5 6 7", sizes=(-2, -2, -2)))
    np.testing.assert_allclose(angstrom.axes, np.eye(3))


@pytest.mark.parametrize("payload", [
    "0 1 2 3 4 5 6", "0 1 2 3 4 5 6 7 8", "0 1 2 3 4 5 6 7 junk",
    "0 1 2 3 4 5 6 7x", "0 1 2 3 4 5 6 7\x00", "0 1 2 3 4 5 6 nan",
    "0 1 2 3 4 5 6 inf", "0 1 2 3 4 5 6 7.0.",
])
def test_cube_payload_rejects_malformed_missing_extra_and_nonfinite(tmp_path, payload):
    with pytest.raises(ValueError):
        read_cube(cube(tmp_path, payload))


@pytest.mark.parametrize("nat,sizes,nfield,payload", [
    (1, (0, 2, 2), 1, ""), (1, (-2, 2, 2), 1, ""), (1, (2, 2, 2), 0, ""),
    (-1, (2, 2, 2), 1, ""), (-1, (2, 2, 2), 1, "0"),
    (-1, (2, 2, 2), 1, "2 17"), (-1, (2, 2, 2), 1, "1 17.0 0 1 2 3 4 5 6 7"),
])
def test_cube_payload_rejects_invalid_dimensions_and_orbital_metadata(
    tmp_path, nat, sizes, nfield, payload
):
    with pytest.raises(ValueError):
        read_cube(cube(tmp_path, payload, nat=nat, sizes=sizes, nfield=nfield))
