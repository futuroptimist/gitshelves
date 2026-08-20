from pathlib import Path


def test_legacy_viewer_is_a_documented_migration_page():
    html = Path("docs/viewer.html").read_text()
    assert "viewer moved" in html
    for contract in ("_colorN", "levelN", "OrbitControls", "STLLoader", "local STL"):
        assert contract in html
    assert "cdn.jsdelivr" not in html


def test_web_viewer_has_behavioral_test_suite():
    tests = Path("web/tests/core.test.ts").read_text()
    assert "canonical logarithmic boundaries" in tests
    assert "classifies compatibility names" in tests
    assert "preserves bytes" in tests
