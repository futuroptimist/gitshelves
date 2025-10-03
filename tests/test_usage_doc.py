from pathlib import Path


def test_usage_doc_includes_required_sections():
    usage = Path("docs/usage.md")
    assert usage.exists(), "docs/usage.md must be created per design spec"
    text = usage.read_text(encoding="utf-8")
    assert "Slicer Presets" in text
    assert "AMS Filament" in text
