from pathlib import Path
import re


def test_viewer_detects_color_files_for_grouping():
    """docs/viewer.html should parse `_colorN` filenames for multi-color previews."""

    html = Path("docs/viewer.html").read_text()
    assert "/color(\\d+)/i" in html, "viewer must recognize _colorN STL names"


def test_viewer_auto_detects_color_groups():
    """Viewer should derive color groups from filenames without manual input."""

    html = Path("docs/viewer.html").read_text()
    assert "colorCount" not in html
    assert "const maxColorIndex" in html
    assert "colorIndex" in html
