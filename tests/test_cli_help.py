"""CLI help text regressions."""

import pytest

from gitshelves.cli import main


def test_help_describes_token_fallback_order(capsys):
    """The --token help text should document the full fallback order."""

    with pytest.raises(SystemExit):
        main(["--help"])
    captured = capsys.readouterr()
    assert "fallback order: --token value, GH_TOKEN, then GITHUB_TOKEN" in captured.out
