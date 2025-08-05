from gitshelves.readme import write_year_readme


def test_write_year_readme(tmp_path):
    counts = {(2023, 1): 5, (2023, 2): 20}
    readme = write_year_readme(2023, counts, outdir=tmp_path)
    text = readme.read_text()
    assert "January: 5 contributions" in text
    assert "February: 20 contributions" in text
