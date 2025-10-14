from datetime import datetime

from gitshelves.core.contributions import build_contribution_maps


def test_build_contribution_maps_expands_months():
    items = [
        {"created_at": "2023-01-15T00:00:00Z"},
        {"created_at": "2023-03-01T12:34:56Z"},
    ]

    start, end, monthly, daily = build_contribution_maps(items, 2023, 2023)

    assert start == end == 2023
    assert monthly[(2023, 2)] == 0
    assert monthly[(2023, 1)] == 1
    assert monthly[(2023, 3)] == 1
    assert daily[(2023, 1, 15)] == 1
    assert daily[(2023, 3, 1)] == 1


def test_build_contribution_maps_handles_missing_timestamp():
    start, end, monthly, daily = build_contribution_maps(
        [{"created_at": None}], None, None
    )

    assert start == end == datetime.now().year
    assert daily == {}
    assert len(monthly) == 12
