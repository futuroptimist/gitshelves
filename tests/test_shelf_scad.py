import pathlib


def test_countersink_faces_front():
    scad = pathlib.Path("openscad/shelf.scad").read_text().splitlines()
    assert any(
        "depth - head_depth" in line for line in scad
    ), "countersink should be offset from front face"
