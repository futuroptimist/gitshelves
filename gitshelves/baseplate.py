"""Utilities for working with bundled baseplate templates."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def load_baseplate_scad(filename: str = "baseplate_2x6.scad") -> str:
    """Return the bundled baseplate OpenSCAD template.

    The template is packaged under ``gitshelves.data``. When the package data is
    unavailable (for example, when running directly from a source checkout where
    files were pruned), the function falls back to ``openscad/<filename>``
    relative to the repository root.
    """

    try:
        return (
            resources.files("gitshelves.data")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        fallback = Path(__file__).resolve().parents[1] / "openscad" / filename
        return fallback.read_text(encoding="utf-8")
