"""Rendering helpers for generating OpenSCAD artifacts."""

from __future__ import annotations

from .baseplate import load_baseplate_scad
from .scad import (
    BLOCK_SIZE,
    GRIDFINITY_BASEPLATE_HEIGHT,
    GRIDFINITY_BIN_SCAD,
    GRIDFINITY_LIBRARY_ROOT,
    GRIDFINITY_PITCH,
    GRIDFINITY_UNIT_HEIGHT,
    blocks_for_contributions,
    generate_contrib_cube_stack_scad,
    generate_gridfinity_plate_scad,
    generate_month_calendar_scad,
    generate_monthly_calendar_scads,
    generate_scad,
    generate_scad_monthly,
    generate_scad_monthly_levels,
    generate_zero_month_annotations,
    group_scad_levels,
    group_scad_levels_with_mapping,
    scad_to_stl,
)

__all__ = [
    "BLOCK_SIZE",
    "GRIDFINITY_BASEPLATE_HEIGHT",
    "GRIDFINITY_BIN_SCAD",
    "GRIDFINITY_LIBRARY_ROOT",
    "GRIDFINITY_PITCH",
    "GRIDFINITY_UNIT_HEIGHT",
    "blocks_for_contributions",
    "generate_contrib_cube_stack_scad",
    "generate_gridfinity_plate_scad",
    "generate_month_calendar_scad",
    "generate_monthly_calendar_scads",
    "generate_scad",
    "generate_scad_monthly",
    "generate_scad_monthly_levels",
    "generate_zero_month_annotations",
    "group_scad_levels",
    "group_scad_levels_with_mapping",
    "load_baseplate_scad",
    "scad_to_stl",
]
