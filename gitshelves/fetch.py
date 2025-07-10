import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict

GITHUB_API = "https://api.github.com/search/issues"


def fetch_user_contributions(username: str, token: str = None) -> List[Dict]:
    """Fetch contribution data for a user using GitHub's Search API.

    The search API is used to gather issues and pull requests created by the
    specified user within the last year. Results are returned as a list of
    dictionaries containing the created date.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    query = f"author:{username} created:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
    url = GITHUB_API
    headers = {}
    if token:
        headers['Authorization'] = f"token {token}"
    params = {'q': query, 'per_page': 100}
    items = []
    page = 1
    while True:
        params['page'] = page
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get('items', []))
        if 'next' not in resp.links:
            break
        page += 1
    return items
