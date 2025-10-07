from pathlib import Path


def test_readme_lists_gridfinity_dependencies_and_headless_tools():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "## Dependencies" in text, "README should expose a dependencies section"
    assert (
        "https://github.com/kennetek/gridfinity-rebuilt-openscad" in text
    ), "Gridfinity baseplate library must be linked"
    assert (
        "https://github.com/vector76/gridfinity_openscad" in text
    ), "Reference implementation should be credited"
    assert "xvfb-run" in text, "Headless rendering helper must be documented"
