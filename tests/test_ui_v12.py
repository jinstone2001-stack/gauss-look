"""Backend contracts used by both v1.2 input and folder interfaces."""

import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pytest

from gausslook.chemistry import gaussian_input
from gausslook.engine import Engine
from gausslook.parser import parse_input
from gausslook.webserver import make_server


@pytest.fixture
def engine(tmp_path):
    value = Engine(tmp_path)
    yield value
    value.close()


@pytest.fixture
def browse(engine):
    server = make_server(engine, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path=""):
        query = urllib.parse.urlencode({"path": str(path)})
        with urllib.request.urlopen(
            f"http://127.0.0.1:{server.server_port}/api/browse?{query}"
        ) as response:
            return json.load(response)

    yield request
    server.shutdown()
    server.server_close()
    thread.join()


def test_browse_pasted_unicode_and_space_paths(engine, browse):
    folder = engine.root / "계산 결과" / "nested folder"
    folder.mkdir(parents=True)
    (folder / "sample.log").write_text("fixture", encoding="utf-8")
    relative = folder.relative_to(engine.root)
    data = browse(relative)
    assert data == browse(folder)
    assert data["path"] == str(relative)
    assert Path(data["absolute_path"]) == folder
    assert Path(data["root"]) == engine.root
    assert data["parent"] == str(relative.parent)
    assert data["entries"] == [
        {
            "name": "sample.log",
            "directory": False,
            "path": str(relative / "sample.log"),
            "size": 7,
        }
    ]


def test_browse_parent_and_root_contract(engine, browse):
    folder = engine.root / "child"
    folder.mkdir()
    root = browse()
    assert root["path"] == "."
    assert root["parent"] is None
    assert root["truncated"] is False
    assert browse("child")["parent"] == "."
    assert browse("child/..")["absolute_path"] == root["absolute_path"]


@pytest.mark.parametrize("path", ["missing directory", "sample.log", ".."])
def test_browse_rejects_missing_file_and_root_escape(engine, browse, path):
    (engine.root / "sample.log").write_text("fixture", encoding="utf-8")
    with pytest.raises(urllib.error.HTTPError) as error:
        browse(path)
    assert error.value.code == 400
    assert json.load(error.value)["error"]


def test_browse_rejects_absolute_root_escape(engine, browse):
    with pytest.raises(urllib.error.HTTPError) as error:
        browse(engine.root.parent)
    assert error.value.code == 400


def test_input_title_link0_and_selected_frame_roundtrip(engine):
    calculation = engine.get(engine.demo()["ids"][0])
    shifted = np.asarray(calculation.frames[0]["coords"]) + [1.25, -2.5, 0.75]
    calculation.frames.append({"coords": shifted.tolist(), "step": 2})
    text = gaussian_input(
        calculation,
        route="PBE0/def2SVP Opt Freq",
        title="Selected geometry",
        memory="8GB",
        cores=12,
        checkpoint="selected frame.chk",
        frame=1,
        additional="C H O 0\ndef2SVP\n****",
    )
    assert text.startswith("%mem=8GB\n%nprocshared=12\n%chk=selected frame.chk\n#p PBE0/def2SVP Opt Freq\n")
    assert "\n\nSelected geometry\n\n0 1\n" in text
    assert text.endswith("C H O 0\ndef2SVP\n****\n\n")
    parsed = parse_input(text, "selected.gjf", "input")[0]
    assert parsed.atoms == calculation.atoms
    assert np.allclose(parsed.frames[0]["coords"], shifted)
    first = parse_input(gaussian_input(calculation, frame=0), "first.gjf", "input")[0]
    assert np.allclose(first.frames[0]["coords"], calculation.frames[0]["coords"])


@pytest.mark.parametrize(
    "values",
    [
        {"title": "first\nsecond"},
        {"title": "first\rsecond"},
        {"title": ""},
        {"memory": "4GB\n%nprocshared=99"},
        {"checkpoint": "test.chk\r# HF/STO-3G"},
        {"route": "HF/STO-3G\n\ninjected title"},
        {"route": "HF/STO-3G\rOpt"},
        {"route": " "},
        {"multiplicity": 99},
    ],
)
def test_input_rejects_invalid_form_values(engine, values):
    calculation = engine.get(engine.demo()["ids"][0])
    with pytest.raises(ValueError):
        gaussian_input(calculation, **values)


def test_numeric_title_remains_a_title_on_input_roundtrip(engine):
    calculation = engine.get(engine.demo()["ids"][0])
    parsed = parse_input(gaussian_input(calculation, title="0 1"), "numeric title", "fixture")[0]
    assert parsed.charge == calculation.charge
    assert parsed.multiplicity == calculation.multiplicity
    assert parsed.atoms == calculation.atoms
    assert np.allclose(parsed.frames[0]["coords"], calculation.frames[0]["coords"])
