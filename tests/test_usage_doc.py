from pathlib import Path


def _usage_text() -> str:
    path = Path("docs/usage.md")
    assert path.exists(), "docs/usage.md should exist per documentation roadmap"
    return path.read_text(encoding="utf-8")


def test_usage_doc_includes_slicer_presets_section():
    text = _usage_text().lower()
    assert "## slicer presets" in text, "Slicer preset guidance should be documented"
    assert "layer height" in text, "Layer height recommendations must be included"
    assert "infill" in text, "Infill guidance is expected for slicer presets"


def test_usage_doc_includes_ams_filament_script_example():
    text = _usage_text().lower()
    assert (
        "## ams filament scripts" in text
    ), "AMS automation examples should be present"
    assert (
        "g-code" in text or "gcode" in text
    ), "G-code snippet expected for AMS scripts"
    assert (
        "m600" in text or "filament change" in text
    ), "AMS section should mention filament change handling"
