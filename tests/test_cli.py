import argparse
from pathlib import Path

import pytest

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
        assert counts == {(2021, 2): 2}
        assert months_per_row == 10
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
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    called = {}
    monkeypatch.setattr(cli, "generate_scad_monthly", fake_generate)

    def fake_stl(src, dest):
        called["stl"] = (src, dest)

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    assert output.read_text() == "SCAD"
    assert fetched_args["params"] == ("user", "tok", 2021, 2021)
    assert called["stl"][0] == str(output)
    captured = capsys.readouterr()
    assert f"Wrote {output}" in captured.out
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
    called = {}

    def fake_stl(src, dest):
        called["stl"] = (src, dest)

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    assert output.read_text() == "DATA"
    assert called["stl"][0] == str(output)
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
        assert counts == {(2021, 1): 1}
        assert months_per_row == 12
        return "DATA"

    scad_mod.generate_scad_monthly = fake_generate
    scad_mod.generate_scad_monthly_levels = lambda counts, months_per_row=12: {}
    scad_mod.group_scad_levels = lambda levels, groups: {1: "G"}
    scad_mod.scad_to_stl = lambda a, b: None
    scad_mod.generate_monthly_calendar_scads = lambda daily, year, days_per_row=5: {
        m: "//" for m in range(1, 13)
    }
    scad_mod.generate_gridfinity_plate_scad = (
        lambda counts, year, columns=6: "// gridfinity"
    )

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
    )
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    def fake_fetch(username, token=None, start_year=None, end_year=None):
        return [{"created_at": "2021-02-01T00:00:00Z"}]

    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)

    def fake_levels(counts, months_per_row=12):
        assert counts == {(2021, 2): 1}
        assert months_per_row == 12
        return {
            1: "// Generated by g\nL1",
            2: "// Generated by g\nL2",
            3: "// Generated by g\nL3",
        }

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(cli, "load_baseplate_scad", lambda: "// Baseplate")
    called = []

    def fake_stl(src, dest):
        called.append((src, dest))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    scad1 = tmp_path / "c_color1.scad"
    scad2 = tmp_path / "c_color2.scad"
    baseplate_scad = tmp_path / "c_baseplate.scad"
    stl1 = tmp_path / "c_color1.stl"
    stl2 = tmp_path / "c_color2.stl"
    baseplate_stl = tmp_path / "c_baseplate.stl"
    assert scad1.read_text() == "// Generated by gitshelves\nL1\nL2"
    assert scad2.read_text() == "// Generated by gitshelves\nL3"
    assert baseplate_scad.read_text() == "// Baseplate"
    assert called == [
        (str(baseplate_scad), str(baseplate_stl)),
        (str(scad1), str(stl1)),
        (str(scad2), str(stl2)),
    ]
    calendar_dir = tmp_path / "stl" / "2021" / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    captured = capsys.readouterr()
    assert f"Wrote {baseplate_scad}" in captured.out
    assert f"Wrote {scad1}" in captured.out


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
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )

    def fake_levels(counts, months_per_row=12):
        assert counts == {(2021, 2): 1}
        assert months_per_row == 12
        return {1: "// Generated by gitshelves\nL"}

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(cli, "load_baseplate_scad", lambda: "// Baseplate")
    captured = {}

    def fake_group(levels, groups):
        captured["groups"] = groups
        assert levels == {1: "// Generated by gitshelves\nL"}
        return {1: "// Generated by gitshelves\nG"}

    monkeypatch.setattr(cli, "group_scad_levels", fake_group)

    called = []
    monkeypatch.setattr(cli, "scad_to_stl", lambda s, d: called.append((s, d)))
    monkeypatch.setattr(cli, "write_year_readme", lambda y, c: tmp_path / "dummy")

    cli.main()

    scad = tmp_path / "m_color1.scad"
    baseplate_scad = tmp_path / "m_baseplate.scad"
    assert scad.read_text() == "// Generated by gitshelves\nG"
    assert baseplate_scad.read_text() == "// Baseplate"
    assert called == []
    calendar_dir = tmp_path / "monthly-5x6"
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    out = capsys.readouterr().out
    assert f"Wrote {baseplate_scad}" in out
    assert f"Wrote {scad}" in out
    assert captured["groups"] == 2


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

    def fake_write(year, counts):
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

    def fake_write(year, counts):
        captured.append((year, dict(counts)))
        return tmp_path / str(year) / "README.md"

    monkeypatch.setattr(cli, "write_year_readme", fake_write)

    cli.main()

    assert captured == [(2042, {})]
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
