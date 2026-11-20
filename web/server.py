#!/usr/bin/env python3
"""Static assets and a bounded public commit preview for the production image."""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import BoundedSemaphore
from urllib.parse import parse_qs, urlsplit

from github_activity import (
    ACTIVITY_PATH,
    ActivityError,
    RequestBudget,
    normalize_login,
    public_activity,
)

ROOT = Path(__file__).resolve().parent / "dist"
BUDGET = RequestBudget()
UPSTREAM = BoundedSemaphore(2)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == ACTIVITY_PATH:
            return self.github_activity()
        if path in {"/healthz", "/livez"}:
            body = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def github_activity(self):
        try:
            if len(self.path) > 250:
                raise ActivityError(400, "invalid_username")
            params = parse_qs(
                urlsplit(self.path).query,
                keep_blank_values=True,
                max_num_fields=1,
                strict_parsing=True,
            )
            if set(params) != {"username"}:
                raise ActivityError(400, "invalid_username")
            login = normalize_login(params["username"][0])
            if not UPSTREAM.acquire(blocking=False):
                raise ActivityError(429, "rate_limited")
            try:
                if not BUDGET.take():
                    raise ActivityError(429, "rate_limited")
                result = public_activity(login)
            finally:
                UPSTREAM.release()
        except ValueError:
            self.send_json(400, {"error": "invalid_username"})
        except ActivityError as error:
            self.send_json(error.status, {"error": error.code})
        else:
            self.send_json(200, result)

    def send_json(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_request(self, code="-", size="-"):
        if self.path.split("?", 1)[0] == ACTIVITY_PATH:
            # The username is never part of the application access log.
            self.log_message("%s %s %s", self.command, ACTIVITY_PATH, code)
        else:
            super().log_request(code, size)

    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path in {"/healthz", "/livez"}:
            pass  # do_GET already supplied the single no-store policy.
        elif path == ACTIVITY_PATH:
            self.send_header("Cache-Control", "no-store")
        elif path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        elif path.startswith("/models/"):
            self.send_header("Cache-Control", "no-cache")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
