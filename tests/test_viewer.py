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


def test_viewer_dropdown_matches_detected_block_colors():
    """Colors dropdown should follow the detected block-color count (ignoring baseplate)."""

    html = Path("docs/viewer.html").read_text()
    assert (
        "Math.max(maxColorIndex, 1)" in html
    ), "viewer should clamp to at least one color"
    assert (
        "totalGroups += 1" not in html
    ), "baseplate should not inflate block-color selection"
    assert (
        "colorCount.innerHTML" in html
    ), "viewer should rebuild dropdown options to match detected colors"
    assert (
        "Array.from({ length: detected }" in html
    ), "viewer should derive option values from detected color count"
    assert (
        "Detected ${blockColorCount} block color" in html
    ), "viewer should still report the number of loaded color files"


def test_viewer_dropdown_filters_block_colors():
    """Manual color selection should toggle higher-order stacks (README promise)."""

    html = Path("docs/viewer.html").read_text()
    assert "const meshRegistry" in html, "viewer should track loaded meshes"
    assert (
        "colorCount.addEventListener('change'" in html
    ), "dropdown should react to manual selections"
    assert (
        "mesh.visible = colorIndex === 0 || colorIndex <= maxColors" in html
    ), "visibility should clamp to the selected color count"


def test_viewer_reuses_accent_color_for_extra_levels():
    """Legacy levelN files should reuse the accent color for magnitudes above four."""

    html = Path("docs/viewer.html").read_text()
    assert (
        "const accentIndex = palette.length - 1" in html
    ), "viewer should expose an accent index for legacy files"
    assert (
        "Math.min(colorIndex, accentIndex)" in html
    ), "higher color indexes should clamp to the accent color"


def test_viewer_expands_dropdown_to_highest_color_index():
    """Sparse color files should still surface their highest stack in the dropdown."""

    html = Path("docs/viewer.html").read_text()
    assert (
        "const maxColorIndex = stls.reduce" in html
    ), "viewer should derive the highest loaded color index"
    assert (
        "Math.max(maxColorIndex, 1)" in html
    ), "dropdown size should respect the maximum detected index"
    assert (
        "maxColorIndex > 0 ? String(maxColorIndex) : '1'" in html
    ), "default selection should reveal the highest detected color stack"
