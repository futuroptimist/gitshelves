"""Compatibility layer for legacy imports."""

from __future__ import annotations

import sys
import types

from .core import github as _github

GITHUB_API = _github.GITHUB_API
TOKEN_FALLBACK_ORDER = _github.TOKEN_FALLBACK_ORDER
determine_year_range = _github.determine_year_range
fetch_user_contributions = _github.fetch_user_contributions
resolve_token = _github.resolve_token
requests = _github.requests
datetime = _github.datetime

__all__ = [
    "GITHUB_API",
    "TOKEN_FALLBACK_ORDER",
    "determine_year_range",
    "fetch_user_contributions",
    "resolve_token",
    "requests",
    "datetime",
    "_determine_year_range",
]


# ``_determine_year_range`` used to be private in this module.
_determine_year_range = determine_year_range


class _Shim(types.ModuleType):
    def __getattr__(self, name: str):
        return getattr(_github, name)

    def __setattr__(self, name: str, value):
        if name in {"_github"}:
            super().__setattr__(name, value)
            return
        setattr(_github, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _Shim
