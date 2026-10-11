"""Render against the real pinned library; snapshots cannot detect missing APIs.

Set GRIDFINITY_RENDER_TESTS=1 and optionally OPENSCAD to enable these tests.
The library must be checked out at the documented openscad/lib location.
"""

import os
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from gitshelves.render import scad

ROOT = Path(__file__).resolve().parents[1]


def test_library_paths_match_documented_checkout():
    assert scad.GRIDFINITY_LIBRARY_ROOT == ROOT / "openscad/lib/gridfinity-rebuilt"
    assert (
        scad.GRIDFINITY_BIN_SCAD == scad.GRIDFINITY_LIBRARY_ROOT / "src/core/bin.scad"
    )


def test_packaged_baseplates_have_explicit_hole_api():
    for name in ("baseplate_1x12.scad", "baseplate_2x6.scad"):
        for directory in ("openscad", "gitshelves/data"):
            source = (ROOT / directory / name).read_text(encoding="utf-8")
            assert (
                "use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-holes.scad>;"
                in source
            )


@pytest.mark.skipif(
    os.environ.get("GRIDFINITY_RENDER_TESTS") != "1",
    reason="Set GRIDFINITY_RENDER_TESTS=1 with the pinned library and OpenSCAD installed",
)
@pytest.mark.parametrize(
    "model", ["cube", "stack", "baseplate", "assembly", "zero", "packaged", "longplate"]
)
def test_pinned_gridfinity_exports(tmp_path, model, canonical_cube_height):
    executable = os.environ.get("OPENSCAD", "openscad")
    executable = shutil.which(executable)
    assert executable, "OpenSCAD is required for integration tests"
    assert scad.GRIDFINITY_BIN_SCAD.is_file(), "Fetch the pinned library first"
    output = tmp_path / f"{model}.stl"
    source = tmp_path / f"{model}.scad"
    if model == "baseplate":
        source = ROOT / "openscad/baseplate_2x6.scad"
    elif model in ("packaged", "longplate"):
        name = "baseplate_2x6.scad" if model == "packaged" else "baseplate_1x12.scad"
        template = (ROOT / "gitshelves/data" / name).read_text(encoding="utf-8")
        source.write_text(
            template.replace(
                "lib/gridfinity-rebuilt/", scad.GRIDFINITY_LIBRARY_ROOT.as_posix() + "/"
            ),
            encoding="utf-8",
        )
    elif model == "assembly":
        source.write_text(
            scad.generate_gridfinity_plate_scad({(2024, 12): 1}, 2024),
            encoding="utf-8",
        )
    else:
        source.write_text(
            scad.generate_contrib_cube_stack_scad(
                {"zero": 0, "cube": 1, "stack": 3}[model]
            ),
            encoding="utf-8",
        )
    command = [executable, "-o", str(output), "--export-format", "binstl", str(source)]
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        command = ["xvfb-run", "-a"] + command
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    diagnostic = result.stdout + result.stderr
    assert "WARNING:" not in diagnostic, diagnostic
    assert "ERROR:" not in diagnostic, diagnostic
    if model == "zero":
        assert "Current top level object is empty" in diagnostic
        assert not output.exists()
        return
    assert result.returncode == 0, diagnostic
    data = output.read_bytes()
    triangles = struct.unpack_from("<I", data, 80)[0]
    assert triangles > 0 and len(data) == 84 + 50 * triangles
    points = [
        struct.unpack_from("<3f", data, 84 + 50 * i + 12 + 12 * j)
        for i in range(triangles)
        for j in range(3)
    ]
    lower = [min(point[axis] for point in points) for axis in range(3)]
    upper = [max(point[axis] for point in points) for axis in range(3)]
    spans = [high - low for high, low in zip(upper, lower)]
    if model in ("cube", "stack"):
        assert spans == pytest.approx(
            [41.5, 41.5, canonical_cube_height + (14 if model == "stack" else 0)],
            abs=0.002,
        )
    elif model == "longplate":
        assert spans[:2] == pytest.approx([504, 42], abs=0.002)
    else:
        # A border-only result starts at x >= -2 and must not pass.
        # Check real grid geometry exists without approving its current placement.
        assert lower[:2] == pytest.approx([-126, -42], abs=0.002)
        if model == "assembly":
            assert upper[2] == pytest.approx(6 + canonical_cube_height, abs=0.002)
        else:
            assert spans[2] == pytest.approx(6, abs=0.002)


@pytest.fixture(scope="module")
def canonical_cube_height(tmp_path_factory):
    """Compare with the canonical model under the same renderer/tessellation."""
    executable = shutil.which(os.environ.get("OPENSCAD", "openscad"))
    assert executable
    output = tmp_path_factory.mktemp("canonical") / "cube.stl"
    command = [
        executable,
        "-o",
        str(output),
        "--export-format",
        "binstl",
        str(ROOT / "openscad/contrib_cube.scad"),
    ]
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        command = ["xvfb-run", "-a"] + command
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    diagnostic = result.stdout + result.stderr
    assert result.returncode == 0, diagnostic
    assert "WARNING:" not in diagnostic and "ERROR:" not in diagnostic, diagnostic
    data = output.read_bytes()
    triangles = struct.unpack_from("<I", data, 80)[0]
    assert triangles > 0 and len(data) == 84 + triangles * 50
    heights = [
        struct.unpack_from("<f", data, 84 + 50 * i + 20 + 12 * j)[0]
        for i in range(triangles)
        for j in range(3)
    ]
    height = max(heights) - min(heights)
    assert 10.4 < height < 10.6
    return height
