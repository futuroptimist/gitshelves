"""Utilities for transforming GitHub contribution metadata."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Callable, Dict, Iterable, Tuple

from .github import determine_year_range

MonthlyKey = Tuple[int, int]
DailyKey = Tuple[int, int, int]

__all__ = [
    "MonthlyKey",
    "DailyKey",
    "build_contribution_maps",
]


def _normalise_timestamp(value: str) -> datetime:
    """Return a ``datetime`` representing the date portion of ``value``."""

    return datetime.fromisoformat(value[:10])


def build_contribution_maps(
    items: Iterable[Dict],
    start_year: int | None,
    end_year: int | None,
    *,
    determine_range: Callable[
        [int | None, int | None], tuple[int, int]
    ] = determine_year_range,
) -> tuple[int, int, Dict[MonthlyKey, int], Dict[DailyKey, int]]:
    """Aggregate raw GitHub events into monthly and daily contribution maps."""

    start_year, end_year = determine_range(start_year, end_year)
    monthly = Counter()
    daily = Counter()

    for item in items:
        created_at = item.get("created_at")
        if not created_at:
            continue
        try:
            dt = _normalise_timestamp(created_at)
        except ValueError:
            continue
        monthly[(dt.year, dt.month)] += 1
        daily[(dt.year, dt.month, dt.day)] += 1

    expanded_monthly: Dict[MonthlyKey, int] = {
        (year, month): monthly.get((year, month), 0)
        for year in range(start_year, end_year + 1)
        for month in range(1, 13)
    }

    return start_year, end_year, expanded_monthly, dict(daily)
