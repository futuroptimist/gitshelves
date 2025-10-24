from gitshelves.render import static


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
