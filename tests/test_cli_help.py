"""CLI help text regressions."""

import pytest

import gitshelves.cli as cli
from gitshelves.cli import main


def test_help_describes_token_fallback_order(capsys):
    """The --token help text should document the full fallback order."""

    with pytest.raises(SystemExit):
        main(["--help"])
    captured = capsys.readouterr()
    assert "fallback order: --token value, GH_TOKEN, then GITHUB_TOKEN" in captured.out


def test_version_flag_uses_package_version(monkeypatch, capsys):
    """`--version` should report the package ``__version__`` when metadata is missing."""

    import gitshelves

    monkeypatch.setattr(gitshelves, "__version__", "9.9.9", raising=False)

    def raise_not_found(*_args, **_kwargs):
        raise cli.metadata.PackageNotFoundError

    monkeypatch.setattr(cli.metadata, "version", raise_not_found)

    with pytest.raises(SystemExit):
        main(["--version"])
    captured = capsys.readouterr()
    assert "9.9.9" in captured.out
