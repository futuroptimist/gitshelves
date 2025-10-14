from datetime import UTC, datetime, timezone
import pytest

import gitshelves.fetch as fetch
from gitshelves.core import github


@pytest.fixture(autouse=True)
def clear_fetch_cache():
    github._cached_fetch.cache_clear()
    yield
    github._cached_fetch.cache_clear()


def test_fetch_single_page(monkeypatch):
    called = {}

    def fake_get(url, headers=None, params=None, timeout=10):
        called["headers"] = headers
        called["params"] = params.copy()

        class Resp:
            links = {}

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def json():
                return {"items": [{"id": 1}]}

        return Resp()

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    items = fetch.fetch_user_contributions("me", start_year=2022, end_year=2022)

    assert items == [{"id": 1}]
    assert called["headers"] == {}
    assert called["params"]["page"] == 1
    assert "2022-01-01" in called["params"]["q"]
    assert "2022-12-31" in called["params"]["q"]


def test_fetch_multiple_pages_with_token(monkeypatch):
    pages = []
    headers_used = []
    queries = []

    def fake_get(url, headers=None, params=None, timeout=10):
        pages.append(params["page"])
        headers_used.append(headers)
        queries.append(params["q"])

        class Resp:
            def __init__(self, page):
                self.links = {"next": "x"} if page == 1 else {}
                self.page = page

            @staticmethod
            def raise_for_status():
                pass

            def json(self):
                return {"items": [{"page": self.page}]}

        return Resp(params["page"])

    class DummyDateTime(datetime):
        tz_used = None

        @classmethod
        def now(cls, tz=None):
            cls.tz_used = tz
            return datetime(2021, 1, 1, tzinfo=tz)

    monkeypatch.setattr(fetch, "datetime", DummyDateTime)
    monkeypatch.setattr(fetch.requests, "get", fake_get)

    items = fetch.fetch_user_contributions("me", token="T")

    assert pages == [1, 2]
    assert headers_used[0]["Authorization"] == "token T"
    assert items == [{"page": 1}, {"page": 2}]
    assert "2021-01-01" in queries[0]
    assert DummyDateTime.tz_used == timezone.utc


def test_determine_year_range_defaults(monkeypatch):
    """Defaults should fall back to the current year."""

    class DummyDateTime(datetime):
        tz_used = None

        @classmethod
        def now(cls, tz=None):
            cls.tz_used = tz
            return datetime(2022, 6, 1, tzinfo=tz)

    monkeypatch.setattr(fetch, "datetime", DummyDateTime)

    assert fetch._determine_year_range(None, None) == (2022, 2022)
    assert DummyDateTime.tz_used == timezone.utc


def test_fetch_user_contributions_env_token(monkeypatch):
    called = {}

    def fake_get(url, headers=None, params=None, timeout=10):
        called["headers"] = headers

        class Resp:
            links = {}

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def json():
                return {"items": []}

        return Resp()

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    monkeypatch.setenv("GH_TOKEN", "T")

    fetch.fetch_user_contributions("me")

    assert called["headers"]["Authorization"] == "token T"


def test_fetch_user_contributions_rejects_invalid_year_range(monkeypatch):
    """start_year must not be greater than end_year."""

    def fake_get(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("network call not expected")

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    with pytest.raises(ValueError):
        fetch.fetch_user_contributions("me", start_year=2025, end_year=2024)


def test_determine_year_range_uses_timezone(monkeypatch):
    """Uses timezone-aware datetime to determine the current year."""

    called = {}

    class DummyDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            called["tz"] = tz
            return datetime(2021, 1, 1, tzinfo=tz)

        @classmethod
        def utcnow(cls):  # pragma: no cover - should not be called
            raise AssertionError("utcnow should not be used")

    monkeypatch.setattr(fetch, "datetime", DummyDateTime)

    start, end = fetch._determine_year_range(None, None)

    assert start == end == 2021
    assert called["tz"] is UTC


def test_fetch_user_contributions_caches_responses(monkeypatch):
    calls = 0

    def fake_get(url, headers=None, params=None, timeout=10):
        nonlocal calls
        calls += 1

        class Resp:
            links = {}

            @staticmethod
            def raise_for_status():
                pass

            @staticmethod
            def json():
                return {"items": [{"id": 1}]}

        return Resp()

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    fetch.fetch_user_contributions("me", start_year=2022, end_year=2022)
    fetch.fetch_user_contributions("me", start_year=2022, end_year=2022)

    assert calls == 1
