"""Render canonical web STL assets from repository-owned OpenSCAD entry points."""

from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web/public/models"


def render(source: Path, target: Path) -> None:
    openscad = shutil.which("openscad")
    if not openscad:
        raise SystemExit("openscad is required; install OpenSCAD and xvfb-run")
    command = [openscad, "-o", str(target), "--export-format", "binstl", str(source)]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        command = ["xvfb-run", "--auto-servernum", *command]
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> None:
    library = ROOT / "openscad/lib/gridfinity-rebuilt"
    if not library.exists():
        raise SystemExit(
            "clone pinned Gridfinity input first: scripts/fetch_gridfinity.sh"
        )
    OUT.mkdir(parents=True, exist_ok=True)
    render(ROOT / "openscad/baseplate_2x6.scad", OUT / "baseplate_2x6.stl")
    render(ROOT / "openscad/contrib_cube.scad", OUT / "contrib_cube.stl")
    for model in OUT.glob("*.stl"):
        if model.stat().st_size < 84:
            raise SystemExit(f"invalid generated STL: {model}")


if __name__ == "__main__":
    main()
