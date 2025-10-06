from pathlib import Path
import re


def test_viewer_detects_color_files_for_grouping():
    """docs/viewer.html should parse `_colorN` filenames for multi-color previews."""

    html = Path("docs/viewer.html").read_text()
    assert "/color(\\d+)/i" in html, "viewer must recognize _colorN STL names"
    assert 'value="5"' in html, "viewer should offer a five-color option"


def test_viewer_reports_detected_color_groups():
    """The viewer should surface detected color counts to match README guidance."""

    html = Path("docs/viewer.html").read_text()
    assert 'id="detectedColors"' in html, "viewer should display detected color summary"
    assert "detectedColors.textContent" in html
    assert "colorCount.value =" in html
    palette = re.search(r"const palette = \[(.*?)\];", html, re.S)
    assert palette, "palette definition missing"
    colors = re.findall(r"0x[0-9a-fA-F]+", palette.group(1))
    assert len(colors) >= 5, "palette should provide baseplate plus four block colors"
