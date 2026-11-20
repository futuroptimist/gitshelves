from datetime import datetime, timezone
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
from threading import Thread
from time import monotonic
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import urlopen

import pytest


@pytest.fixture
def api(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "web"))
    return import_module("github_activity")


def item(sha, date, login="Futuroptimist"):
    return {
        "sha": sha * 40,
        "author": {"login": login},
        "commit": {"author": {"date": date}},
    }


def test_real_data_shape_maps_thirty_utc_days_without_duplicates(api):
    body = {
        "total_count": 160,
        "incomplete_results": False,
        "items": [
            item("a", "2026-10-22T23:30:00-07:00"),
            item("a", "2026-10-22T23:30:00-07:00"),
            item("b", "2026-11-02T13:00:00Z"),
            item("c", "2026-11-02T14:00:00Z", "someone-else"),
            item("d", "2027-01-01T00:00:00Z"),
        ],
    }

    def upstream(request, *, timeout):
        target = urlsplit(request.full_url)
        assert (target.scheme, target.netloc, target.path) == (
            "https",
            "api.github.com",
            "/search/commits",
        )
        assert parse_qs(target.query) == {
            "q": [
                "author:futuroptimist "
                "author-date:2026-10-22T00:00:00Z..2026-11-20T00:00:00Z"
            ],
            "sort": ["author-date"],
            "order": ["desc"],
            "per_page": ["100"],
        }
        assert request.get_header("Authorization") is None
        assert timeout == api.REQUEST_TIMEOUT
        return BytesIO(json.dumps(body).encode())

    assert api.public_activity(
        " Futuroptimist ",
        now=datetime(2026, 11, 20, tzinfo=timezone.utc),
        open_url=upstream,
    ) == {
        "username": "futuroptimist",
        "start": "2026-10-22",
        "counts": [0, 1] + [0] * 9 + [1] + [0] * 18,
        "sampled": 2,
        "limited": True,
    }


@pytest.mark.parametrize("value", ["", "a--b", "-name", "name-", "a" * 40, "a:b", "K"])
def test_rejects_invalid_login_without_fetching(api, value):
    with pytest.raises(api.ActivityError) as error:
        api.public_activity(value, open_url=lambda *_a, **_kw: pytest.fail("fetched"))
    assert error.value.status == 400


@pytest.mark.parametrize(
    "status,headers,expected",
    [(403, {"X-RateLimit-Remaining": "0"}, 429), (422, {}, 422), (502, {}, 502)],
)
def test_upstream_errors_do_not_expose_body(api, status, headers, expected):
    def upstream(request, **_kwargs):
        raise HTTPError(
            request.full_url, status, "sensitive upstream details", headers, BytesIO()
        )

    with pytest.raises(api.ActivityError) as error:
        api.public_activity("futuroptimist", open_url=upstream)
    assert error.value.status == expected
    assert "sensitive" not in str(error.value)


def test_bounds_reads_and_rejects_malformed_upstream(api, monkeypatch):
    monkeypatch.setattr(api, "READ_LIMIT", 16)
    for data in (b"x" * 40, b"not JSON", b"{}"):
        with pytest.raises(api.ActivityError) as error:
            api.public_activity(
                "futuroptimist", open_url=lambda *_a, **_k: BytesIO(data)
            )
        assert error.value.status == 502


def test_budget_rolls_over_without_identity(api):
    now = [30.0]
    budget = api.RequestBudget(limit=2, clock=lambda: now[0])
    assert budget.take()
    assert budget.take()
    assert not budget.take()
    now[0] += 60.0
    assert budget.take()


def test_http_route_is_same_origin_noncached_and_logs_no_username(
    api, monkeypatch, capsys
):
    server_module = import_module("server")
    monkeypatch.setattr(server_module, "BUDGET", api.RequestBudget())
    monkeypatch.setattr(
        server_module, "public_activity", lambda login: {"username": login}
    )
    with server_module.ThreadingHTTPServer(
        ("127.0.0.1", 0), server_module.Handler
    ) as srv:
        thread = Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{srv.server_port}{api.ACTIVITY_PATH}"
            with urlopen(url + "?username=futuroptimist", timeout=2) as response:
                assert response.headers["Cache-Control"] == "no-store"
                assert "Access-Control-Allow-Origin" not in response.headers
                assert json.load(response) == {"username": "futuroptimist"}
            with pytest.raises(HTTPError) as error:
                urlopen(url + "?username=one&username=two", timeout=2)
            assert error.value.code == 400
            error.value.close()
        finally:
            srv.shutdown()
            thread.join(timeout=2)
    log = capsys.readouterr().err
    assert api.ACTIVITY_PATH in log
    assert "?username=" not in log
    assert "futuroptimist" not in log


def test_deadline_and_truncated_body_are_generic_errors(api, monkeypatch):
    from http.client import IncompleteRead

    class Response(BytesIO):
        def read1(self, _size):
            raise IncompleteRead(b"upstream data must not escape")

    with pytest.raises(api.ActivityError) as error:
        api.public_activity("futuroptimist", open_url=lambda *_a, **_k: Response())
    assert error.value.status == 502
    assert str(error.value) == "github_unavailable"

    times = iter((1, 2, 10))
    monkeypatch.setattr(api, "monotonic", lambda: next(times))
    with pytest.raises(api.ActivityError) as error:
        api.public_activity(
            "futuroptimist", open_url=lambda *_a, **_k: BytesIO(b"truncated stream")
        )
    assert error.value.status == 502


def test_second_resolution_bounds_future_items_before_sample_limit(api):
    now = datetime.fromisoformat("2026-11-20T03:08:09.730-08:00")
    midnight = item("a", "2026-10-21T17:00:00-07:00")
    latest = item("b", "2026-11-20T03:08:09-08:00")
    too_old = item("c", "2026-10-21T23:59:59Z")
    one_second_future = item("d", "2026-11-20T11:08:10Z")

    def upstream(request, *, timeout):
        query = parse_qs(urlsplit(request.full_url).query)["q"][0]
        assert query == (
            "author:futuroptimist "
            "author-date:2026-10-22T00:00:00Z..2026-11-20T11:08:09Z"
        )
        # The provider enforces the range before its descending 100-item cap.
        # Keep a defensive check against boundary violations in the response.
        return BytesIO(
            json.dumps(
                {
                    "total_count": 2,
                    "incomplete_results": False,
                    "items": [one_second_future, latest, midnight, too_old],
                }
            ).encode()
        )

    result = api.public_activity("futuroptimist", now=now, open_url=upstream)
    assert result["sampled"] == 2
    assert result["counts"] == [1, *([0] * 28), 1]


@pytest.mark.parametrize(
    "wire_error, status",
    [("rate_limited", 429), ("search_rejected", 422), ("sensitive", 502)],
)
def test_worker_protocol_sanitizes_errors(
    api, monkeypatch, tmp_path, wire_error, status
):
    script = tmp_path / "worker.py"
    script.write_text(f'print({json.dumps(json.dumps({"error": wire_error}))})')
    monkeypatch.setattr(api, "__file__", str(script))
    with pytest.raises(api.ActivityError) as error:
        api.public_activity("futuroptimist")
    assert error.value.status == status
    assert "sensitive" not in str(error.value)


def test_worker_protocol_keeps_identity_and_clock_in_pipe(api, monkeypatch, tmp_path):
    script = tmp_path / "worker.py"
    script.write_text(
        "import json, os, sys\n"
        "assert len(sys.argv) == 1 and 'PRIVATE_CANARY' not in os.environ\n"
        "login, clock = sys.stdin.read().splitlines()\n"
        "assert clock == '2026-11-20T11:08:09.730000+00:00'\n"
        "print(json.dumps({'username': login, 'start': '2026-10-22',"
        "'counts': [0]*30, 'sampled': 0, 'limited': False}))\n"
    )
    monkeypatch.setattr(api, "__file__", str(script))
    monkeypatch.setenv("PRIVATE_CANARY", "server-only-test-value")
    result = api.public_activity(
        "Futuroptimist", now=datetime.fromisoformat("2026-11-20T03:08:09.730-08:00")
    )
    assert result == {
        "username": "futuroptimist",
        "start": "2026-10-22",
        "counts": [0] * 30,
        "sampled": 0,
        "limited": False,
    }


def test_parent_deadline_kills_and_reaps_blocked_lookup(api, monkeypatch, tmp_path):
    import os

    script = tmp_path / "worker.py"
    ready = tmp_path / "started"
    script.write_text(
        "import os, sys, time\n"
        "from pathlib import Path\n"
        "assert len(sys.argv) == 1\n"
        "assert 'PRIVATE_CANARY' not in os.environ\n"
        "assert sys.stdin.buffer.read().startswith(b'futuroptimist\\n')\n"
        f"Path({str(ready)!r}).write_text(str(os.getpid()))\n"
        "time.sleep(10)\n"
    )
    monkeypatch.setattr(api, "__file__", str(script))
    monkeypatch.setattr(api, "REQUEST_TIMEOUT", 0.75)
    monkeypatch.setenv("PRIVATE_CANARY", "server-only-test-value")
    started = monotonic()
    with pytest.raises(api.ActivityError) as error:
        api.public_activity("futuroptimist")
    assert str(error.value) == "github_unavailable"
    assert 0.65 <= monotonic() - started < 3
    pid = int(ready.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
