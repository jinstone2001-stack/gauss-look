import json, threading, urllib.request, urllib.error
from pathlib import Path
import numpy as np
import pytest
from gausslook.engine import Engine
from gausslook.model import Calculation, BOHR_ANG
from gausslook.parser import parse_log, parse_fchk, parse_input
from gausslook.analysis import quality, spectrum, measure, alignment, thermochemistry_correction
from gausslook.fields import read_cube, Field, isosurface, field_operation, sample, integrate
from gausslook.chemistry import gaussian_input
from gausslook.webserver import make_server

GEOM = """ Standard orientation:
 ---------------------------------------------------------------------
 Center Atomic Atomic Coordinates (Angstroms)
 Number Number Type X Y Z
 ---------------------------------------------------------------------
 1 8 0 0.000000 0.000000 0.000000
 2 1 0 0.750000 0.000000 0.500000
 3 1 0 -0.750000 0.000000 0.500000
 ---------------------------------------------------------------------
"""
LOG = (
    """ #p hf/sto-3g opt freq
 -------------------
 Charge = 0 Multiplicity = 1
"""
    + GEOM
    + """ SCF Done: E(RHF) = -74.123456789 A.U. after 8 cycles
 Maximum Force 0.000001 0.000450 YES
 RMS Force 0.000001 0.000300 YES
 Maximum Displacement 0.000001 0.001800 YES
 RMS Displacement 0.000001 0.001200 YES
 Optimization completed.
 Frequencies -- -20.000 1600.000 3600.000
 Red. masses -- 1.1 1.2 1.3
 IR Inten -- 2.0 3.0 4.0
 Raman Activ -- 5.0 6.0 7.0
 Atom AN X Y Z X Y Z X Y Z
 1 8 0.1 0 0 0 .1 0 0 0 .1
 2 1 0.1 0 0 0 .1 0 0 0 .1
 3 1 0.1 0 0 0 .1 0 0 0 .1
 Temperature 298.150 Kelvin. Pressure 1.00000 Atm.
 Zero-point correction= 0.02
 Sum of electronic and thermal Free Energies= -74.1
 Normal termination of Gaussian 16
"""
)


@pytest.fixture
def engine(tmp_path):
    e = Engine(tmp_path)
    yield e
    e.close()


def test_log_units_modes_and_convergence():
    c = parse_log(LOG, "water", "fixture")[0]
    assert len(c.atoms) == 3 and len(c.frames) == 1
    assert c.energies[-1]["hartree"] == pytest.approx(-74.123456789)
    assert len(c.modes) == 3 and len(c.modes[0]["displacements"]) == 3
    assert c.status["optimization"] == "converged"
    assert quality(c)["imaginary_count"] == 1
    assert c.thermo["gibbs"] == -74.1


def test_link1_isolation_and_absolute_provenance():
    text = LOG + "\n--Link1--\n" + LOG.replace("-74.123456789", "-80.111111111")
    cs = parse_log(text, "multi", "fixture")
    assert len(cs) == 2
    assert cs[1].energies[-1]["hartree"] == pytest.approx(-80.111111111)
    for c in cs:
        assert "SCF Done" in text.splitlines()[c.energies[-1]["line"] - 1]


def test_missing_frequency_is_unknown():
    c = Calculation("SP")
    assert quality(c)["imaginary_count"] is None


def test_truncated_log_still_usable():
    c = parse_log(LOG.split("Normal termination")[0], "partial", "fixture")[0]
    assert c.status["termination"] == "incomplete" and len(c.modes) == 3


def test_scf_failure_not_converged():
    c = parse_log(
        LOG.replace("Normal termination of Gaussian 16", "Convergence failure\nError termination"),
        "failed",
        "fixture",
    )[0]
    assert c.status["scf"] == "failed" and c.status["termination"] == "error"


def test_frequency_internal_optimizer_is_not_opt_job():
    text = (
        LOG.replace("#p hf/sto-3g opt freq", "#p hf/sto-3g freq")
        + "\nStep number 1 out of a maximum of 2\n"
    )
    c = parse_log(text, "freq", "fixture")[0]
    assert c.kind == "frequency" and c.status["optimization"] == "not_performed"


def test_raman_laser_and_temperature_change_intensity():
    c = parse_log(LOG, "water", "fixture")[0]
    a = spectrum(c, "Raman", laser_nm=532)
    b = spectrum(c, "Raman", laser_nm=785)
    assert a["sticks"][0]["y"] > b["sticks"][0]["y"] and len(a["sticks"]) == 2
    with pytest.raises(ValueError):
        spectrum(c, width=0)


def test_spectrum_peak_area():
    c = Calculation("s", modes=[{"frequency_cm1": 1000.0, "ir_km_mol": 7.0}])
    d = spectrum(c, width=20, points=4000)
    assert np.trapezoid(d["y"], d["x"]) == pytest.approx(7.0, rel=1e-3)


def test_geometry_and_degenerate_angles():
    assert measure([[0, 0, 0], [1, 0, 0]], [0, 1])["value"] == 1.0
    assert measure([[1, 0, 0], [0, 0, 0], [0, 1, 0]], [0, 1, 2])["value"] == pytest.approx(90)
    with pytest.raises(ValueError):
        measure([[0, 0, 0], [0, 0, 0], [1, 0, 0]], [0, 1, 2])


def fchk_text():
    rows = ["Fixture", "SP RHF STO-3G"]

    def scalar(k, v):
        rows.append(f"{k:<43}I   {v}")

    def array(k, v, typ="R"):
        rows.append(f"{k:<43}{typ}   N= {len(v)}")
        rows.append(" ".join(map(str, v)))

    scalar("Charge", 0)
    scalar("Multiplicity", 1)
    scalar("Number of alpha electrons", 1)
    array("Atomic numbers", [1, 1], "I")
    array("Current cartesian coordinates", [0, 0, 0, 0, 0, 1.4])
    array("Alpha Orbital Energies", [-0.5, 0.2])
    return "\n".join(rows)


def test_fchk_coordinate_and_energy_units():
    c = parse_fchk(fchk_text(), "test", "file.fchk")[0]
    assert c.frames[0]["coords"][1][2] == pytest.approx(1.4 * BOHR_ANG)
    assert c.orbitals["alpha"]["energies_eV"][0] == pytest.approx(-13.605693122994)
    assert c.status["termination"] == "unknown"


def test_fchk_incomplete_array_rejected():
    with pytest.raises(ValueError):
        parse_fchk(fchk_text().replace("N= 6", "N= 66"), "bad", "bad")


def test_input_roundtrip_and_spin_validation(engine):
    cid = engine.demo()["ids"][0]
    c = engine.get(cid)
    text = gaussian_input(c)
    new = parse_input(text, "water", "input")[0]
    assert c.atoms == new.atoms and np.allclose(c.frames[0]["coords"], new.frames[0]["coords"])
    with pytest.raises(ValueError):
        gaussian_input(c, multiplicity=2)


def test_edit_clears_calculated_results(engine):
    cid = engine.demo()["ids"][0]
    new = engine.action("edit", cid, operation="delete", indices=[2])["ids"][0]
    c = engine.get(new)
    assert len(c.atoms) == 2 and not c.modes and not c.energies and not c.orbitals


def test_project_does_not_trust_host_paths(engine):
    cid = engine.demo()["ids"][0]
    data = engine.project()
    data["calculations"][0]["source"] = "/etc/passwd"
    new = engine.load_project(data)["ids"][0]
    assert engine.get(new).source == ""


def test_root_restriction(engine, tmp_path):
    with pytest.raises(ValueError):
        engine.load(tmp_path.parent / "outside.log", restricted=True)


def test_cube_axes_channels_and_missing_values(tmp_path):
    p = tmp_path / "a.cube"
    p.write_text("demo\ndemo\n1 0 0 0\n2 1 0 0\n2 0 1 0\n2 0 0 1\n1 0 0 0 0\n0 1 2 3 4 5 6 7\n")
    f = read_cube(p)
    assert f.values.shape == (2, 2, 2, 1) and f.axes[0, 0] == pytest.approx(BOHR_ANG)
    p.write_text(p.read_text().replace("6 7", "6"))
    with pytest.raises(ValueError):
        read_cube(p)


def test_mesh_mapping_and_grid_mismatch(engine):
    fid = engine.demo()["field_id"]
    f = engine.fields[fid]
    m = isosurface(f, 0.03)
    assert len(m["faces"]) > 0 and np.isfinite(m["vertices"]).all()
    assert np.max(np.abs(sample(f, m["vertices"]) - 0.03)) < 0.003
    with pytest.raises(ValueError):
        isosurface(f, 100)
    g = Field("shift", f.origin + 1, f.axes, f.values, f.atoms, f.coords)
    with pytest.raises(ValueError):
        field_operation(f, "subtract", g)


def test_thermo_entropy_correction_preserves_original():
    c = Calculation(
        "q",
        thermo={"gibbs": -10.0, "temperature_K": 298.15, "pressure_atm": 1.0},
        modes=[{"frequency_cm1": 20.0}, {"frequency_cm1": 1000.0}],
    )
    d = thermochemistry_correction(c)
    assert d["corrected_G_hartree"] > -10 and c.thermo["gibbs"] == -10
    with pytest.raises(ValueError):
        thermochemistry_correction(c, temperature=350)


def test_rigid_alignment(engine):
    a = engine.get(engine.demo()["ids"][0])
    b = Calculation(
        "rot",
        atoms=a.atoms,
        charge=0,
        multiplicity=1,
        frames=[
            {
                "coords": (
                    np.array(a.frames[0]["coords"]) @ np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
                    + 3
                ).tolist()
            }
        ],
    )
    assert alignment(a, b)["rmsd_A"] < 1e-10


def test_web_routes_project_and_cross_origin(engine):
    server = make_server(engine, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def request(path, data=None, origin=None):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"Content-Type": "application/json", **({"Origin": origin} if origin else {})},
        )
        return json.load(urllib.request.urlopen(req))

    try:
        r = request("/api/demo", {})
        assert request("/api/calculation/" + r["ids"][0])["properties"]["demo"]
        assert request("/api/project")["version"] == 1
        with pytest.raises(urllib.error.HTTPError):
            request("/api/demo", {}, "https://external.example")
        with pytest.raises(urllib.error.HTTPError):
            request("/api/browse?path=..")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_formchk_adapter_preserves_original(engine, tmp_path):
    import os

    fixture = tmp_path / "reference.fchk"
    fixture.write_text(fchk_text())
    exe = tmp_path / "fake_formchk"
    exe.write_text(
        "#!/usr/bin/env python3\nimport shutil,sys\nshutil.copyfile("
        + repr(str(fixture))
        + ",sys.argv[2])\n"
    )
    exe.chmod(0o755)
    engine.utilities["formchk"] = str(exe)
    original = tmp_path / "original.chk"
    original.write_bytes(b"ORIGINAL BINARY CHECKPOINT")
    r = engine.convert_checkpoint(original, {"cancel": False})
    assert r["ids"] and original.read_bytes() == b"ORIGINAL BINARY CHECKPOINT"


def test_utility_failure_is_not_success(engine, tmp_path):
    exe = tmp_path / "bad_utility"
    exe.write_text('#!/usr/bin/env python3\nimport sys\nprint("utility failed")\nsys.exit(2)\n')
    exe.chmod(0o755)
    engine.utilities["formchk"] = str(exe)
    with pytest.raises(ValueError, match="utility failed"):
        engine.utility("formchk", [], {"cancel": False})


def test_compare_mismatch_does_not_rank(engine):
    a = engine.get(engine.demo()["ids"][0])
    a.energies = [{"kind": "SCF", "hartree": -10}]
    b = Calculation(
        "other", charge=1, multiplicity=2, atoms=a.atoms, energies=[{"kind": "SCF", "hartree": -11}]
    )
    bid = engine.add(b)
    rows = engine.action("compare")
    assert rows[1]["relative_kJ_mol"] is None


def test_isotope_projection_for_linear_diatomic(tmp_path):
    from gausslook.chemistry import isotope_modes

    rows = fchk_text().splitlines()
    h = np.zeros((6, 6))
    h[2, 2] = h[5, 5] = 1.0
    h[2, 5] = h[5, 2] = -1.0
    values = h[np.tril_indices(6)].tolist()
    rows += [f'{"Cartesian Force Constants":<43}R   N= {len(values)}', " ".join(map(str, values))]
    p = tmp_path / "h2.fchk"
    p.write_text("\n".join(rows))
    a = isotope_modes(p, [1, 1])
    b = isotope_modes(p, [2, 2])
    assert len(a) == 1 and b[0]["frequency_cm1"] / a[0]["frequency_cm1"] == pytest.approx(
        1 / np.sqrt(2)
    )
