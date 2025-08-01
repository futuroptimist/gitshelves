from typing import Iterable, Dict, Tuple


def blocks_for_contributions(count: int) -> int:
    """Return the number of stacked blocks for a contribution count.

    Uses a logarithmic scale where 1 block represents 1-9 contributions,
    2 blocks represent 10-99 contributions, and so on. Zero or negative
    counts yield zero blocks.
    """
    if count <= 0:
        return 0
    import math

    return int(math.log10(count)) + 1


def generate_scad(contributions: Iterable[int]) -> str:
    """Generate an OpenSCAD script for a sequence of daily contributions."""
    scad_lines = ["// Generated by gitshelves"]
    block_size = 10  # mm per block cube
    spacing = 12
    for idx, count in enumerate(contributions):
        blocks = blocks_for_contributions(count)
        for level in range(blocks):
            x = idx * spacing
            y = 0
            z = level * block_size
            scad_lines.append(f"translate([{x}, {y}, {z}]) cube({block_size});")
    return "\n".join(scad_lines)


def generate_scad_monthly(
    contributions: Dict[Tuple[int, int], int], months_per_row: int = 12
) -> str:
    """Generate an OpenSCAD script from monthly contribution counts.

    The ``contributions`` mapping uses ``(year, month)`` tuples as keys. The
    months are arranged left-to-right in rows of ``months_per_row`` slots.  Each
    slot contains a stack of blocks on a logarithmic scale, so a month with
    1‑9 contributions shows one block, 10‑99 contributions shows two blocks, and
    so on.
    """
    scad_lines = ["// Generated by gitshelves"]
    block_size = 10  # mm per block cube
    spacing = 12
    if not contributions:
        return "\n".join(scad_lines)

    first_year = min(year for year, _ in contributions)
    last_year = max(year for year, _ in contributions)
    idx = 0
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            count = contributions.get((year, month), 0)
            blocks = blocks_for_contributions(count)
            col = idx % months_per_row
            row = idx // months_per_row
            for level in range(blocks):
                x = col * spacing
                y = row * spacing
                z = level * block_size
                scad_lines.append(
                    f"translate([{x}, {y}, {z}]) cube({block_size}); // {year}-{month:02}"
                )
            idx += 1
    return "\n".join(scad_lines)


def scad_to_stl(scad_file: str, stl_file: str) -> None:
    """Convert ``scad_file`` to ``stl_file`` using the ``openscad`` CLI.

    If the current environment lacks an X display (``$DISPLAY`` is unset), the
    command is automatically wrapped in ``xvfb-run`` when available. This mirrors
    the CI configuration and prevents ``openscad`` from exiting with code ``1``
    on headless servers.
    """
    import os
    import shutil
    import subprocess

    if shutil.which("openscad") is None:
        raise FileNotFoundError("openscad not found")

    cmd = ["openscad", "-o", stl_file, scad_file]
    if "DISPLAY" not in os.environ:
        if shutil.which("xvfb-run") is None:
            raise RuntimeError("xvfb-run required for headless rendering")
        cmd = [
            "xvfb-run",
            "--auto-servernum",
            "--server-args=-screen 0 1024x768x24",
        ] + cmd

    subprocess.run(cmd, check=True)
