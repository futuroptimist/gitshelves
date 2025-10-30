from pathlib import Path

from gitshelves.render import static


def test_is_library_path_outside_root(tmp_path):
    root = tmp_path / "openscad"
    root.mkdir()
    outside = tmp_path / "other" / "file.scad"
    outside.parent.mkdir()
    outside.write_text("// outside")

    assert static._is_library_path(outside, root) is False


def test_discover_static_scad_files_missing_root(tmp_path):
    missing = tmp_path / "missing"

    assert static.discover_static_scad_files(missing) == []


def test_discover_static_scad_files_skips_lib(tmp_path):
    root = tmp_path / "openscad"
    root.mkdir()
    (root / "top.scad").write_text("// top")
    nested = root / "nested"
    nested.mkdir()
    (nested / "inner.scad").write_text("// inner")
    lib_dir = root / "lib"
    lib_dir.mkdir()
    (lib_dir / "ignored.scad").write_text("// ignored")

    discovered = static.discover_static_scad_files(root)

    assert sorted(path.name for path in discovered) == ["inner.scad", "top.scad"]


def test_discover_static_scad_files_ignores_lib_case_insensitive(tmp_path):
    root = tmp_path / "openscad"
    root.mkdir()
    (root / "keep.scad").write_text("// keep")
    upper_lib = root / "Lib"
    upper_lib.mkdir()
    (upper_lib / "ignored.scad").write_text("// ignored")

    discovered = static.discover_static_scad_files(root)

    assert [path.name for path in discovered] == ["keep.scad"]


def test_render_static_stls_invokes_scad_to_stl(tmp_path, monkeypatch):
    source = tmp_path / "openscad"
    source.mkdir()
    (source / "a.scad").write_text("// a")
    subdir = source / "sub"
    subdir.mkdir()
    (subdir / "b.scad").write_text("// b")

    called: list[tuple[str, str]] = []

    monkeypatch.setattr(
        static,
        "discover_static_scad_files",
        lambda root=None: [
            source / "a.scad",
            subdir / "b.scad",
        ],
    )
    monkeypatch.setattr(
        static,
        "scad_to_stl",
        lambda src, dest: called.append((src, dest)),
    )

    output = tmp_path / "stl"
    rendered = static.render_static_stls(
        source_root=source,
        output_root=output,
    )

    expected_pairs = [
        (source / "a.scad", output / "a.stl"),
        (subdir / "b.scad", output / "sub" / "b.stl"),
    ]
    assert rendered == expected_pairs
    assert called == [(str(pair[0]), str(pair[1])) for pair in expected_pairs]
    for _, stl_path in expected_pairs:
        assert stl_path.parent.exists()


def test_render_static_stls_removes_stale_outputs(tmp_path, monkeypatch):
    source = tmp_path / "openscad"
    source.mkdir()
    keep_scad = source / "keep.scad"
    keep_scad.write_text("// keep")

    output = tmp_path / "stl"
    output.mkdir()
    stale_root = output / "orphan.stl"
    stale_root.write_text("stale")
    stale_dir = output / "old"
    stale_dir.mkdir()
    stale_nested = stale_dir / "unused.stl"
    stale_nested.write_text("old")

    recorded: list[tuple[str, str]] = []
    monkeypatch.setattr(
        static,
        "scad_to_stl",
        lambda src, dest: recorded.append((src, dest)),
    )

    rendered = static.render_static_stls(
        source_root=source,
        output_root=output,
    )

    expected_stl = output / "keep.stl"
    assert rendered == [(keep_scad, expected_stl)]
    assert recorded == [(str(keep_scad), str(expected_stl))]
    assert not stale_root.exists()
    assert not stale_nested.exists()
    assert not stale_dir.exists()


def test_cli_invokes_render_static_stls(monkeypatch, capsys):
    called: dict[str, tuple[Path | None, Path | None]] = {}

    def fake_render_static_stls(*, source_root=None, output_root=None):
        called["args"] = (source_root, output_root)
        return [
            (Path("source.scad"), Path("output.stl")),
        ]

    monkeypatch.setattr(static, "render_static_stls", fake_render_static_stls)

    exit_code = static._cli([])

    assert exit_code == 0
    assert called["args"] == (None, None)
    captured = capsys.readouterr()
    assert "Rendered output.stl from source.scad" in captured.out
