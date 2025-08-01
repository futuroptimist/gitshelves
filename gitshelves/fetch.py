import os
import requests
from datetime import datetime
from typing import List, Dict

GITHUB_API = "https://api.github.com/search/issues"


def fetch_user_contributions(
    username: str,
    token: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> List[Dict]:
    """Fetch contribution data for a user using GitHub's Search API.

    Parameters can specify a range of years to query. If no range is
    provided, only the current year is fetched.
    """
    end = datetime.utcnow().year if end_year is None else end_year
    start = end if start_year is None else start_year
    start_date = datetime(start, 1, 1)
    end_date = datetime(end, 12, 31)
    query = f"author:{username} created:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
    url = GITHUB_API
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    params = {"q": query, "per_page": 100}
    items = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("items", []))
        if "next" not in resp.links:
            break
        page += 1
    return items
