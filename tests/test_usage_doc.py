from pathlib import Path


def test_usage_doc_includes_required_sections():
    repo_root = Path(__file__).resolve().parents[1]
    usage_doc = repo_root / "docs" / "usage.md"
    assert usage_doc.exists(), "docs/usage.md should exist per design spec"
    text = usage_doc.read_text(encoding="utf-8")
    assert "# Usage Guide" in text
    assert "## Slicer Presets" in text
    assert "## AMS Filament Scripts" in text
    assert "```" in text, "usage guide should include at least one example code block"
