"""Regressions for real format boundaries and the v1.1 analysis workflow."""

import copy
import time
from pathlib import Path
import numpy as np
import pytest
from gausslook.parser import fchk_records, parse_fchk, parse_log
from gausslook.analysis import frame_analysis, orbital_analysis, polarizability_analysis
from gausslook.model import Calculation, HARTREE_EV, BOHR_ANG
from gausslook.engine import Engine
from gausslook.help import TOPICS, help_for_label
from test_core import LOG, GEOM, fchk_text


def array(key, values, typ="R"):
    return f"\n{key:<43}{typ}   N= {len(values)}\n" + " ".join(map(str, values)) + "\n"


def scalar(key, value, typ="R"):
    return f"\n{key:<43}{typ}   {value}\n"


def test_full_title_fixed_width_spaces_five_words_four_fields():
    # N=4 means four A12 fields, not four whitespace-separated words.
    title = "A water molecule for testing".ljust(48)
    text = (
        fchk_text()
        + f'\n{"Full title":<43}C   N= 4\n'
        + title.rstrip()
        + scalar("Total Energy", -2.2)
    )
    c = parse_fchk(text, "water", "water.fchk")[0]
    assert c.properties["full_title"] == "A water molecule for testing"
    assert c.frames[0]["energy_hartree"] == -2.2


def test_fixed_width_real_numbers_touching_and_title_looks_like_record():
    text = (
        "Fixture\nSP RHF STO-3G\n"
        + f'{"Touching":<43}R   N= 2\n'
        + f"{-1.e100:16.8E}{-2.e100:16.8E}\n"
    )
    text += f'{"Full title":<43}C   N= 2\n' + "Some I 5 values".ljust(24) + "\n"
    r = fchk_records(text)
    assert (
        r["Touching"] == [-1.0e100, -2.0e100]
        and "".join(r["Full title"]).strip() == "Some I 5 values"
    )


def test_character_multiline_hollerith_logical_and_empty_arrays():
    text = (
        f'{"Route":<43}C   N= 7\n' + ("Opt Freq".ljust(60)) + "\n" + "two fields".ljust(24) + "\n"
    )
    text += f'{"Words":<43}H   N= 2\n' + "ab cd".ljust(8) + "ef".ljust(8) + "\n"
    text += f'{"Flags":<43}L   N= 4\nTFFT\n' + f'{"Empty":<43}R   N= 0\n'
    records = fchk_records("Fixture\nSP RHF STO-3G\n" + text)
    assert len(records["Route"]) == 7 and "".join(records["Route"]).startswith("Opt Freq")
    assert records["Words"] == ["ab cd   ", "ef      "]
    assert records["Flags"] == [True, False, False, True] and records["Empty"] == []


@pytest.mark.parametrize(
    "text",
    [
        f'{"Bad":<43}R   N= 4\n1 2\n' + scalar("Next", 3),
        f'{"Bad":<43}R   N= 2\n1 rubbish\n',
        f'{"Bad":<43}C   N= 6\n' + "x".ljust(60) + "\n" + scalar("Next", 3).lstrip("\n"),
        f'{"Bad":<43}L   N= 2\nTX\n',
    ],
)
def test_malformed_arrays_still_rejected(text):
    with pytest.raises(ValueError):
        fchk_records("Fixture\nSP RHF STO-3G\n" + text)


def enriched_fchk():
    return (
        fchk_text()
        + scalar("SCF Energy", -1.0)
        + scalar("MP2 Energy", -1.1)
        + scalar("Total Energy", -1.2)
        + array("Cartesian Gradient", [0.01, -0.02, 0.03, -0.01, 0.02, -0.03])
        + array("Polarizability", [3, 1, 4, 0, 0, 5])
        + array("Alpha MO coefficients", [0.1, 0.2, 0.3, 0.4])
        + scalar("Number of Normal Modes", 1, "I")
        + array("Vib-E2", [-55, 1.2, 0.03, 7, 8])
        + array("Vib-Modes", [0.1, 0, 0, -0.1, 0, 0])
    )


def test_checkpoint_total_energy_force_sign_tensor_modes():
    c = parse_fchk(enriched_fchk(), "c", "c.fchk")[0]
    d = frame_analysis(c)
    assert d["energy"]["hartree"] == -1.2 and d["energy"]["kind"] == "Total Energy"
    np.testing.assert_allclose(d["force"]["vectors_hartree_bohr"][0], [-0.01, 0.02, -0.03])
    assert d["force"]["vectors_eV_A"][0][1] == pytest.approx(0.02 * HARTREE_EV / BOHR_ANG)
    assert d["force"]["rms_component_hartree_bohr"] == pytest.approx(
        np.sqrt((0.01**2 + 0.02**2 + 0.03**2) / 3)
    )
    p = polarizability_analysis(c)["records"][0]
    assert p["mean_au"] == 4 and p["mean_A3"] == pytest.approx(4 * 0.148184711472)
    assert p["anisotropy_au"] == pytest.approx(np.sqrt(6))
    assert c.modes[0]["reference_frame"] == 0 and c.modes[0]["frequency_cm1"] == -55
    assert c.modes[0]["displacements"] == [[0.1, 0, 0], [-0.1, 0, 0]]
    assert orbital_analysis(c)["channels"]["alpha"]["has_coefficients"]


def test_restricted_open_shell_and_unrestricted_frontiers():
    text = fchk_text() + scalar("Number of beta electrons", 0, "I")
    c = parse_fchk(text, "radical", "c.fchk")[0]
    a = orbital_analysis(c)["channels"]["alpha"]
    assert a["homo"]["mo"] == 1 and a["homo"]["occupation"] == 1 and a["lumo"]["mo"] == 2
    assert a["gap_eV"] == pytest.approx(0.7 * HARTREE_EV)
    c = parse_fchk(text + array("Beta Orbital Energies", [-0.4, 0.3]), "u", "u.fchk")[0]
    a = orbital_analysis(c)["channels"]
    assert a["beta"]["homo"] is None and a["beta"]["lumo"]["mo"] == 1
    assert not a["alpha"]["homo"]["singly_occupied"]


FORCES = """ Center Atomic                   Forces (Hartrees/Bohr)
 Number Number                          X             Y             Z
 -------------------------------------------------------------------
 1 8 .01 .02 .03
 2 1 -.01 0 0
 3 1 0 -.02 -.03
 -------------------------------------------------------------------
"""


def test_log_force_per_frame_missing_is_not_carried_reference_frame():
    text = (
        LOG + FORCES + GEOM + " SCF Done: E(RHF) = -74.2 A.U.\n" + GEOM + " Frequencies -- -100.0\n"
    )
    c = parse_log(text, "history", "fixture")[0]
    assert len(c.frames) == 3 and len(c.force_records) == 1
    assert frame_analysis(c, 0)["force"]["vectors_hartree_bohr"][0] == [0.01, 0.02, 0.03]
    assert frame_analysis(c, 1)["force"] is None and frame_analysis(c, 2)["energy"] is None
    assert c.modes[0]["reference_frame"] == 0 and c.modes[-1]["reference_frame"] == 2
    assert frame_analysis(c, 1)["energy"]["hartree"] == -74.2


def test_force_rotates_input_axes_into_viewer_standard_axes():
    input_geom = GEOM.replace("Standard orientation:", "Input orientation:")
    rotated = GEOM.replace("-0.750000 0.000000 0.500000", "0.000000 -0.750000 0.500000").replace(
        "0.750000 0.000000 0.500000", "0.000000 0.750000 0.500000"
    )
    c = parse_log("#p hf/sto-3g force\n" + input_geom + rotated + FORCES, "rotated", "source")[0]
    force = frame_analysis(c)["force"]
    raw = np.array(c.force_records[0]["raw_forces_hartree_bohr"])
    # Planar structures admit a rigid rotation; test the fitted coordinates and forces together.
    assert "rotated from input axes" in force["coordinate_system"]
    np.testing.assert_allclose(
        np.linalg.norm(force["vectors_hartree_bohr"], axis=1), np.linalg.norm(raw, axis=1)
    )
    np.testing.assert_allclose(force["vectors_hartree_bohr"][0], [-0.02, 0.01, 0.03], atol=1e-12)


def test_ccd_printed_hartree_remains_final_despite_cclib_supplements(monkeypatch):
    from types import SimpleNamespace
    from cclib.parser.utils import convertor
    from cclib import parser

    final = -75.017378003
    mock = SimpleNamespace(
        mpenergies=np.array(
            [[convertor(-75.0, "hartree", "eV"), convertor(-75.01, "hartree", "eV")]]
        ),
        ccenergies=np.array([convertor(final, "hartree", "eV")]),
        moenergies=np.array([[-10.0, 2.0]]),
        homos=np.array([0]),
    )
    monkeypatch.setattr(parser, "Gaussian", lambda *a, **k: SimpleNamespace(parse=lambda: mock))
    c = parse_log(
        "Gaussian 16:\n#p CCD/STO-3G\n"
        + GEOM
        + "SCF Done: E(RHF) = -74.9\n E(CORR)= -75.017378003\n Alpha occ. eigenvalues -- -.5\n Alpha virt. eigenvalues -- .1\n",
        "ccd",
        "source",
    )[0]
    assert c.energies[-1]["kind"] == "CCD" and c.energies[-1]["hartree"] == final
    assert frame_analysis(c)["energy"]["hartree"] == final
    assert c.orbitals["alpha"]["energies_eV"][0] == pytest.approx(-0.5 * HARTREE_EV, abs=1e-12)
    # If only the supplemental parser recognized the energy, reverse its own conversion constant.
    from gausslook.parser import _cclib_enrich

    other = Calculation("fallback")
    _cclib_enrich(other, "Gaussian 16:")
    assert other.energies[-1]["hartree"] == pytest.approx(final, abs=1e-12)


def test_polar_archive_precision_response_and_absolute_line_provenance():
    text = LOG + """ Exact polarizability: 3 1 4 0 0 5
 Polarizability= 3.100000000D+00 1.200000000D+00 4.300000000D+00
                 0.000000000D+00 0.000000000D+00 5.400000000D+00
 SCF Polarizability for W= 0.05
              1              2              3
 1 6.0
 2 .1 7.0
 3 .2 .3 8.0
"""
    cs = parse_log(LOG + "\n--Link1--\n" + text, "multi", "source")
    p = polarizability_analysis(cs[1])
    assert len(p["records"]) == 3
    assert p["default_index"] == 1 and p["records"][1]["mean_au"] == pytest.approx(12.8 / 3)
    assert p["records"][2]["frequency_au"] == 0.05 and p["records"][2]["tensor_au"][0][2] == 0.2
    joined = (LOG + "\n--Link1--\n" + text).splitlines()
    assert "Polarizability=" in joined[p["records"][1]["line"] - 1]


def test_log_restricted_open_shell_electron_counts():
    c = parse_log(
        LOG
        + "\n5 alpha electrons 4 beta electrons\n Alpha occ. eigenvalues -- -1 -.8 -.6 -.4 -.2\n Alpha virt. eigenvalues -- .1 .2\n",
        "ro",
        "source",
    )[0]
    assert c.orbitals["alpha"]["occupations"] == [2, 2, 2, 2, 1, 0, 0]


def test_log_checkpoint_link_rotates_frames_modes_and_forces(tmp_path):
    e = Engine(tmp_path)
    try:
        a = parse_log(LOG + FORCES, "log", "logsource")[0]
        aid = e.add(a)
        rot = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
        b = Calculation(
            "chk",
            kind="checkpoint",
            atoms=a.atoms,
            charge=0,
            multiplicity=1,
            frames=[{"coords": (np.array(a.frames[-1]["coords"]) @ rot + 3).tolist()}],
            orbitals={
                "alpha": {"energies_eV": [-1, 1], "occupations": [2, 0], "has_coefficients": True}
            },
        )
        bid = e.add(b)
        e.checkpoints[bid] = "trusted.fchk"
        new = e.get(e.link_checkpoint(aid, bid)["ids"][0])
        np.testing.assert_allclose(new.frames[-1]["coords"], b.frames[-1]["coords"], atol=1e-12)
        np.testing.assert_allclose(
            new.modes[0]["displacements"], np.array(a.modes[0]["displacements"]) @ rot, atol=1e-12
        )
        np.testing.assert_allclose(
            new.force_records[0]["forces_hartree_bohr"],
            np.array(a.force_records[0]["forces_hartree_bohr"]) @ rot,
            atol=1e-12,
        )
        assert e.get(aid).frames == a.frames and e.get(new.id).orbitals["alpha"]["has_coefficients"]
        b.charge = 1
        with pytest.raises(ValueError):
            e.link_checkpoint(aid, bid)
        b.charge = 0
        b.frames[-1]["coords"][0][0] += 1
        with pytest.raises(ValueError):
            e.link_checkpoint(aid, bid)
    finally:
        e.close()


def test_orbital_surface_mock_utility_two_phases_cache_and_snapshot_trust(tmp_path):
    e = Engine(tmp_path)
    try:
        p = tmp_path / "source.fchk"
        p.write_text(enriched_fchk())
        cid = e.load(p)["ids"][0]
        calls = []

        def utility(name, args, task):
            calls.append((name, args))
            assert args[1] == "AMO=1" and str(args[2]) == str(p)
            cube = Path(args[3])
            grid = range(4)
            values = [(i - 1.5) / 4 for i in grid for j in grid for k in grid]
            cube.write_text(
                "mock MO\nmock MO\n2 0 0 0\n4 1 0 0\n4 0 1 0\n4 0 0 1\n1 0 0 0 0\n1 0 0 0 1.4\n"
                + " ".join(map(str, values))
            )

        e.utility = utility
        d = e.orbital_surface(cid, "alpha", 1, "coarse", 0.03, {"cancel": False})
        assert len(d["meshes"]) == 2 and sorted(m["level"] for m in d["meshes"]) == [-0.03, 0.03]
        e.orbital_surface(cid, "alpha", 1, "coarse", 0.05, {"cancel": False})
        assert len(calls) == 1
        with pytest.raises(ValueError):
            e.orbital_surface(cid, "alpha", 3, "coarse", 0.03, {"cancel": False})
        project = e.project()
        project["calculations"][0]["properties"]["formatted_checkpoint"] = "/etc/passwd"
        restored = e.load_project(project)["ids"][0]
        assert not e.detail(restored)["checkpoint_linked"]
        with pytest.raises(ValueError):
            e.orbital_surface(restored, "alpha", 1, "coarse", 0.03, {"cancel": False})
        with pytest.raises(ValueError):
            e.reload_source(restored)
    finally:
        e.close()


def test_original_chk_reload_reconverts_and_never_edits_original(tmp_path):
    e = Engine(tmp_path)
    try:
        original = tmp_path / "original.chk"
        original.write_bytes(b"unchanged")
        calls = []

        def utility(name, args, task):
            calls.append(name)
            Path(args[1]).write_text(enriched_fchk())

        e.utility = utility
        cid = e.convert_checkpoint(original, {"cancel": False})["ids"][0]
        task = e.reload_source(cid)["task"]
        for _ in range(100):
            if e.task(task)["status"] not in ("running", "queued"):
                break
            time.sleep(0.01)
        assert e.task(task)["status"] == "done" and calls == ["formchk", "formchk"]
        assert original.read_bytes() == b"unchanged"
    finally:
        e.close()


def test_shared_manual_explains_utility_buttons_and_scientific_limits():
    assert len(TOPICS) >= 17
    for label in [
        "Demo",
        "Reload source",
        "Save project",
        "XYZ",
        "Report JSON",
        "HOMO",
        "LUMO",
        "Selected MO +/-",
        "선택 MO ±표면",
    ]:
        text = help_for_label(label)
        assert "기능입니다. 자세한" not in text, label
    assert any("1 GHz" in t["body_ko"] for t in TOPICS)
