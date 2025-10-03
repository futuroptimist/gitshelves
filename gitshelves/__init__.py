"""Utilities for generating 3D printable GitHub contribution charts."""

from importlib import metadata

from .scad import (
    generate_scad,
    generate_scad_monthly,
    generate_month_calendar_scad,
    generate_monthly_calendar_scads,
    blocks_for_contributions,
    generate_gridfinity_plate_scad,
)
from .fetch import fetch_user_contributions

try:  # pragma: no cover - handled in package distribution
    __version__ = metadata.version("gitshelves")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "generate_scad",
    "generate_scad_monthly",
    "generate_month_calendar_scad",
    "generate_monthly_calendar_scads",
    "blocks_for_contributions",
    "generate_gridfinity_plate_scad",
    "fetch_user_contributions",
    "__version__",
]
