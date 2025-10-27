"""Utilities for working with bundled baseplate templates."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def load_baseplate_scad(filename: str = "baseplate_2x6.scad") -> str:
    """Return the bundled baseplate OpenSCAD template.

    The template is packaged under ``gitshelves.data``. When the package (or the
    specific file within it) is unavailable—for example, in source checkouts
    where package data was pruned—the function falls back to
    ``openscad/<filename>`` relative to the repository root.
    """

    try:
        package_root = resources.files("gitshelves.data")
    except (FileNotFoundError, ModuleNotFoundError):
        package_root = None

    if package_root is not None:
        try:
            return package_root.joinpath(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass

    fallback = Path(__file__).resolve().parents[2] / "openscad" / filename
    return fallback.read_text(encoding="utf-8")


__all__ = ["load_baseplate_scad", "resources"]
