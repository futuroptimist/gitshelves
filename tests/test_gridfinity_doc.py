from pathlib import Path


def test_gridfinity_design_notes_usage_guide_is_shipped():
    """Gridfinity design doc should reflect the shipped usage guide."""

    text = Path("docs/gridfinity_design.md").read_text(encoding="utf-8")
    assert "docs/usage.md" in text, "Usage guide link should be documented"
    assert (
        "Add docs/usage.md" not in text
    ), "Future enhancements section should not list shipped docs"
    assert (
        "Add a short Dependencies block" not in text
    ), "Dependencies guidance should no longer be flagged as future work"
