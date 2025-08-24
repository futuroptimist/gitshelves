import os
from datetime import UTC, datetime
from typing import Dict, Iterable, List

import requests

GITHUB_API = "https://api.github.com/search/issues"


def _determine_year_range(
    start_year: int | None, end_year: int | None
) -> tuple[int, int]:
    """Return inclusive start and end years, validating user input."""
    end = datetime.now(UTC).year if end_year is None else end_year
    start = end if start_year is None else start_year
    if start > end:
        raise ValueError("start_year cannot be after end_year")
    return start, end


def _search_api(url: str, headers: dict, params: dict) -> Iterable[Dict]:
    """Yield items across paginated GitHub search API responses."""
    page = 1
    while True:
        resp = requests.get(
            url, headers=headers, params={**params, "page": page}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        yield from data.get("items", [])
        if "next" not in resp.links:
            break
        page += 1


def fetch_user_contributions(
    username: str,
    token: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> List[Dict]:
    """Fetch contribution data for a user using GitHub's Search API.

    Parameters can specify a range of years to query. If no range is
    provided, only the current year is fetched. When ``token`` is omitted,
    ``GH_TOKEN`` or ``GITHUB_TOKEN`` environment variables are used if set.
    """
    start, end = _determine_year_range(start_year, end_year)
    start_date = datetime(start, 1, 1)
    end_date = datetime(end, 12, 31)

    query = (
        f"author:{username} "
        f"created:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
    )
    token = token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    params = {"q": query, "per_page": 100}
    return list(_search_api(GITHUB_API, headers, params))
