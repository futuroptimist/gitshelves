from pathlib import Path


def test_build_stl_upload_step():
    wf = Path(".github/workflows/build-stl.yml").read_text()
    assert "actions/upload-artifact" in wf
    assert "path: stl/${{ matrix.year }}/baseplate_2x6.stl" in wf
    assert "xvfb-run" in wf
