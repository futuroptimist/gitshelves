from pathlib import Path
import re


def test_viewer_detects_color_files_for_grouping():
    """docs/viewer.html should parse `_colorN` filenames for multi-color previews."""

    html = Path("docs/viewer.html").read_text()
    assert "/color(\\d+)/i" in html, "viewer must recognize _colorN STL names"
