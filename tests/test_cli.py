import argparse
from pathlib import Path

import pytest

from gitshelves.scad import SPACING

import gitshelves
import gitshelves.cli as cli


def test_cli_main(tmp_path, monkeypatch, capsys):
    output = tmp_path / "out.scad"

    fetched_args = {}

    monkeypatch.chdir(tmp_path)

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        fetched_args["params"] = (username, token, start_year, end_year)
        return [
            {"created_at": "2021-02-01T12:00:00Z"},
            {"created_at": "2021-02-15T12:00:00Z"},
        ]

    def fake_generate(counts, months_per_row=12):
        assert months_per_row == 10
        assert set(counts) == {(2021, month) for month in range(1, 13)}
        assert counts[(2021, 2)] == 2
        assert sum(counts.values()) == 2
        return "SCAD"

    args = argparse.Namespace(
        username="user",
        token="tok",
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=10,
        stl=str(tmp_path / "out.stl"),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    stl_calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(cli, "generate_scad_monthly", fake_generate)

    def fake_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    assert output.read_text() == "SCAD"
    assert fetched_args["params"] == ("user", "tok", 2021, 2021)
    baseplate_scad = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    assert baseplate_scad.exists()
    assert len(stl_calls) == 2
    assert stl_calls[0][0].resolve() == baseplate_scad.resolve()
    assert stl_calls[1][0].resolve() == output.resolve()
    captured = capsys.readouterr()
    assert f"Wrote {output}" in captured.out
    assert "baseplate_2x6.scad" in captured.out
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    files = sorted(calendar_dir.glob("*.scad"))
    assert len(files) == 12
    february = calendar_dir / "02_february.scad"
    text = february.read_text()
    assert "2021-02-01" in text
    assert "2021-02-15" in text


def test_cli_creates_output_dirs(tmp_path, monkeypatch):
    output = tmp_path / "nested" / "dir" / "out.scad"
    args = argparse.Namespace(
        username="u",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=str(tmp_path / "nested" / "dir" / "out.stl"),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "DATA"
    )
    stl_calls: list[tuple[Path, Path]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    assert output.read_text() == "DATA"
    baseplate_scad = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    assert baseplate_scad.exists()
    assert len(stl_calls) == 2
    assert stl_calls[0][0].resolve() == baseplate_scad.resolve()
    assert stl_calls[1][0].resolve() == output.resolve()
    assert (tmp_path / "nested" / "dir").is_dir()
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert calendar_dir.is_dir()
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_env_token(tmp_path, monkeypatch):
    output = tmp_path / "out.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GH_TOKEN", "envtok")
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )

    captured = {}

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        captured["token"] = token
        return [{"created_at": "2021-01-01T00:00:00Z"}]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "S"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda a, b: None)

    cli.main()

    assert output.read_text() == "S"
    assert captured["token"] == "envtok"
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_github_token_env(tmp_path, monkeypatch):
    output = tmp_path / "out.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "envtok2")
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )

    captured = {}

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        captured["token"] = token
        return [{"created_at": "2021-01-01T00:00:00Z"}]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "S"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda a, b: None)

    cli.main()

    assert output.read_text() == "S"
    assert captured["token"] == "envtok2"
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_runpy(tmp_path, monkeypatch):
    output = tmp_path / "file.scad"
    args = argparse.Namespace(
        username="u",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )

    import sys, types, runpy

    fetch_mod = types.ModuleType("gitshelves.fetch")

    def fake_fetch(*a, **k):
        return [{"created_at": "2021-01-01T00:00:00Z"}]

    fetch_mod.fetch_user_contributions = fake_fetch
    from gitshelves.fetch import _determine_year_range as real_determine_year_range

    fetch_mod._determine_year_range = real_determine_year_range

    scad_mod = types.ModuleType("gitshelves.scad")

    def fake_generate(counts, months_per_row=12):
        assert months_per_row == 12
        assert set(counts) == {(2021, month) for month in range(1, 13)}
        assert counts[(2021, 1)] == 1
        assert sum(counts.values()) == 1
        return "DATA"

    scad_mod.generate_scad_monthly = fake_generate
    scad_mod.generate_scad_monthly_levels = lambda counts, months_per_row=12: {}
    scad_mod.generate_zero_month_annotations = lambda counts, months_per_row: []
    scad_mod.group_scad_levels = lambda levels, groups: {1: "G"}
    scad_mod.scad_to_stl = lambda a, b: None
    scad_mod.generate_monthly_calendar_scads = lambda daily, year, days_per_row=5: {
        m: "//" for m in range(1, 13)
    }
    scad_mod.generate_gridfinity_plate_scad = (
        lambda counts, year, columns=6: "// gridfinity"
    )
    scad_mod.blocks_for_contributions = lambda count: 1 if count else 0
    scad_mod.generate_contrib_cube_stack_scad = lambda levels: "// cubes"

    sys.modules["gitshelves.fetch"] = fetch_mod
    sys.modules["gitshelves.scad"] = scad_mod
    sys.modules.pop("gitshelves.cli", None)

    runpy.run_module("gitshelves.cli", run_name="__main__")

    assert output.read_text() == "DATA"
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_multiple_colors(tmp_path, monkeypatch, capsys):
    base = tmp_path / "c.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(tmp_path / "c.stl"),
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        return [{"created_at": "2021-02-01T00:00:00Z"}]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)

    def fake_levels(counts, months_per_row=12):
        assert months_per_row == 12
        assert set(counts) == {(2021, month) for month in range(1, 13)}
        assert counts[(2021, 2)] == 1
        assert sum(counts.values()) == 1
        return {
            1: "// Generated by g\nL1",
            2: "// Generated by g\nL2",
            3: "// Generated by g\nL3",
        }

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    stl_calls: list[tuple[Path, Path]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    scad1 = tmp_path / "c_color1.scad"
    scad2 = tmp_path / "c_color2.scad"
    per_year_baseplate = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    baseplate_scad = tmp_path / "c_baseplate.scad"
    stl1 = tmp_path / "c_color1.stl"
    stl2 = tmp_path / "c_color2.stl"
    baseplate_stl = tmp_path / "c_baseplate.stl"
    scad1_text = scad1.read_text()
    scad2_text = scad2.read_text()
    assert scad1_text.startswith("// Generated by gitshelves\nL1")
    assert scad2_text.startswith("// Generated by gitshelves\nL2\nL3")
    reserved = "// 2021-01 (0 contributions) reserved at [0, 0]"
    assert reserved in scad1_text
    assert reserved in scad2_text
    assert baseplate_scad.read_text() == "// Baseplate"
    assert per_year_baseplate.exists()
    assert len(stl_calls) == 4
    assert stl_calls[0][0].resolve() == per_year_baseplate.resolve()
    assert stl_calls[1][0].resolve() == baseplate_scad.resolve()
    assert stl_calls[2][0].resolve() == scad1.resolve()
    assert stl_calls[3][0].resolve() == scad2.resolve()
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    captured = capsys.readouterr()
    assert f"Wrote {baseplate_scad}" in captured.out
    assert f"Wrote {scad1}" in captured.out


def test_cli_color_outputs_include_zero_month_annotations(tmp_path, monkeypatch):
    """Color-group SCADs should annotate zero-contribution months (README promise)."""

    base = tmp_path / "annotated.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    contributions = [
        {"created_at": "2021-01-01T00:00:00Z"},
        {"created_at": "2021-03-05T00:00:00Z"},
        {"created_at": "2021-03-06T00:00:00Z"},
    ]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: contributions)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    color_files = sorted(tmp_path.glob("annotated_color*.scad"))
    assert color_files, "Expected color-group SCAD outputs"
    expected_comment = "// 2021-02 (0 contributions) reserved at [12, 0]"
    for path in color_files:
        text = path.read_text()
        assert text.startswith("// Generated by gitshelves")
        assert (
            expected_comment in text
        ), f"Missing zero-contribution annotation in {path.name}"


def test_cli_supports_four_block_colors(tmp_path, monkeypatch, capsys):
    base = tmp_path / "multi.scad"
    stl = tmp_path / "multi.stl"
    monkeypatch.chdir(tmp_path)

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        return [
            {"created_at": "2021-01-01T00:00:00Z"},
            {"created_at": "2021-02-01T00:00:00Z"},
            {"created_at": "2021-03-01T00:00:00Z"},
            {"created_at": "2021-04-01T00:00:00Z"},
        ]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)

    def fake_levels(counts, months_per_row=12):
        assert counts[(2021, 1)] == 1
        return {
            1: "// Generated by gitshelves\nL1",
            2: "// Generated by gitshelves\nL2",
            3: "// Generated by gitshelves\nL3",
            4: "// Generated by gitshelves\nL4",
        }

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )

    def fake_write_year_readme(year, counts, extras=None):
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# placeholder")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)

    stl_calls: list[tuple[Path, Path]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    groups_seen = {}
    real_group = cli.group_scad_levels

    def capture_groups(levels, groups):
        groups_seen["value"] = groups
        return real_group(levels, groups)

    monkeypatch.setattr(cli, "group_scad_levels", capture_groups)

    argv = [
        "user",
        "--token",
        "tok",
        "--start-year",
        "2021",
        "--end-year",
        "2021",
        "--output",
        str(base),
        "--stl",
        str(stl),
        "--colors",
        "5",
    ]

    cli.main(argv)

    assert groups_seen["value"] == 4
    baseplate_scad = tmp_path / "multi_baseplate.scad"
    assert baseplate_scad.read_text() == "// Baseplate"
    for idx in range(1, 5):
        path = tmp_path / f"multi_color{idx}.scad"
        assert path.read_text().startswith("// Generated by gitshelves")

    per_year_baseplate = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    assert per_year_baseplate.exists()
    assert len(stl_calls) == 6
    assert stl_calls[0][0].resolve() == per_year_baseplate.resolve()
    captured = capsys.readouterr().out
    assert f"Wrote {baseplate_scad}" in captured


def test_cli_multiple_colors_custom_baseplate_template(tmp_path, monkeypatch):
    base = tmp_path / "custom.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_1x12.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )

    monkeypatch.setattr(
        cli,
        "generate_scad_monthly_levels",
        lambda counts, months_per_row=12: {1: "// Generated by gitshelves\nL1"},
    )

    seen: dict[str, str] = {}

    def fake_load_baseplate_scad(name: str = "baseplate_2x6.scad") -> str:
        seen["name"] = name
        return f"// {name}"

    monkeypatch.setattr(cli, "load_baseplate_scad", fake_load_baseplate_scad)
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    baseplate_scad = tmp_path / "custom_baseplate.scad"
    assert baseplate_scad.read_text() == "// baseplate_1x12.scad"
    assert seen["name"] == "baseplate_1x12.scad"


def test_cli_multiple_colors_baseplate_typeerror_falls_back(tmp_path, monkeypatch):
    """Gracefully fall back when ``load_baseplate_scad`` rejects template args."""

    base = tmp_path / "fallback.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly_levels",
        lambda counts, months_per_row=12: {1: "// Generated by gitshelves"},
    )
    monkeypatch.setattr(
        cli,
        "group_scad_levels",
        lambda levels, groups: {1: "// Generated by gitshelves\nG1"},
    )
    monkeypatch.setattr(
        cli,
        "generate_zero_month_annotations",
        lambda counts, months_per_row=12: [],
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_write_year_baseplate", lambda *a, **k: None)

    def fake_write_year_readme(year, counts, extras=None):
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# placeholder")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)

    calls: list[tuple[tuple, dict]] = []

    def flaky_load(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 1:
            raise TypeError("unexpected argument")
        return "// fallback"

    monkeypatch.setattr(cli, "load_baseplate_scad", flaky_load)

    cli.main()

    baseplate_scad = tmp_path / "fallback_baseplate.scad"
    color_scad = tmp_path / "fallback_color1.scad"

    # Verify fallback behavior
    assert baseplate_scad.read_text() == "// fallback"
    assert color_scad.read_text().startswith("// Generated by gitshelves")
    assert calls[0][0] == ("baseplate_2x6.scad",)
    assert calls[1][0] == ()


def test_cli_multiple_colors_without_stl(tmp_path, monkeypatch, capsys):
    base = tmp_path / "m.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )

    def fake_levels(counts, months_per_row=12):
        assert months_per_row == 12
        assert set(counts) == {(2021, month) for month in range(1, 13)}
        assert counts[(2021, 2)] == 1
        assert sum(counts.values()) == 1
        return {1: "// Generated by gitshelves\nL"}

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    captured = {}

    def fake_group(levels, groups):
        captured["groups"] = groups
        assert levels == {1: "// Generated by gitshelves\nL"}
        return {1: "// Generated by gitshelves\nG"}

    monkeypatch.setattr(cli, "group_scad_levels", fake_group)

    called = []
    monkeypatch.setattr(cli, "scad_to_stl", lambda s, d: called.append((s, d)))
    monkeypatch.setattr(
        cli, "write_year_readme", lambda y, c, extras=None: tmp_path / "dummy"
    )

    cli.main()

    scad = tmp_path / "m_color1.scad"
    baseplate_scad = tmp_path / "m_baseplate.scad"
    text = scad.read_text()
    assert text.startswith("// Generated by gitshelves\nG")
    assert "// 2021-01 (0 contributions) reserved" in text
    assert baseplate_scad.read_text() == "// Baseplate"
    assert called == []
    calendar_dir = tmp_path / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    out = capsys.readouterr().out
    assert f"Wrote {baseplate_scad}" in out
    assert f"Wrote {scad}" in out
    assert captured["groups"] == 2


def test_cli_colors_with_more_levels_than_groups(tmp_path, monkeypatch, capsys):
    base = tmp_path / "many.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=5,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )

    def fake_levels(counts, months_per_row=12):
        return {
            1: "// Generated by g\nL1",
            2: "// Generated by g\nL2",
            3: "// Generated by g\nL3",
            4: "// Generated by g\nL4",
            5: "// Generated by g\nL5",
        }

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )

    def fake_write_year_readme(year, counts, extras=None):
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# materials")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    baseplate_scad = tmp_path / "many_baseplate.scad"
    assert baseplate_scad.read_text() == "// Baseplate"

    color1 = tmp_path / "many_color1.scad"
    color2 = tmp_path / "many_color2.scad"
    color3 = tmp_path / "many_color3.scad"
    color4 = tmp_path / "many_color4.scad"
    color_texts = [
        color1.read_text(),
        color2.read_text(),
        color3.read_text(),
        color4.read_text(),
    ]
    for idx, text in enumerate(color_texts, start=1):
        assert text.startswith("// Generated by gitshelves")
        assert "// 2021-02 (0 contributions) reserved" in text
    assert "L1" in color_texts[0]
    assert "L2" in color_texts[1]
    assert "L3" in color_texts[2]
    assert "L4" in color_texts[3]
    assert "L5" in color_texts[3]
    assert not (tmp_path / "many_color5.scad").exists()

    out = capsys.readouterr().out
    assert f"Wrote {baseplate_scad}" in out
    assert f"Wrote {color1}" in out
    assert f"Wrote {color4}" in out


def test_cli_writes_readmes_for_full_range(tmp_path, monkeypatch):
    base = tmp_path / "out.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2023,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        return [
            {"created_at": "2021-01-01T00:00:00Z"},
            {"created_at": "2023-12-31T00:00:00Z"},
        ]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    called_years: list[int] = []

    def fake_write(year, counts, extras=None):
        called_years.append(year)
        return tmp_path / str(year) / "README.md"

    monkeypatch.setattr(cli, "write_year_readme", fake_write)

    cli.main()

    assert called_years == [2021, 2022, 2023]
    assert base.read_text() == "SCAD"
    for year in (2021, 2022, 2023):
        calendar_dir = tmp_path / str(year) / "monthly-5x6"
        assert calendar_dir.is_dir()
        assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_writes_yearly_baseplate_scad(tmp_path, monkeypatch):
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(tmp_path / "chart.scad"),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )

    def fail_stl(*_args, **_kwargs):  # pragma: no cover - sanity guard
        raise AssertionError("scad_to_stl should not run without --stl")

    monkeypatch.setattr(cli, "scad_to_stl", fail_stl)

    cli.main()

    baseplate = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    assert baseplate.exists()
    text = baseplate.read_text()
    assert "gridfinity_baseplate" in text


def test_cli_writes_yearly_baseplate_stl(tmp_path, monkeypatch):
    output = tmp_path / "chart.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=str(tmp_path / "chart.stl"),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )

    stl_calls: list[tuple[Path, Path]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    baseplate = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    baseplate_stl = baseplate.with_suffix(".stl")
    assert baseplate.exists()
    assert any(
        src.resolve() == baseplate.resolve()
        and dest.resolve() == baseplate_stl.resolve()
        for src, dest in stl_calls
    )
    assert any(
        src.resolve() == output.resolve()
        and dest.resolve() == (tmp_path / "chart.stl").resolve()
        for src, dest in stl_calls
    )


def test_cli_preserves_empty_year_rows(tmp_path, monkeypatch):
    output = tmp_path / "layout.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2023,
        output=str(output),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2023-12-15T00:00:00Z"}],
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )

    cli.main()

    scad_text = output.read_text()
    expected_x = 11 * SPACING
    expected_y = 2 * SPACING
    assert (
        f"translate([{expected_x}, {expected_y}, 0]) cube(10); // 2023-12" in scad_text
    )
    assert f"translate([{expected_x}, 0, 0]) cube(10); // 2023-12" not in scad_text


def test_cli_writes_readme_when_no_contributions(tmp_path, monkeypatch):
    base = tmp_path / "empty.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=None,
        end_year=None,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: [])
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_determine_year_range", lambda start, end: (2042, 2042))

    captured: list[tuple[int, dict]] = []

    def fake_write(year, counts, extras=None):
        captured.append((year, dict(counts)))
        return tmp_path / str(year) / "README.md"

    monkeypatch.setattr(cli, "write_year_readme", fake_write)

    cli.main()

    assert captured
    recorded_year, recorded_counts = captured[0]
    assert recorded_year == 2042
    assert set(recorded_counts) == {(2042, month) for month in range(1, 13)}
    assert all(value == 0 for value in recorded_counts.values())
    assert base.read_text() == "SCAD"
    calendar_dir = tmp_path / "2042" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    january = calendar_dir / "01_january.scad"
    assert january.read_text().strip() == "// Generated by gitshelves"


def test_cli_generates_gridfinity_layout(
    tmp_path, monkeypatch, capsys, gridfinity_library
):
    base = tmp_path / "grid.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=True,
        gridfinity_columns=4,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    layout_path = tmp_path / "stl" / "2021" / "gridfinity_plate.scad"
    text = layout_path.read_text()
    assert text.startswith("// Generated by gitshelves")
    assert "grid_x = 4;" in text
    assert "grid_y = 3;" in text
    assert "2021-01" in text
    captured = capsys.readouterr().out
    assert f"Wrote {layout_path.relative_to(tmp_path)}" in captured


def test_cli_generates_gridfinity_layout_stl(
    tmp_path, monkeypatch, capsys, gridfinity_library
):
    base = tmp_path / "grid.scad"
    stl_path = tmp_path / "grid.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(stl_path),
        colors=1,
        gridfinity_layouts=True,
        gridfinity_columns=4,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    stl_calls: list[tuple[Path, Path]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src).resolve(), Path(dest).resolve()))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    layout_path = tmp_path / "stl" / "2021" / "gridfinity_plate.scad"
    layout_stl = layout_path.with_suffix(".stl")
    assert (layout_path.resolve(), layout_stl.resolve()) in stl_calls
    captured = capsys.readouterr().out
    assert f"Wrote {layout_stl.relative_to(tmp_path)}" in captured


def test_cli_rejects_non_positive_gridfinity_columns(tmp_path, monkeypatch, capsys):
    """`--gridfinity-columns` should reject non-positive values before running."""

    monkeypatch.chdir(tmp_path)

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("gridfinity helpers should not run when columns <= 0")

    monkeypatch.setattr(cli, "fetch_user_contributions", should_not_run)
    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", should_not_run)
    monkeypatch.setattr(cli, "generate_scad_monthly", should_not_run)
    monkeypatch.setattr(cli, "generate_gridfinity_plate_scad", should_not_run)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "user",
                "--gridfinity-layouts",
                "--gridfinity-columns",
                "0",
            ]
        )

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "--gridfinity-columns must be positive" in captured.err


def test_cli_generates_gridfinity_cubes(tmp_path, monkeypatch, gridfinity_library):
    """`--gridfinity-cubes` alone should only emit SCAD stacks (docs promise)."""
    base = tmp_path / "grid.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=True,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    feb_entries = [
        {"created_at": f"2021-02-{day:02d}T00:00:00Z"} for day in range(1, 11)
    ]
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: feb_entries + [{"created_at": "2021-04-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    recorded_levels = []

    def fake_cube_stack(levels):
        recorded_levels.append(levels)
        return f"// cubes {levels}"

    monkeypatch.setattr(cli, "generate_contrib_cube_stack_scad", fake_cube_stack)

    def fake_stl(*_args):  # pragma: no cover - should not be called
        raise AssertionError("scad_to_stl should not run without --stl")

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    assert not (year_dir / "contrib_cube_01.scad").exists()
    feb_scad = year_dir / "contrib_cube_02.scad"
    apr_scad = year_dir / "contrib_cube_04.scad"
    assert feb_scad.read_text() == "// cubes 2"
    assert apr_scad.read_text() == "// cubes 1"
    assert recorded_levels == [2, 1]


def test_cli_generates_gridfinity_cube_stls_when_requested(
    tmp_path, monkeypatch, gridfinity_library
):
    """Pairing `--gridfinity-cubes` with `--stl` should render cube STLs."""
    base = tmp_path / "grid.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(tmp_path / "grid.stl"),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=True,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    feb_entries = [
        {"created_at": f"2021-02-{day:02d}T00:00:00Z"} for day in range(1, 11)
    ]
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: feb_entries + [{"created_at": "2021-04-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    monkeypatch.setattr(
        cli,
        "generate_contrib_cube_stack_scad",
        lambda levels: f"// cubes {levels}",
    )

    stl_calls: list[tuple[str, str]] = []

    def fake_stl(src, dest):
        stl_calls.append((Path(src).name, Path(dest).name))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    feb_scad = year_dir / "contrib_cube_02.scad"
    apr_scad = year_dir / "contrib_cube_04.scad"
    assert feb_scad.read_text() == "// cubes 2"
    assert apr_scad.read_text() == "// cubes 1"
    assert ("baseplate_2x6.scad", "baseplate_2x6.stl") in stl_calls
    assert ("contrib_cube_02.scad", "contrib_cube_02.stl") in stl_calls
    assert ("contrib_cube_04.scad", "contrib_cube_04.stl") in stl_calls
    assert (Path(base).name, Path(base).with_suffix(".stl").name) in stl_calls


def test_cli_readme_mentions_gridfinity_outputs(
    tmp_path, monkeypatch, gridfinity_library
):
    base = tmp_path / "grid.scad"
    stl_target = tmp_path / "grid.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(stl_target),
        colors=1,
        gridfinity_layouts=True,
        gridfinity_columns=6,
        gridfinity_cubes=True,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    entries = [
        {"created_at": "2021-02-01T00:00:00Z"},
        {"created_at": "2021-02-02T00:00:00Z"},
        {"created_at": "2021-04-01T00:00:00Z"},
    ]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli,
        "generate_gridfinity_plate_scad",
        lambda counts, year, columns=6: "// gridfinity",
    )
    monkeypatch.setattr(
        cli,
        "generate_contrib_cube_stack_scad",
        lambda levels: f"// cubes {levels}",
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    readme_path = tmp_path / "stl" / "2021" / "README.md"
    text = readme_path.read_text()
    assert "## Gridfinity" in text
    assert "gridfinity_plate.scad" in text
    assert "gridfinity_plate.stl" in text
    assert "Gridfinity cubes" in text
    assert "Feb" in text and "Apr" in text


def test_cli_readme_notes_empty_gridfinity_cubes(tmp_path, monkeypatch):
    base = tmp_path / "grid.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2022,
        end_year=2022,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=True,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: [])
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    cli.main()

    readme_path = tmp_path / "stl" / "2022" / "README.md"
    text = readme_path.read_text()
    assert "- Gridfinity cubes: none generated (no contributions)" in text


def test_cli_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    out = capsys.readouterr().out.strip()
    assert gitshelves.__version__ in out


def test_cli_help_mentions_env_vars():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "gitshelves.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert "GH_TOKEN" in result.stdout
    assert "GITHUB_TOKEN" in result.stdout
