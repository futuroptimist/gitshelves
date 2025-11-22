from pathlib import Path


def test_gridfinity_stl_directories_seeded():
    root = Path("stl")
    years = [2021, 2022, 2023, 2024, 2025]

    for year in years:
        year_dir = root / str(year)
        assert (
            year_dir.exists() and year_dir.is_dir()
        ), "Expected stl/year directories per gridfinity spec"
        readme = year_dir / "README.md"
        assert readme.exists(), "Year directories should explain CI-rendered baseplates"
        text = readme.read_text(encoding="utf-8").lower()
        assert "baseplate_2x6.stl" in text
        assert "openscad/baseplate_2x6.scad" in text
