from gitshelves.readme import write_year_readme


def test_write_year_readme(tmp_path):
    counts = {(2023, 1): 5, (2023, 2): 20}
    readme = write_year_readme(2023, counts, outdir=tmp_path)
    text = readme.read_text()
    assert "January: 5 contributions" in text
    assert "February: 20 contributions" in text
    assert "`monthly-5x6`" in text


def test_write_year_readme_zero_and_plural(tmp_path):
    counts = {(2024, 1): 1, (2024, 2): 10}
    readme = write_year_readme(2024, counts, outdir=tmp_path)
    text = readme.read_text()
    assert "January: 1 contribution \u2192 1 cube" in text
    assert "February: 10 contributions \u2192 2 cubes" in text
    assert "March: 0 contributions \u2192 0 cubes" in text


def test_write_year_readme_includes_gridfinity_extras(tmp_path):
    counts = {(2025, 5): 12}
    extras = [
        "- Gridfinity layout: `gridfinity_plate.scad` (auto-generated)",
        "- Gridfinity cubes: May (SCAD + STL)",
    ]
    readme = write_year_readme(2025, counts, outdir=tmp_path, extras=extras)
    text = readme.read_text()
    assert "## Gridfinity" in text
    for line in extras:
        assert line in text
