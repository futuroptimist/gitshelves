import pytest

from gitshelves import scad as scad_module


@pytest.fixture
def gridfinity_library(monkeypatch, tmp_path):
    """Provide temporary Gridfinity library files for tests."""

    baseplate = tmp_path / "gridfinity-rebuilt-baseplate.scad"
    bin_file = tmp_path / "gridfinity-rebuilt-bin.scad"
    baseplate.write_text("// gridfinity baseplate")
    bin_file.write_text("// gridfinity bin")
    monkeypatch.setattr(
        scad_module, "GRIDFINITY_BASEPLATE_SCAD", baseplate, raising=False
    )
    monkeypatch.setattr(scad_module, "GRIDFINITY_BIN_SCAD", bin_file, raising=False)
    yield
