"""Helpers for emitting metadata alongside generated SCAD assets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from ..render import scad as _scad

MonthlyCounts = Dict[Tuple[int, int], int]
DailyCounts = Dict[Tuple[int, int, int], int]


def _filter_none(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Return ``mapping`` without ``None`` values for stable JSON output."""

    return {key: value for key, value in mapping.items() if value is not None}


def _monthly_payload(
    counts: MonthlyCounts,
    *,
    year: int | None = None,
    month: int | None = None,
) -> List[Dict[str, Any]]:
    """Serialise monthly contribution counts for JSON metadata."""

    items: List[Dict[str, Any]] = []
    for (count_year, count_month), count in sorted(counts.items()):
        if year is not None and count_year != year:
            continue
        if month is not None and count_month != month:
            continue
        items.append(
            {
                "year": count_year,
                "month": count_month,
                "count": count,
                "blocks": _scad.blocks_for_contributions(count),
            }
        )
    return items


def _daily_payload(
    counts: DailyCounts,
    *,
    year: int,
    month: int,
) -> List[Dict[str, Any]]:
    """Serialise daily contribution counts for JSON metadata."""

    items: List[Dict[str, Any]] = []
    for (count_year, count_month, day), count in sorted(counts.items()):
        if count_year != year or count_month != month:
            continue
        items.append(
            {
                "year": count_year,
                "month": count_month,
                "day": day,
                "count": count,
                "blocks": _scad.blocks_for_contributions(count),
            }
        )
    return items


def _zero_months(counts: MonthlyCounts) -> List[Dict[str, int]]:
    """Return metadata entries for months without contributions."""

    zeroed: List[Dict[str, int]] = []
    for (year, month), count in sorted(counts.items()):
        if count > 0:
            continue
        zeroed.append({"year": year, "month": month})
    return zeroed


@dataclass(slots=True)
class MetadataWriter:
    """Write JSON metadata files describing generated SCAD assets."""

    username: str
    start_year: int
    end_year: int
    monthly_counts: MonthlyCounts = field(repr=False)
    daily_counts: DailyCounts = field(repr=False)
    months_per_row: int
    calendar_days_per_row: int
    colors: int
    gridfinity_layouts: bool
    gridfinity_columns: int
    gridfinity_cubes: bool
    baseplate_template: str

    def _common_payload(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "year_range": {"start": self.start_year, "end": self.end_year},
            "months_per_row": self.months_per_row,
            "calendar_days_per_row": self.calendar_days_per_row,
            "colors": self.colors,
            "gridfinity": {
                "layouts": self.gridfinity_layouts,
                "columns": self.gridfinity_columns,
                "cubes": self.gridfinity_cubes,
            },
            "baseplate_template": self.baseplate_template,
        }

    def monthly_contributions(
        self, *, year: int | None = None, month: int | None = None
    ) -> List[Dict[str, Any]]:
        return _monthly_payload(self.monthly_counts, year=year, month=month)

    def daily_contributions(self, *, year: int, month: int) -> List[Dict[str, Any]]:
        return _daily_payload(self.daily_counts, year=year, month=month)

    def zero_months(self) -> List[Dict[str, int]]:
        return _zero_months(self.monthly_counts)

    def write_scad(
        self,
        scad_path: Path,
        *,
        kind: str,
        stl_path: Path | None = None,
        year: int | None = None,
        month: int | None = None,
        color_index: int | None = None,
        levels: Iterable[int] | None = None,
        monthly_contributions: List[Dict[str, Any]] | None = None,
        daily_contributions: List[Dict[str, Any]] | None = None,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """Write ``scad_path.with_suffix('.json')`` describing the asset."""

        payload: Dict[str, Any] = {
            **self._common_payload(),
            "scad": str(scad_path),
            "kind": kind,
        }
        if stl_path is not None:
            payload["stl"] = str(stl_path)
            payload["stl_generated"] = True
        else:
            payload["stl"] = None
            payload["stl_generated"] = False
        payload.update(
            _filter_none(
                {
                    "year": year,
                    "month": month,
                    "color_index": color_index,
                }
            )
        )
        if levels is not None:
            payload["levels"] = list(levels)
        if monthly_contributions is not None:
            payload["monthly_contributions"] = monthly_contributions
        if daily_contributions is not None:
            payload["daily_contributions"] = daily_contributions
        if details:
            payload["details"] = details
        if kind == "monthly":
            payload["zero_months"] = self.zero_months()

        metadata_path = scad_path.with_suffix(".json")
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {metadata_path}")

    @staticmethod
    def unlink_for(scad_path: Path) -> None:
        """Remove the metadata file associated with ``scad_path`` if present."""

        scad_path.with_suffix(".json").unlink(missing_ok=True)
