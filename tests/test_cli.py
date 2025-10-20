import argparse
import json
import runpy
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest

from gitshelves.scad import SPACING

import gitshelves
import gitshelves.cli as cli


def calendar_slug(days_per_row: int = 12) -> str:
    return f"monthly-{days_per_row}x6"


def test_cli_generate_contrib_cube_stack_scad_delegates(monkeypatch):
    stub = types.SimpleNamespace(
        generate_contrib_cube_stack_scad=lambda levels: f"stub-{levels}"
    )
    monkeypatch.setitem(sys.modules, "gitshelves.scad", stub)

    assert cli.generate_contrib_cube_stack_scad(2) == "stub-2"


def test_cli_scad_to_stl_delegates(monkeypatch):
    calls: list[tuple[tuple, dict]] = []

    def fake_scad_to_stl(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(cli._scad_module(), "scad_to_stl", fake_scad_to_stl)

    cli.scad_to_stl("in.scad", "out.stl")

    assert calls == [(("in.scad", "out.stl"), {})]


def test_cli_group_scad_levels_delegates(monkeypatch):
    calls: list[tuple[tuple, dict]] = []

    class Stub:
        def group_scad_levels(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {1: ["A"]}

    monkeypatch.setitem(sys.modules, "gitshelves.scad", Stub())

    result = cli.group_scad_levels("levels", groups=3)

    assert result == {1: ["A"]}
    assert calls == [(("levels",), {"groups": 3})]


def test_cli_group_scad_levels_with_mapping_fallback(monkeypatch):
    calls: list[tuple[tuple, dict]] = []

    class Stub:
        def group_scad_levels(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {0: ["base"], 1: ["accent"]}

    monkeypatch.setitem(sys.modules, "gitshelves.scad", Stub())

    grouped, mapping = cli.group_scad_levels_with_mapping("levels", groups=2)

    assert grouped == {0: ["base"], 1: ["accent"]}
    assert mapping == {0: [], 1: []}
    assert calls == [(("levels",), {"groups": 2})]


def test_cli_module_main_guard_invokes_main():
    with pytest.raises(SystemExit):
        runpy.run_module("gitshelves.cli.__init__", run_name="__main__", alter_sys=True)


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
    metadata_path = output.with_suffix(".json")
    metadata = json.loads(metadata_path.read_text())
    assert metadata["kind"] == "monthly"
    assert metadata["stl"] == str(tmp_path / "out.stl")
    assert metadata["stl_generated"] is True
    assert metadata["monthly_contributions"]
    assert any(entry["month"] == 1 for entry in metadata["zero_months"])
    baseplate_scad = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    assert baseplate_scad.exists()
    baseplate_metadata = json.loads(baseplate_scad.with_suffix(".json").read_text())
    assert baseplate_metadata["kind"] == "year-baseplate"
    assert baseplate_metadata["year"] == 2021
    assert baseplate_metadata["stl_generated"] is True
    assert (
        Path(baseplate_metadata["stl"]).resolve()
        == baseplate_scad.with_suffix(".stl").resolve()
    )
    readme_path = tmp_path / "stl" / "2021" / "README.md"
    readme_text = readme_path.read_text()
    assert "[`baseplate_2x6.scad`](baseplate_2x6.scad)" in readme_text
    assert "[`baseplate_2x6.stl`](baseplate_2x6.stl)" in readme_text
    assert len(stl_calls) == 2
    assert stl_calls[0][0].resolve() == baseplate_scad.resolve()
    assert stl_calls[1][0].resolve() == output.resolve()
    captured = capsys.readouterr()
    assert f"Wrote {output}" in captured.out
    assert "baseplate_2x6.scad" in captured.out
    calendar_dir = tmp_path / "stl" / "2021" / calendar_slug(args.months_per_row)
    files = sorted(calendar_dir.glob("*.scad"))
    assert len(files) == 12
    february = calendar_dir / "02_february.scad"
    text = february.read_text()
    assert "2021-02-01" in text
    assert "2021-02-15" in text
    february_meta = json.loads(february.with_suffix(".json").read_text())
    assert february_meta["kind"] == "monthly-calendar"
    assert february_meta["stl_generated"] is False
    assert february_meta["stl"] is None
    assert any(day["day"] == 1 for day in february_meta["daily_contributions"])


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
        calendar_days_per_row=5,
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
    calendar_dir = tmp_path / "stl" / "2021" / calendar_slug(args.calendar_days_per_row)
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
        calendar_days_per_row=5,
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
    readme_text = (tmp_path / "stl" / "2021" / "README.md").read_text()
    assert "[`baseplate_2x6.scad`](baseplate_2x6.scad)" in readme_text
    assert "[`baseplate_2x6.stl`](baseplate_2x6.stl)" not in readme_text
    expected_slug = calendar_slug(
        getattr(args, "calendar_days_per_row", args.months_per_row)
    )
    calendar_dir = tmp_path / "stl" / "2021" / expected_slug
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_writes_run_summary(tmp_path, monkeypatch, capsys):
    output = tmp_path / "summary.scad"
    summary = tmp_path / "run-summary.json"
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
        calendar_days_per_row=12,
        json=str(summary),
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=12: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "//"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# materials")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)

    cli.main()

    assert summary.exists()
    data = json.loads(summary.read_text())
    assert data["outputs"]
    monthly = next(entry for entry in data["outputs"] if entry["kind"] == "monthly")
    assert monthly["scad"] == str(output)
    assert monthly["metadata"].endswith("run-summary.json") is False
    captured = capsys.readouterr().out
    assert f"Wrote {summary}" in captured


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
        calendar_days_per_row=5,
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
    readme_text = (tmp_path / "stl" / "2021" / "README.md").read_text()
    assert "[`baseplate_2x6.scad`](baseplate_2x6.scad)" in readme_text
    assert "[`baseplate_2x6.stl`](baseplate_2x6.stl)" not in readme_text
    calendar_dir = tmp_path / "stl" / "2021" / calendar_slug(args.calendar_days_per_row)
    assert len(list(calendar_dir.glob("*.scad"))) == 12


def test_cli_forwards_calendar_days_per_row(tmp_path, monkeypatch):
    base = tmp_path / "out.scad"
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
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=7,
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )

    seen: dict[str, int] = {}

    def fake_calendars(daily, year, *, days_per_row: int):
        seen["days_per_row"] = days_per_row
        return {m: "//" for m in range(1, 13)}

    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", fake_calendars)
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    assert seen["days_per_row"] == 7


def test_cli_defaults_calendar_width_to_months_per_row(tmp_path, monkeypatch):
    """Docs promise calendar exports follow the monthly grid when not overridden."""

    base = tmp_path / "auto.scad"
    argv = [
        "user",
        "--output",
        str(base),
        "--start-year",
        "2021",
        "--end-year",
        "2021",
        "--months-per-row",
        "8",
    ]

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *_args, **_kwargs: [{"created_at": "2021-01-15T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly",
        lambda _counts, months_per_row=12: "// monthly",
    )
    calendar_capture: dict[str, int] = {}

    def fake_calendars(_daily, year, *, days_per_row):
        calendar_capture["year"] = year
        calendar_capture["days_per_row"] = days_per_row
        return {month: "//" for month in range(1, 13)}

    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        fake_calendars,
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *_args, **_kwargs: None)

    captured_slug: dict[str, str] = {}

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
        captured_slug["year"] = year
        captured_slug["slug"] = calendar_slug
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# placeholder", encoding="utf-8")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)

    cli.main(argv)

    assert calendar_capture == {"year": 2021, "days_per_row": 8}
    assert captured_slug["slug"] == calendar_slug(8)

    year_dir = tmp_path / "stl" / "2021"
    assert (year_dir / calendar_slug(8)).is_dir()
    assert not (year_dir / calendar_slug(5)).exists()


def test_cli_writes_calendars_to_dynamic_slug(tmp_path, monkeypatch):
    base = tmp_path / "out.scad"
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
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=7,
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )

    def fallback_calendars(daily, year, *, days_per_row):
        return {m: "//" for m in range(1, 13)}

    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", fallback_calendars)
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    expected_slug = calendar_slug(args.calendar_days_per_row)
    calendar_dir = year_dir / expected_slug
    assert calendar_dir.exists(), "Expected calendars to live in slugged directory"
    assert not (year_dir / calendar_slug()).exists(), "Default slug should not persist"

    readme_text = (year_dir / "README.md").read_text()
    assert expected_slug in readme_text


def test_cli_removes_stale_calendar_directory(tmp_path, monkeypatch):
    base = tmp_path / "out.scad"
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
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=4,
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    year_dir = tmp_path / "stl" / "2021"
    stale_dir = year_dir / calendar_slug()
    stale_dir.mkdir(parents=True)
    (stale_dir / "stale.scad").write_text("// stale")

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    assert not stale_dir.exists(), "Old calendar directory should be removed"
    new_dir = year_dir / calendar_slug(args.calendar_days_per_row)
    assert new_dir.exists(), "Expected new calendar directory to be created"


def test_cli_removes_stale_calendar_file(tmp_path, monkeypatch):
    base = tmp_path / "out.scad"
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
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=7,
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    year_dir = tmp_path / "stl" / "2021"
    stale_file = year_dir / calendar_slug()
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.write_text("// stale file")

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    assert not stale_file.exists(), "Old calendar file should be removed"
    new_dir = year_dir / calendar_slug(args.calendar_days_per_row)
    assert new_dir.exists(), "Expected new calendar directory to be created"


def test_cleanup_calendar_directories_preserves_requested_slug(tmp_path):
    keep = tmp_path / calendar_slug()
    keep.mkdir()
    (keep / "keep.txt").write_text("keep")

    stale_dir = tmp_path / "monthly-4x6"
    stale_dir.mkdir()
    stale_file = tmp_path / "monthly-7x6"
    stale_file.write_text("stale")

    cli._cleanup_calendar_directories(tmp_path, keep.name)

    assert keep.exists(), "Expected keep slug to remain"
    assert (keep / "keep.txt").exists()
    assert not stale_dir.exists()
    assert not stale_file.exists()


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
    calendar_dir = tmp_path / "stl" / "2021" / calendar_slug()
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
    scad3 = tmp_path / "c_color3.scad"
    per_year_baseplate = tmp_path / "stl" / "2021" / "baseplate_2x6.scad"
    baseplate_scad = tmp_path / "c_baseplate.scad"
    stl1 = tmp_path / "c_color1.stl"
    stl2 = tmp_path / "c_color2.stl"
    stl3 = tmp_path / "c_color3.stl"
    baseplate_stl = tmp_path / "c_baseplate.stl"
    scad1_text = scad1.read_text()
    scad2_text = scad2.read_text()
    scad3_text = scad3.read_text()
    assert "L1" in scad1_text
    assert "L2" in scad2_text
    assert "L3" in scad3_text
    reserved = "// 2021-01 (0 contributions) reserved at [0, 0]"
    assert reserved in scad1_text
    assert reserved in scad2_text
    assert reserved in scad3_text
    assert baseplate_scad.read_text() == "// Baseplate"
    assert per_year_baseplate.exists()
    assert len(stl_calls) == 5
    assert stl_calls[0][0].resolve() == per_year_baseplate.resolve()
    assert stl_calls[1][0].resolve() == baseplate_scad.resolve()
    assert stl_calls[2][0].resolve() == scad1.resolve()
    assert stl_calls[3][0].resolve() == scad2.resolve()
    assert stl_calls[4][0].resolve() == scad3.resolve()
    calendar_dir = tmp_path / "stl" / "2021" / calendar_slug()
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    captured = capsys.readouterr()
    assert f"Wrote {baseplate_scad}" in captured.out
    assert f"Wrote {scad1}" in captured.out


def test_cli_two_color_palette_writes_two_color_files(tmp_path, monkeypatch):
    """`--colors 2` should emit two block files as documented in the CLI matrix."""

    base = tmp_path / "palette.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(tmp_path / "palette.stl"),
        colors=2,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )

    def fake_levels(counts, months_per_row=12):
        return {
            1: "// Generated by g\nL1",
            2: "// Generated by g\nL2",
        }

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    color1 = tmp_path / "palette_color1.scad"
    color2 = tmp_path / "palette_color2.scad"
    assert color1.exists(), "First color file should be generated"
    assert color2.exists(), "Second color file should be generated"

    assert "L1" in color1.read_text()
    assert "L2" in color2.read_text()

    rendered = {dest.name for _, dest in stl_calls}
    assert "palette_color1.stl" in rendered
    assert "palette_color2.stl" in rendered


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    stale_baseplate_stl = tmp_path / "annotated_baseplate.stl"
    stale_baseplate_stl.write_text("old mesh")

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
    assert (
        not stale_baseplate_stl.exists()
    ), "Multi-color baseplate STL should be removed"


def test_cli_multicolor_writes_placeholders_for_empty_data(tmp_path, monkeypatch):
    """Multi-color runs should still emit placeholder `_colorN` files with zero notes."""

    base = tmp_path / "empty.scad"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2024,
        end_year=2024,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=4,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: [])
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    color_files = sorted(tmp_path.glob("empty_color*.scad"))
    assert [path.name for path in color_files] == [
        "empty_color1.scad",
        "empty_color2.scad",
        "empty_color3.scad",
        "empty_color4.scad",
    ]
    expected_comment = "// 2024-01 (0 contributions) reserved at [0, 0]"
    for path in color_files:
        text = path.read_text()
        assert text.startswith("// Generated by gitshelves")
        assert expected_comment in text
        assert "translate([" not in text, "Placeholder should not include geometry"


def test_cli_multicolor_removes_stale_color_stls(tmp_path, monkeypatch):
    """Empty multi-color runs should clean up stale color STLs (docs promise)."""

    base = tmp_path / "empty.scad"
    stl_target = tmp_path / "empty.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2024,
        end_year=2024,
        output=str(base),
        months_per_row=12,
        stl=str(stl_target),
        colors=4,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: [])
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )

    # Pretend a previous run generated color STLs that should now be removed.
    stale_paths = [
        tmp_path / "empty_color1.stl",
        tmp_path / "empty_color2.stl",
        tmp_path / "empty_color3.stl",
        tmp_path / "empty_color4.stl",
    ]
    for path in stale_paths:
        path.write_text("// stale")

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    for path in stale_paths:
        assert not path.exists(), "Stale color STLs should be removed"

    # Only baseplates should be rendered when no color geometry exists.
    rendered_names = {dest.name for _, dest in stl_calls}
    assert "empty_baseplate.stl" in rendered_names
    assert any(name.endswith("baseplate_2x6.stl") for name in rendered_names)
    assert all("color" not in name for name in rendered_names)


def test_cli_multicolor_drops_stale_files_when_palette_shrinks(tmp_path, monkeypatch):
    """Shrinking the palette should remove stale `_colorN` outputs (README promise)."""

    base = tmp_path / "multi.scad"
    stl_target = tmp_path / "multi.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2024,
        end_year=2024,
        output=str(base),
        months_per_row=12,
        stl=str(stl_target),
        colors=2,
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
        lambda *a, **k: [{"created_at": "2024-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )

    def fake_levels(counts, months_per_row=12):
        return {1: "// Generated by gitshelves\ntranslate([0, 0, 0]) cube(10);"}

    monkeypatch.setattr(cli, "generate_scad_monthly_levels", fake_levels)
    monkeypatch.setattr(
        cli, "generate_zero_month_annotations", lambda counts, months_per_row=12: []
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )

    for idx in (2, 3):
        (tmp_path / f"multi_color{idx}.scad").write_text("// stale scad")
        (tmp_path / f"multi_color{idx}.stl").write_text("stale stl")

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))
        Path(dest).write_text("generated")

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    color_one_scad = tmp_path / "multi_color1.scad"
    color_one_stl = tmp_path / "multi_color1.stl"
    assert color_one_scad.exists(), "Current palette should still produce color1"
    assert color_one_stl.exists(), "Color1 STL should be regenerated"

    color_two_scad = tmp_path / "multi_color2.scad"
    assert color_two_scad.exists(), "Palette should retain the second color file"
    assert not (
        tmp_path / "multi_color2.stl"
    ).exists(), "Stale color2 STL should be removed"
    assert not (tmp_path / "multi_color3.scad").exists()
    assert not (tmp_path / "multi_color3.stl").exists()


def test_cli_multicolor_writes_placeholders_for_unused_groups(tmp_path, monkeypatch):
    """Requested color groups should always be present to keep file sets predictable."""

    base = tmp_path / "multi.scad"
    stl_target = tmp_path / "multi.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2024,
        end_year=2024,
        output=str(base),
        months_per_row=12,
        stl=str(stl_target),
        colors=4,
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
        lambda *a, **k: [{"created_at": "2024-01-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {
            month: "// calendar" for month in range(1, 13)
        },
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly_levels",
        lambda counts, months_per_row=12: {
            1: "// Generated by gitshelves\ntranslate([0, 0, 0]) cube(10);"
        },
    )
    zero_annotation = "// zero note"
    monkeypatch.setattr(
        cli,
        "generate_zero_month_annotations",
        lambda counts, months_per_row=12: [zero_annotation],
    )

    stale_paths = [tmp_path / f"multi_color{idx}.stl" for idx in (2, 3)]
    for path in stale_paths:
        path.write_text("// stale")

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    color_paths = [tmp_path / f"multi_color{idx}.scad" for idx in (1, 2, 3, 4)]
    for path in color_paths:
        assert path.exists(), f"Expected placeholder for {path.name}"
        text = path.read_text()
        assert text.startswith("// Generated by gitshelves")
        assert zero_annotation in text

    assert "translate([" in color_paths[0].read_text()
    for placeholder in color_paths[1:]:
        text = placeholder.read_text()
        assert "translate([" not in text, "Unused groups should remain geometry-free"

    for path in stale_paths:
        assert not path.exists(), "Unused color STLs should be removed"

    rendered_sources = {src.name for src, _ in stl_calls}
    assert "multi_color1.scad" in rendered_sources
    assert "multi_color2.scad" not in rendered_sources
    assert "multi_color3.scad" not in rendered_sources
    assert "multi_color4.scad" not in rendered_sources


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

    def fake_calendars(daily, year, *, days_per_row):
        return {m: "//" for m in range(1, 13)}

    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", fake_calendars)

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
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
    scad_module = cli._scad_module()
    real_group = scad_module.group_scad_levels_with_mapping

    def capture_groups(levels, groups):
        groups_seen["value"] = groups
        return real_group(levels, groups)

    monkeypatch.setattr(scad_module, "group_scad_levels_with_mapping", capture_groups)

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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
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

    scad_module = cli._scad_module()

    def fake_group(levels, groups):
        captured["groups"] = groups
        assert levels == {1: "// Generated by gitshelves\nL"}
        return {1: "// Generated by gitshelves\nG"}, {1: [1]}

    monkeypatch.setattr(scad_module, "group_scad_levels_with_mapping", fake_group)

    called = []
    monkeypatch.setattr(cli, "scad_to_stl", lambda s, d: called.append((s, d)))
    monkeypatch.setattr(
        cli,
        "write_year_readme",
        lambda y, c, extras=None, include_baseplate_stl=False, calendar_slug=calendar_slug(): tmp_path
        / "dummy",
    )

    cli.main()

    scad = tmp_path / "m_color1.scad"
    baseplate_scad = tmp_path / "m_baseplate.scad"
    text = scad.read_text()
    assert text.startswith("// Generated by gitshelves\nG")
    assert "// 2021-01 (0 contributions) reserved" in text
    assert baseplate_scad.read_text() == "// Baseplate"
    assert called == []
    calendar_dir = tmp_path / calendar_slug()
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    out = capsys.readouterr().out
    assert f"Wrote {baseplate_scad}" in out
    assert f"Wrote {scad}" in out
    assert captured["groups"] == 3


def test_cli_multi_color_removes_stale_color_files(tmp_path, monkeypatch):
    """README promises palette shrinks drop stale `_colorN` outputs."""

    base = tmp_path / "palette.scad"
    stl_target = tmp_path / "palette.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(stl_target),
        colors=3,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    # Simulate a previous four-color run that left stale artifacts behind.
    for idx in (3, 4):
        (tmp_path / f"palette_color{idx}.scad").write_text("// old")
        (tmp_path / f"palette_color{idx}.stl").write_text("binary", encoding="utf-8")

    entries = [
        {"created_at": "2021-02-01T00:00:00Z"},
        {"created_at": "2021-03-01T00:00:00Z"},
    ]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly_levels",
        lambda counts, months_per_row=12: {
            1: "// Generated by gitshelves\nL1",
            2: "// Generated by gitshelves\nL2",
        },
    )
    monkeypatch.setattr(
        cli,
        "group_scad_levels",
        lambda levels, groups: {
            1: "// Generated by gitshelves\nG1",
            2: "// Generated by gitshelves\nG2",
        },
    )
    monkeypatch.setattr(
        cli,
        "generate_zero_month_annotations",
        lambda counts, months_per_row=12: [],
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "_write_year_baseplate", lambda *a, **k: None)

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
        path = tmp_path / "stl" / str(year) / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# materials")
        return path

    monkeypatch.setattr(cli, "write_year_readme", fake_write_year_readme)

    def fake_scad_to_stl(src, dest):
        Path(dest).write_text("stl", encoding="utf-8")

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    assert (tmp_path / "palette_color3.scad").exists()
    assert not (tmp_path / "palette_color4.scad").exists()
    assert not (tmp_path / "palette_color3.stl").exists()
    assert not (tmp_path / "palette_color4.stl").exists()
    assert (tmp_path / "palette_color1.scad").exists()
    assert (tmp_path / "palette_color2.scad").exists()
    assert (tmp_path / "palette_color1.stl").exists()
    assert (tmp_path / "palette_color2.stl").exists()


def test_cli_multi_color_without_stl_removes_lingering_color_meshes(
    tmp_path, monkeypatch
):
    """README promises non-STL runs delete leftover `_colorN.stl` meshes."""

    base = tmp_path / "nostl.scad"
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

    for idx in (1, 2, 3):
        (tmp_path / f"nostl_color{idx}.stl").write_text("old", encoding="utf-8")

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly_levels",
        lambda counts, months_per_row=12: {
            1: "// Generated by gitshelves\nL1",
            2: "// Generated by gitshelves\nL2",
        },
    )
    monkeypatch.setattr(
        cli,
        "group_scad_levels",
        lambda levels, groups: {
            1: "// Generated by gitshelves\nG1",
            2: "// Generated by gitshelves\nG2",
        },
    )
    monkeypatch.setattr(
        cli,
        "generate_zero_month_annotations",
        lambda counts, months_per_row=12: [],
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "_write_year_baseplate", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "write_year_readme",
        lambda year, counts, extras=None, include_baseplate_stl=False, calendar_slug=calendar_slug(): tmp_path
        / "stl"
        / str(year)
        / "README.md",
    )

    cli.main()

    assert not any(tmp_path.glob("nostl_color*.stl"))
    assert (tmp_path / "nostl_color1.scad").exists()
    assert (tmp_path / "nostl_color2.scad").exists()
    assert (tmp_path / "nostl_color3.scad").exists()


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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

    def fake_write_year_readme(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
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

    def fake_write(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
        called_years.append(year)
        return tmp_path / str(year) / "README.md"

    monkeypatch.setattr(cli, "write_year_readme", fake_write)

    cli.main()

    assert called_years == [2021, 2022, 2023]
    assert base.read_text() == "SCAD"
    for year in (2021, 2022, 2023):
        calendar_dir = tmp_path / str(year) / calendar_slug()
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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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


def test_cli_removes_stale_baseplate_stl(tmp_path, monkeypatch):
    """Stale baseplate meshes should disappear when --stl is omitted."""

    output = tmp_path / "chart.scad"
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
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: [])
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )

    def forbidden_scad_to_stl(*_args, **_kwargs):  # pragma: no cover - guard
        raise AssertionError("scad_to_stl should not run without --stl")

    monkeypatch.setattr(cli, "scad_to_stl", forbidden_scad_to_stl)

    year_dir = tmp_path / "stl" / "2021"
    year_dir.mkdir(parents=True, exist_ok=True)
    stale_stl = year_dir / "baseplate_2x6.stl"
    stale_stl.write_text("old mesh")

    cli.main()

    baseplate_scad = year_dir / "baseplate_2x6.scad"
    assert baseplate_scad.exists(), "Baseplate SCAD should be regenerated"
    assert not stale_stl.exists(), "Stale baseplate STL should be removed"


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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

    def fake_write(
        year,
        counts,
        extras=None,
        *,
        include_baseplate_stl=False,
        calendar_slug=calendar_slug(),
    ):
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
    calendar_dir = tmp_path / "2042" / calendar_slug()
    assert len(list(calendar_dir.glob("*.scad"))) == 12
    january = calendar_dir / "01_january.scad"
    january_text = january.read_text()
    assert "// Generated by gitshelves" in january_text
    assert "// 2042-01-01 (0 contributions) reserved at [0, 0]" in january_text


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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
    layout_metadata = json.loads(layout_path.with_suffix(".json").read_text())
    assert layout_metadata["kind"] == "gridfinity-layout"
    assert layout_metadata["details"]["columns"] == 4
    assert layout_metadata["stl_generated"] is False
    assert layout_metadata["stl"] is None
    captured = capsys.readouterr().out
    assert f"Wrote {layout_path.relative_to(tmp_path)}" in captured


def test_cli_gridfinity_readme_lists_footprint(
    tmp_path, monkeypatch, gridfinity_library
):
    """README extras should note the Gridfinity footprint (docs highlight columns)."""

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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    cli.main()

    readme_path = tmp_path / "stl" / "2021" / "README.md"
    text = readme_path.read_text()
    assert "Gridfinity layout" in text
    assert "4×3 grid" in text
    assert "gridfinity_plate.scad" in text


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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


def test_cli_rejects_non_positive_months_per_row(tmp_path, monkeypatch, capsys):
    """`--months-per-row` should fail fast for non-positive values."""

    monkeypatch.chdir(tmp_path)

    fetch_mock = Mock(name="fetch_user_contributions")
    monthly_mock = Mock(name="generate_monthly_calendar_scads")
    scad_mock = Mock(name="generate_scad_monthly")

    monkeypatch.setattr(cli, "fetch_user_contributions", fetch_mock)
    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", monthly_mock)
    monkeypatch.setattr(cli, "generate_scad_monthly", scad_mock)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "user",
                "--months-per-row",
                "0",
            ]
        )

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "--months-per-row must be positive" in captured.err

    fetch_mock.assert_not_called()
    monthly_mock.assert_not_called()
    scad_mock.assert_not_called()


def test_cli_rejects_non_positive_calendar_days_per_row(tmp_path, monkeypatch, capsys):
    """`--calendar-days-per-row` should reject non-positive values."""

    monkeypatch.chdir(tmp_path)

    fetch_mock = Mock(name="fetch_user_contributions")
    monthly_mock = Mock(name="generate_monthly_calendar_scads")
    scad_mock = Mock(name="generate_scad_monthly")

    monkeypatch.setattr(cli, "fetch_user_contributions", fetch_mock)
    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", monthly_mock)
    monkeypatch.setattr(cli, "generate_scad_monthly", scad_mock)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "user",
                "--calendar-days-per-row",
                "0",
            ]
        )

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "--calendar-days-per-row must be positive" in captured.err

    fetch_mock.assert_not_called()
    monthly_mock.assert_not_called()
    scad_mock.assert_not_called()


def test_cli_rejects_non_positive_gridfinity_columns(tmp_path, monkeypatch, capsys):
    """`--gridfinity-columns` should reject non-positive values before running."""

    monkeypatch.chdir(tmp_path)

    fetch_mock = Mock(name="fetch_user_contributions")
    monthly_mock = Mock(name="generate_monthly_calendar_scads")
    scad_mock = Mock(name="generate_scad_monthly")
    gridfinity_mock = Mock(name="generate_gridfinity_plate_scad")

    monkeypatch.setattr(cli, "fetch_user_contributions", fetch_mock)
    monkeypatch.setattr(cli, "generate_monthly_calendar_scads", monthly_mock)
    monkeypatch.setattr(cli, "generate_scad_monthly", scad_mock)
    monkeypatch.setattr(cli, "generate_gridfinity_plate_scad", gridfinity_mock)

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

    fetch_mock.assert_not_called()
    monthly_mock.assert_not_called()
    scad_mock.assert_not_called()
    gridfinity_mock.assert_not_called()


def test_cli_generates_gridfinity_cube_stls_without_global_flag(
    tmp_path, monkeypatch, gridfinity_library
):
    """README promises cube STLs render even when `--stl` is omitted."""
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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    recorded_levels = []

    def fake_cube_stack(levels):
        recorded_levels.append(levels)
        return f"// cubes {levels}"

    monkeypatch.setattr(cli, "generate_contrib_cube_stack_scad", fake_cube_stack)

    scad_to_stl_calls: list[tuple[str, str]] = []

    def fake_stl(src, dest):
        scad_to_stl_calls.append((Path(src).name, Path(dest).name))
        Path(dest).write_text("STL")

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    assert not (year_dir / "contrib_cube_01.scad").exists()
    feb_scad = year_dir / "contrib_cube_02.scad"
    apr_scad = year_dir / "contrib_cube_04.scad"
    assert feb_scad.read_text() == "// cubes 2"
    assert apr_scad.read_text() == "// cubes 1"
    assert recorded_levels == [2, 1]
    assert scad_to_stl_calls
    assert (year_dir / "contrib_cube_02.stl").read_text() == "STL"
    assert (year_dir / "contrib_cube_04.stl").read_text() == "STL"


def test_cli_generates_gridfinity_cube_stls_when_requested(
    tmp_path, monkeypatch, gridfinity_library
):
    """`--gridfinity-cubes` should render STLs when `--stl` is provided."""

    base = tmp_path / "grid.scad"
    stl_base = tmp_path / "grid.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=str(stl_base),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=True,
        baseplate_template="baseplate_2x6.scad",
    )

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [
            {"created_at": "2021-02-01T00:00:00Z"},
            {"created_at": "2021-02-02T00:00:00Z"},
        ],
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))
        Path(dest).write_text("STL")

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    cube_scad = year_dir / "contrib_cube_02.scad"
    cube_stl = year_dir / "contrib_cube_02.stl"
    assert cube_scad.read_text() == "// cubes 1"
    assert cube_stl.read_text() == "STL"
    assert any("contrib_cube_02.scad" in str(src) for src, _ in stl_calls)

    readme_text = (tmp_path / "stl" / "2021" / "README.md").read_text()
    assert "- Gridfinity cubes: Feb, Apr (SCAD + STL)" in readme_text


def test_cube_month_from_path_edge_cases():
    """Helper should ignore filenames that are not valid month encodings."""

    assert cli._cube_month_from_path(Path("contrib_cube_02.scad")) == 2
    assert cli._cube_month_from_path(Path("contrib_cube_00.scad")) is None
    assert cli._cube_month_from_path(Path("contrib_cube_13")) is None
    assert cli._cube_month_from_path(Path("README")) is None


def test_cube_month_from_path_value_error(monkeypatch):
    """Defensive guard should handle unexpected integer conversion failures."""

    class FakeMatch:
        def group(
            self, index: int
        ) -> str:  # pragma: no cover - signature documentation
            return "oops"

    class FakePattern:
        def match(self, _: str) -> FakeMatch:
            return FakeMatch()

    monkeypatch.setattr(cli, "_CUBE_FILE_PATTERN", FakePattern())

    assert cli._cube_month_from_path(Path("contrib_cube_02.scad")) is None


def test_cleanup_gridfinity_cube_outputs(tmp_path):
    """Cleanup should drop stale months while respecting active ones."""

    stale_scad = tmp_path / "contrib_cube_01.scad"
    stale_scad.write_text("// old")
    stale_scad.with_suffix(".json").write_text("{}")
    keep_scad = tmp_path / "contrib_cube_02.scad"
    keep_scad.write_text("// new")
    keep_scad.with_suffix(".json").write_text("{}")
    ignored_scad = tmp_path / "contrib_cube_extra.scad"
    ignored_scad.write_text("// other")

    stale_stl = tmp_path / "contrib_cube_03.stl"
    stale_stl.write_text("stale")
    keep_stl = tmp_path / "contrib_cube_02.stl"
    keep_stl.write_text("fresh")
    ignored_stl = tmp_path / "contrib_cube_misc.stl"
    ignored_stl.write_text("misc")

    cli._cleanup_gridfinity_cube_outputs(tmp_path, {2}, remove_stls=False)

    assert not stale_scad.exists()
    assert not stale_scad.with_suffix(".json").exists()
    assert keep_scad.exists()
    assert keep_scad.with_suffix(".json").exists()
    assert ignored_scad.exists(), "Non-matching filenames should be preserved"
    assert not stale_stl.exists()
    assert keep_stl.exists()
    assert ignored_stl.exists()

    # With ``remove_stls`` true even active month STLs are cleared.
    keep_stl.write_text("fresh")
    cli._cleanup_gridfinity_cube_outputs(tmp_path, {2}, remove_stls=True)
    assert not keep_stl.exists()


def test_cli_gridfinity_cubes_remove_stale_files(
    tmp_path, monkeypatch, gridfinity_library
):
    """Old Gridfinity cube files should be removed when months lose activity."""

    base = tmp_path / "stacks.scad"
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

    year_dir = tmp_path / "stl" / "2021"
    year_dir.mkdir(parents=True, exist_ok=True)
    stale_scad = year_dir / "contrib_cube_01.scad"
    stale_scad.write_text("// old january")
    stale_stl = year_dir / "contrib_cube_01.stl"
    stale_stl.write_text("old stl")
    keep_scad = year_dir / "contrib_cube_02.scad"
    keep_scad.write_text("// old february")
    keep_stl = year_dir / "contrib_cube_02.stl"
    keep_stl.write_text("old stl")

    monkeypatch.setattr(
        cli,
        "fetch_user_contributions",
        lambda *a, **k: [{"created_at": "2021-02-01T00:00:00Z"}],
    )
    monkeypatch.setattr(
        cli,
        "generate_scad_monthly",
        lambda counts, months_per_row=12: "// monthly",
    )
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily_counts, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli,
        "generate_contrib_cube_stack_scad",
        lambda levels: f"// cubes {levels}",
    )

    def fake_scad_to_stl(src, dest):
        Path(dest).write_text("new stl")

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    assert not stale_scad.exists()
    assert not stale_stl.exists()

    new_scad = year_dir / "contrib_cube_02.scad"
    assert "// cubes" in new_scad.read_text()

    new_stl = year_dir / "contrib_cube_02.stl"
    assert new_stl.read_text() == "new stl"


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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


def test_cli_removes_stale_gridfinity_cube_exports(
    tmp_path, monkeypatch, gridfinity_library
):
    """Gridfinity cube runs should clean up stale SCAD/STL files for empty months."""

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

    entries = [{"created_at": "2021-02-01T00:00:00Z"}]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli,
        "generate_contrib_cube_stack_scad",
        lambda levels: f"// cubes {levels}",
    )

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    year_dir = tmp_path / "stl" / "2021"
    year_dir.mkdir(parents=True, exist_ok=True)
    stale_scad = year_dir / "contrib_cube_01.scad"
    stale_stl = stale_scad.with_suffix(".stl")
    stale_scad.write_text("// stale")
    stale_stl.write_text("binary")

    cli.main()

    assert not stale_scad.exists()
    assert not stale_stl.exists()

    feb_scad = year_dir / "contrib_cube_02.scad"
    assert feb_scad.read_text() == "// cubes 1"
    assert any(dest.name == "contrib_cube_02.stl" for _src, dest in stl_calls)


def test_cli_cleans_up_gridfinity_layout_when_flag_disabled(
    tmp_path, monkeypatch, gridfinity_library
):
    """Existing layout files should be removed when `--gridfinity-layouts` isn't used."""

    output = tmp_path / "grid.scad"
    stl_target = tmp_path / "grid.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=str(stl_target),
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    entries = [{"created_at": "2021-01-01T00:00:00Z"}]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )

    year_dir = tmp_path / "stl" / "2021"
    year_dir.mkdir(parents=True, exist_ok=True)
    layout_scad = year_dir / "gridfinity_plate.scad"
    layout_stl = layout_scad.with_suffix(".stl")
    layout_scad.write_text("// stale layout")
    layout_stl.write_text("binary")
    layout_scad.with_suffix(".json").write_text("{}")

    stl_calls: list[tuple[Path, Path]] = []

    def fake_scad_to_stl(src, dest):
        stl_calls.append((Path(src), Path(dest)))

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    assert not layout_scad.exists(), "Old layout SCAD should be removed"
    assert not layout_scad.with_suffix(".json").exists()
    assert not layout_stl.exists(), "Old layout STL should be removed"
    rendered = {dest.name for _, dest in stl_calls}
    assert "gridfinity_plate.stl" not in rendered
    assert (tmp_path / "grid.scad").exists()


def test_cli_cleans_up_gridfinity_cubes_when_flag_disabled(
    tmp_path, monkeypatch, gridfinity_library
):
    """Leftover cube stacks should disappear when `--gridfinity-cubes` is omitted."""

    output = tmp_path / "grid.scad"
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
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.chdir(tmp_path)

    entries = [{"created_at": "2021-02-01T00:00:00Z"}]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// Baseplate"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    year_dir = tmp_path / "stl" / "2021"
    year_dir.mkdir(parents=True, exist_ok=True)
    stale_scad = year_dir / "contrib_cube_02.scad"
    stale_stl = stale_scad.with_suffix(".stl")
    stale_scad.write_text("// stale cube")
    stale_stl.write_text("binary")
    stale_scad.with_suffix(".json").write_text("{}")

    cli.main()

    assert not stale_scad.exists(), "Cube SCAD should be removed when flag is absent"
    assert not stale_scad.with_suffix(".json").exists()
    assert not stale_stl.exists(), "Cube STL should be removed when flag is absent"


def test_cli_removes_gridfinity_layout_stl_when_stl_flag_dropped(
    tmp_path, monkeypatch, gridfinity_library
):
    """Gridfinity layout STLs should clear when `--stl` is omitted on reruns."""

    base = tmp_path / "grid.scad"
    stl_target = tmp_path / "grid.stl"
    args_with_stl = argparse.Namespace(
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
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=5,
    )
    args_without_stl = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(base),
        months_per_row=12,
        stl=None,
        colors=1,
        gridfinity_layouts=True,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
        calendar_days_per_row=5,
    )
    args_queue = [args_with_stl, args_without_stl]

    def fake_parse_args(self, *a, **k):
        return args_queue.pop(0)

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", fake_parse_args)
    monkeypatch.chdir(tmp_path)

    entries = [{"created_at": "2021-02-01T00:00:00Z"}]
    monkeypatch.setattr(cli, "fetch_user_contributions", lambda *a, **k: entries)
    monkeypatch.setattr(
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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
        cli, "load_baseplate_scad", lambda name="baseplate_2x6.scad": "// baseplate"
    )

    def fake_scad_to_stl(src, dest):
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text("binary")

    monkeypatch.setattr(cli, "scad_to_stl", fake_scad_to_stl)

    cli.main()

    year_dir = tmp_path / "stl" / "2021"
    layout_stl = year_dir / "gridfinity_plate.stl"
    assert layout_stl.exists()

    cli.main()

    assert not layout_stl.exists(), "Layout STL should be removed when not requested"
    layout_metadata = json.loads((year_dir / "gridfinity_plate.json").read_text())
    assert layout_metadata["stl_generated"] is False
    assert layout_metadata["stl"] is None


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
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
    assert "- Gridfinity cubes: Feb, Apr (SCAD + STL)" in text


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
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )

    cli.main()

    readme_path = tmp_path / "stl" / "2022" / "README.md"
    text = readme_path.read_text()
    assert "- Gridfinity cubes: none generated (no contributions)" in text


def test_cli_single_color_removes_stale_palette(tmp_path, monkeypatch):
    output = tmp_path / "chart.scad"
    stl_target = tmp_path / "chart.stl"
    args = argparse.Namespace(
        username="user",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
        months_per_row=12,
        stl=str(stl_target),
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
        cli,
        "generate_monthly_calendar_scads",
        lambda daily, year, days_per_row=5: {m: "//" for m in range(1, 13)},
    )
    monkeypatch.setattr(
        cli, "generate_scad_monthly", lambda counts, months_per_row=12: "SCAD"
    )
    monkeypatch.setattr(cli, "scad_to_stl", lambda *a, **k: None)

    stale_paths = [
        tmp_path / "chart_color1.scad",
        tmp_path / "chart_color2.scad",
        tmp_path / "chart_color3.stl",
        tmp_path / "chart_color4.stl",
    ]
    for path in stale_paths:
        path.write_text("stale")

    cli.main()

    assert output.read_text() == "SCAD"
    for path in stale_paths:
        assert not path.exists(), "Stale multi-color files should be removed"


def test_color_index_from_path_handles_invalid_values(tmp_path):
    valid = tmp_path / "example_color3.scad"
    valid.touch()
    assert cli._color_index_from_path(valid) == 3

    missing_digits = tmp_path / "example_color.scad"
    missing_digits.touch()
    assert cli._color_index_from_path(missing_digits) is None

    zero_index = tmp_path / "example_color0.scad"
    zero_index.touch()
    assert cli._color_index_from_path(zero_index) is None


def test_cleanup_color_outputs_removes_all_when_zero_groups(tmp_path):
    base_output = tmp_path / "palette"
    stale_scad = tmp_path / "palette_color2.scad"
    stale_stl = tmp_path / "palette_color2.stl"
    stale_scad.touch()
    stale_stl.touch()
    stale_scad.with_suffix(".json").touch()

    cli._cleanup_color_outputs(base_output, 0, stl_requested=True)

    assert not stale_scad.exists()
    assert not stale_scad.with_suffix(".json").exists()
    assert not stale_stl.exists()


def test_cleanup_color_outputs_ignores_negative_groups(tmp_path):
    base_output = tmp_path / "palette"
    base_output.touch()
    stale_scad = tmp_path / "palette_color2.scad"
    stale_stl = tmp_path / "palette_color2.stl"
    stale_scad.touch()
    stale_stl.touch()

    cli._cleanup_color_outputs(base_output, -1, stl_requested=True)

    assert stale_scad.exists()
    assert stale_stl.exists()


def test_cleanup_color_outputs_skips_invalid_indices(tmp_path):
    base_output = tmp_path / "colors"
    invalid_scad = tmp_path / "colors_color.scad"
    invalid_stl = tmp_path / "colors_colorNaN.stl"
    invalid_scad.touch()
    invalid_stl.touch()

    cli._cleanup_color_outputs(base_output, 2, stl_requested=True)

    assert invalid_scad.exists()
    assert invalid_stl.exists()


def test_cleanup_color_outputs_respects_palette_and_stl_request(tmp_path):
    base_output = tmp_path / "shades"
    keep_scad = tmp_path / "shades_color1.scad"
    remove_scad = tmp_path / "shades_color3.scad"
    remove_stl_no_request = tmp_path / "shades_color1.stl"
    remove_stl_extra_color = tmp_path / "shades_color4.stl"

    for path in [keep_scad, remove_scad, remove_stl_no_request, remove_stl_extra_color]:
        path.touch()
    keep_scad.with_suffix(".json").touch()
    remove_scad.with_suffix(".json").touch()

    cli._cleanup_color_outputs(base_output, 2, stl_requested=False)

    assert keep_scad.exists()
    assert keep_scad.with_suffix(".json").exists()
    assert not remove_scad.exists()
    assert not remove_scad.with_suffix(".json").exists()
    assert not remove_stl_no_request.exists()
    assert not remove_stl_extra_color.exists()


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
