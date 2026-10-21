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


def test_packaged_2x6_matches_canonical_source():
    assert (ROOT / "openscad/baseplate_2x6.scad").read_bytes() == (
        ROOT / "gitshelves/data/baseplate_2x6.scad"
    ).read_bytes()


def _assert_real_grid(points, columns=6, rows=2):
    """Require interior plate vertices in every cell, not just an outer ring.

    Bins start at Z=6 and cannot satisfy this plate-only check. Ring vertices
    lie on the outer plate boundary, outside the strict cell interiors.
    """
    for row in range(rows):
        for col in range(columns):
            x = (2 * col - columns + 1) * 21
            y = (2 * row - rows + 1) * 21
            assert any(
                abs(px - x) < 20.9 and abs(py - y) < 20.9 and 0 <= pz <= 5.002
                for px, py, pz in points
            ), f"Missing interior baseplate geometry in cell ({col}, {row})"


def test_grid_guard_rejects_correctly_sized_border_only():
    points = [
        (x, y, z)
        for width, depth in [(128, 44), (126, 42)]
        for x in [-width, width]
        for y in [-depth, depth]
        for z in [0, 6]
    ]
    with pytest.raises(AssertionError, match="Missing interior baseplate geometry"):
        _assert_real_grid(points)


def _render_command(executable, output, source):
    command = [executable, "-o", str(output), "--export-format", "binstl", str(source)]
    if (
        os.name != "nt"
        and not os.environ.get("DISPLAY")
        and os.environ.get("QT_QPA_PLATFORM") != "offscreen"
    ):
        command = ["xvfb-run", "-a"] + command
    return command


@pytest.mark.skipif(
    os.environ.get("GRIDFINITY_RENDER_TESTS") != "1",
    reason="Set GRIDFINITY_RENDER_TESTS=1 with the pinned library and OpenSCAD installed",
)
@pytest.mark.parametrize(
    "model",
    [
        "cube",
        "stack",
        "baseplate",
        "assembly",
        "assembly_first",
        "assembly_full",
        "assembly_empty",
        "assembly_custom",
        "zero",
        "packaged",
        "longplate",
    ],
)
def test_pinned_gridfinity_exports(tmp_path, model, canonical_cube_mesh):
    canonical_cube_height, canonical_signature = canonical_cube_mesh
    executable = os.environ.get("OPENSCAD", "openscad")
    executable = shutil.which(executable)
    assert executable, "OpenSCAD is required for integration tests"
    assert scad.GRIDFINITY_BIN_SCAD.is_file(), "Fetch the pinned library first"
    output = tmp_path / f"{model}.stl"
    source = tmp_path / f"{model}.scad"
    columns, rows = (5, 3) if model == "assembly_custom" else (6, 2)
    occupied_months = {
        "assembly": [12],
        "assembly_first": [1],
        "assembly_full": list(range(1, 13)),
        "assembly_empty": [],
        "assembly_custom": [1, 12],
    }.get(model, [])
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
    elif model.startswith("assembly"):
        source.write_text(
            scad.generate_gridfinity_plate_scad(
                {(2024, month): 1 for month in occupied_months}, 2024, columns=columns
            ),
            encoding="utf-8",
        )
    else:
        source.write_text(
            scad.generate_contrib_cube_stack_scad(
                {"zero": 0, "cube": 1, "stack": 3}[model]
            ),
            encoding="utf-8",
        )
    command = _render_command(executable, output, source)
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
    if model == "cube":
        assert _triangle_signature(data) == canonical_signature
    if model in ("cube", "stack"):
        assert spans == pytest.approx(
            [41.5, 41.5, canonical_cube_height + (14 if model == "stack" else 0)],
            abs=0.002,
        )
    elif model == "longplate":
        assert spans[:2] == pytest.approx([504, 42], abs=0.002)
    else:
        _assert_real_grid(points, columns, rows)
        assert lower[2] == pytest.approx(0, abs=0.002)
        if model.startswith("assembly"):
            # Generated layouts have a bare plate, not the static border ring.
            assert lower[:2] == pytest.approx([-columns * 21, -rows * 21], abs=0.002)
            assert upper[:2] == pytest.approx([columns * 21, rows * 21], abs=0.002)
            expected_height = 6 + canonical_cube_height if occupied_months else 5
            assert upper[2] == pytest.approx(expected_height, abs=0.002)
            for month in occupied_months:
                x = (2 * ((month - 1) % columns) - columns + 1) * 21
                y = (2 * ((month - 1) // columns) - rows + 1) * 21
                bin_points = [
                    point
                    for point in points
                    if point[2] >= 6
                    and abs(point[0] - x) < 21
                    and abs(point[1] - y) < 21
                ]
                assert bin_points, f"Missing bin for month {month}"
                for axis, center in enumerate([x, y]):
                    assert min(p[axis] for p in bin_points) == pytest.approx(
                        center - 20.75, abs=0.002
                    )
                    assert max(p[axis] for p in bin_points) == pytest.approx(
                        center + 20.75, abs=0.002
                    )
        else:
            assert lower == pytest.approx([-128, -44, 0], abs=0.002)
            assert upper == pytest.approx([128, 44, 6], abs=0.002)
            assert spans == pytest.approx([256, 88, 6], abs=0.002)


@pytest.fixture(scope="module")
def canonical_cube_mesh(tmp_path_factory):
    """Compare with the canonical model under the same renderer/tessellation."""
    executable = shutil.which(os.environ.get("OPENSCAD", "openscad"))
    assert executable
    output = tmp_path_factory.mktemp("canonical") / "cube.stl"
    command = _render_command(executable, output, ROOT / "openscad/contrib_cube.scad")
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
    return height, _triangle_signature(data)


def _triangle_signature(data):
    """Ignore STL header/facet ordering while preserving every mesh triangle."""
    triangles = []
    for offset in range(84, len(data), 50):
        vertices = [
            tuple(
                round(value, 5)
                for value in struct.unpack_from("<3f", data, offset + 12 + 12 * vertex)
            )
            for vertex in range(3)
        ]
        triangles.append(tuple(sorted(vertices)))
    return sorted(triangles)
