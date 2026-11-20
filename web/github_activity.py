"""Bounded public GitHub commit sample for the web preview."""

from collections import deque
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
import json
import re
import subprocess
import sys
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

SEARCH_URL = "https://api.github.com/search/commits"
ACTIVITY_PATH = "/api/github-activity"
DAYS = 30
SAMPLE_LIMIT = 100
READ_LIMIT = 5 * 1024 * 1024
REQUEST_TIMEOUT = 8
READ_CHUNK = 64 * 1024
LOGIN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII | re.IGNORECASE)
SHA = re.compile(r"[a-f0-9]{40}", re.ASCII)


class ActivityError(Exception):
    """A public, generic error. Never put upstream response bodies here."""

    def __init__(self, status, code):
        super().__init__(code)
        self.status = status
        self.code = code


class NoRedirect(HTTPRedirectHandler):
    """Only the configured GitHub origin is allowed to receive requests."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RequestBudget:
    """A capped, in-memory process budget with no identifiers or payloads."""

    def __init__(self, limit=8, clock=monotonic):
        self.limit = limit
        self.clock = clock
        self.requests = deque()
        self.lock = Lock()

    def take(self):
        with self.lock:
            now = self.clock()
            while self.requests and self.requests[0] <= now - 60:
                self.requests.popleft()
            if len(self.requests) >= self.limit:
                return False
            self.requests.append(now)
            return True


def normalize_login(value):
    login = value.strip()
    if len(login) > 39 or not LOGIN.fullmatch(login):
        raise ActivityError(400, "invalid_username")
    return login.lower()


def utc_seconds(instant):
    return instant.isoformat(timespec="seconds").replace("+00:00", "Z")


def search_request(login, now):
    start = (now - timedelta(days=DAYS - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    interval = f"{utc_seconds(start)}..{utc_seconds(now)}"
    # Only a validated username can enter the fixed search qualifier.
    query = urlencode(
        {
            "q": f"author:{login} author-date:{interval}",
            "sort": "author-date",
            "order": "desc",
            "per_page": SAMPLE_LIMIT,
        }
    )
    return Request(
        f"{SEARCH_URL}?{query}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Gitshelves-public-commit-preview",
        },
    )


def read_search(request, open_url):
    deadline = monotonic() + REQUEST_TIMEOUT
    payload = bytearray()
    try:
        with open_url(request, timeout=REQUEST_TIMEOUT) as response:
            while len(payload) <= READ_LIMIT:
                if monotonic() >= deadline:
                    raise ActivityError(502, "github_unavailable")
                chunk = response.read1(min(READ_CHUNK, READ_LIMIT + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
            if monotonic() >= deadline:
                raise ActivityError(502, "github_unavailable")
    except HTTPError as error:
        try:
            status = error.code
            headers = error.headers
        finally:
            error.close()
        if status == 429 or (
            status == 403
            and (
                headers.get("X-RateLimit-Remaining") == "0"
                or headers.get("Retry-After")
            )
        ):
            raise ActivityError(429, "rate_limited") from None
        if status == 422:
            raise ActivityError(422, "search_rejected") from None
        raise ActivityError(502, "github_unavailable") from None
    except (URLError, OSError, HTTPException):
        raise ActivityError(502, "github_unavailable") from None
    if len(payload) > READ_LIMIT:
        raise ActivityError(502, "github_unavailable")
    try:
        return json.loads(payload)
    except (UnicodeError, ValueError, RecursionError):
        raise ActivityError(502, "github_unavailable") from None


def summarize(data, login, now):
    start = now.date() - timedelta(days=DAYS - 1)
    counts = [0] * DAYS
    seen = set()
    try:
        items = data["items"]
        total = data["total_count"]
        incomplete = data["incomplete_results"]
        if (
            not isinstance(items, list)
            or len(items) > SAMPLE_LIMIT
            or type(total) is not int
            or total < 0
            or type(incomplete) is not bool
        ):
            raise ValueError
        for item in items:
            author = item.get("author")
            if not author or author["login"].lower() != login:
                # Never attribute unavailable or unrelated authors to this search.
                continue
            sha = item["sha"]
            date = datetime.fromisoformat(item["commit"]["author"]["date"])
            if not SHA.fullmatch(sha) or date.utcoffset() is None:
                raise ValueError
            date = date.astimezone(timezone.utc)
            offset = (date.date() - start).days
            if sha not in seen and 0 <= offset < DAYS and date <= now:
                counts[offset] += 1
                seen.add(sha)
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        raise ActivityError(502, "github_unavailable") from None
    return {
        "username": login,
        "start": start.isoformat(),
        "counts": counts,
        "sampled": len(seen),
        "limited": incomplete or total > len(seen) or len(items) == SAMPLE_LIMIT,
    }


def fetch_activity(login, now, open_url):
    return summarize(read_search(search_request(login, now), open_url), login, now)


def run_lookup_worker(request):
    """Bound the complete lookup, not just socket inactivity.

    The handler holds an upstream slot until the child has been reaped, so
    DNS, TLS, headers, and body reads cannot leave a live worker behind.
    The fixed helper emits only a bounded summarized result, not upstream data.
    """
    deadline = monotonic() + REQUEST_TIMEOUT
    try:
        with subprocess.Popen(
            [sys.executable, "-I", __file__],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env={},
        ) as worker:
            try:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(worker.args, REQUEST_TIMEOUT)
                output, _ = worker.communicate(input=request, timeout=remaining)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.communicate()
                raise ActivityError(502, "github_unavailable") from None
            if worker.returncode != 0 or monotonic() >= deadline:
                raise ActivityError(502, "github_unavailable")
        if len(output) > 4096:
            raise ActivityError(502, "github_unavailable")
        result = json.loads(output)
        if not isinstance(result, dict):
            raise ValueError
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise ActivityError(502, "github_unavailable") from None
    if "error" in result:
        code = result["error"]
        if code == "rate_limited":
            raise ActivityError(429, code)
        if code == "search_rejected":
            raise ActivityError(422, code)
        raise ActivityError(502, "github_unavailable")
    return result


def public_activity(login, *, now=None, open_url=None):
    login = normalize_login(login)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if open_url is not None:
        return fetch_activity(login, now, open_url)
    # Same instant for query and filtering; no username in child arguments.
    return run_lookup_worker(f"{login}\n{now.isoformat()}".encode("ascii"))


def worker_result(request):
    try:
        login, instant = request.decode("ascii").splitlines()
        now = datetime.fromisoformat(instant).astimezone(timezone.utc)
        return fetch_activity(
            normalize_login(login), now, build_opener(NoRedirect()).open
        )
    except (UnicodeError, ValueError, OverflowError):
        return {"error": "github_unavailable"}
    except ActivityError as error:
        return {"error": error.code}


if __name__ == "__main__":
    print(json.dumps(worker_result(sys.stdin.buffer.read(128)), separators=(",", ":")))
