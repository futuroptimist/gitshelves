from pathlib import Path

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
