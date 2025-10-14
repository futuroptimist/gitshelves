"""Tests for GitHub token resolution helpers."""

from gitshelves.core import github


def test_resolve_token_prefers_explicit(monkeypatch):
    """A provided token should override any environment variables."""

    monkeypatch.setenv("GH_TOKEN", "gh-token")
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")

    assert github.resolve_token("explicit-token") == "explicit-token"


def test_resolve_token_prefers_gh_token(monkeypatch):
    """GH_TOKEN should be preferred when no explicit token is supplied."""

    monkeypatch.setenv("GH_TOKEN", "gh-token")
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")

    assert github.resolve_token(None) == "gh-token"


def test_resolve_token_falls_back_to_github_token(monkeypatch):
    """When GH_TOKEN is missing, fall back to GITHUB_TOKEN."""

    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")

    assert github.resolve_token(None) == "github-token"
