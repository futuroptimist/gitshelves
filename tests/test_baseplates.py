from pathlib import Path

from gitshelves.baseplate import load_baseplate_scad

BASEPLATE_INCLUDE = "include <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>"
BASEPLATE_USE = "use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>"


def _read(path: str) -> str:
    return Path(path).read_text()


def test_baseplate_2x6_uses_library_without_extraneous_geometry():
    data = _read("openscad/baseplate_2x6.scad")
    assert BASEPLATE_USE in data
    assert BASEPLATE_INCLUDE not in data


def test_baseplate_1x12_uses_library_without_extraneous_geometry():
    data = _read("openscad/baseplate_1x12.scad")
    assert BASEPLATE_USE in data
    assert BASEPLATE_INCLUDE not in data


def test_load_baseplate_scad_prefers_packaged_resource(monkeypatch):
    captured = {}

    class DummyResource:
        def joinpath(self, name: str):
            captured["name"] = name
            return self

        def read_text(self, encoding: str = "utf-8") -> str:
            captured["encoding"] = encoding
            return "// packaged"

    def fake_files(package: str):
        assert package == "gitshelves.data"
        return DummyResource()

    monkeypatch.setattr("gitshelves.baseplate.resources.files", fake_files)

    assert load_baseplate_scad() == "// packaged"
    assert captured == {"name": "baseplate_2x6.scad", "encoding": "utf-8"}


def test_load_baseplate_scad_falls_back_to_repository_checkout(monkeypatch):
    def missing_files(package: str):  # pragma: no cover - defensive guard
        raise FileNotFoundError

    monkeypatch.setattr("gitshelves.baseplate.resources.files", missing_files)

    expected = _read("openscad/baseplate_2x6.scad")
    assert load_baseplate_scad() == expected
