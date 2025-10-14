"""Helpers for retrieving GitHub contribution data."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from functools import lru_cache
from typing import Dict, Iterable, List

import requests

GITHUB_API = "https://api.github.com/search/issues"
TOKEN_FALLBACK_ORDER = ("GH_TOKEN", "GITHUB_TOKEN")

__all__ = [
    "GITHUB_API",
    "TOKEN_FALLBACK_ORDER",
    "determine_year_range",
    "resolve_token",
    "fetch_user_contributions",
]


def determine_year_range(
    start_year: int | None, end_year: int | None
) -> tuple[int, int]:
    """Return inclusive start and end years, validating user input."""

    end = datetime.now(UTC).year if end_year is None else end_year
    start = end if start_year is None else start_year
    if start > end:
        raise ValueError("start_year cannot be after end_year")
    return start, end


def resolve_token(explicit: str | None) -> str | None:
    """Resolve an API token using the documented fallback order."""

    if explicit:
        return explicit
    for env_var in TOKEN_FALLBACK_ORDER:
        value = os.getenv(env_var)
        if value:
            return value
    return None


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


@lru_cache(maxsize=32)
def _cached_fetch(
    username: str,
    token: str | None,
    start_year: int,
    end_year: int,
) -> tuple[Dict, ...]:
    """Return cached GitHub search results for the provided parameters."""

    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    query = (
        f"author:{username} "
        f"created:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
    )
    headers = {"Authorization": f"token {token}"} if token else {}
    params = {"q": query, "per_page": 100}
    return tuple(_search_api(GITHUB_API, headers, params))


def fetch_user_contributions(
    username: str,
    token: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> List[Dict]:
    """Fetch contribution data for a user using GitHub's Search API.

    Parameters can specify a range of years to query. If no range is provided,
    only the current year is fetched. When ``token`` is omitted the fallback
    order is explicit ``--token`` value, ``GH_TOKEN``, then ``GITHUB_TOKEN``.
    Results are cached in-memory for the lifetime of the process.
    """

    start, end = determine_year_range(start_year, end_year)
    resolved_token = resolve_token(token)
    return [item.copy() for item in _cached_fetch(username, resolved_token, start, end)]


# Backwards compatibility for legacy imports.
_determine_year_range = determine_year_range
