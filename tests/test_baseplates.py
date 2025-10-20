import importlib.resources
from pathlib import Path

from gitshelves.baseplate import load_baseplate_scad

BASEPLATE_INCLUDE = "include <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>"
BASEPLATE_USE = "use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>"


def _read(path: str) -> str:
    return Path(path).read_text()


def test_package_root_exports_load_baseplate_scad():
    """README promises ``load_baseplate_scad`` at the package root."""

    from gitshelves import load_baseplate_scad as root_loader

    assert root_loader is load_baseplate_scad


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


def test_load_baseplate_scad_loads_packaged_1x12():
    """The 1×12 template should be bundled for narrow shelves."""

    expected = (
        importlib.resources.files("gitshelves.data")
        .joinpath("baseplate_1x12.scad")
        .read_text(encoding="utf-8")
    )

    assert load_baseplate_scad("baseplate_1x12.scad") == expected


def test_load_baseplate_scad_falls_back_to_repository_checkout(monkeypatch):
    def missing_files(package: str):  # pragma: no cover - defensive guard
        raise FileNotFoundError

    monkeypatch.setattr("gitshelves.baseplate.resources.files", missing_files)

    expected = _read("openscad/baseplate_2x6.scad")
    assert load_baseplate_scad() == expected


def test_load_baseplate_scad_handles_missing_package(monkeypatch):
    """Fallback path should trigger when the data package is unavailable."""

    def missing_package(package: str):
        raise ModuleNotFoundError

    monkeypatch.setattr("gitshelves.baseplate.resources.files", missing_package)

    expected = _read("openscad/baseplate_2x6.scad")
    assert load_baseplate_scad() == expected


def test_load_baseplate_scad_falls_back_when_packaged_file_missing(monkeypatch):
    """Gracefully fall back when the package exists but the file does not."""

    class MissingFileResource:
        def joinpath(self, name: str):
            assert name == "baseplate_2x6.scad"
            return self

        def read_text(self, encoding: str = "utf-8") -> str:
            raise FileNotFoundError

    monkeypatch.setattr(
        "gitshelves.baseplate.resources.files",
        lambda package: MissingFileResource(),
    )

    expected = _read("openscad/baseplate_2x6.scad")
    assert load_baseplate_scad() == expected
