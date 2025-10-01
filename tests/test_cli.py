import argparse
from pathlib import Path

import pytest

import gitshelves
import gitshelves.cli as cli


def test_cli_main(tmp_path, monkeypatch, capsys):
    output = tmp_path / "out.scad"

    fetched_args = {}

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
    )
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
    )

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
    )

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
    )

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )

    import sys, types, runpy

    fetch_mod = types.ModuleType("gitshelves.fetch")

    def fake_fetch(*a, **k):
        return [{"created_at": "2021-01-01T00:00:00Z"}]

    fetch_mod.fetch_user_contributions = fake_fetch

    scad_mod = types.ModuleType("gitshelves.scad")

    def fake_generate(counts, months_per_row=12):
        assert counts == {(2021, 1): 1}
        assert months_per_row == 12
        return "DATA"

    scad_mod.generate_scad_monthly = fake_generate
    scad_mod.generate_scad_monthly_levels = lambda counts, months_per_row=12: {}
    scad_mod.group_scad_levels = lambda levels, groups: {1: "G"}
    scad_mod.scad_to_stl = lambda a, b: None

    sys.modules["gitshelves.fetch"] = fetch_mod
    sys.modules["gitshelves.scad"] = scad_mod
    sys.modules.pop("gitshelves.cli", None)

    runpy.run_module("gitshelves.cli", run_name="__main__")

    assert output.read_text() == "DATA"


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
    )
    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, *a, **k: args
    )

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
    called = []

    def fake_stl(src, dest):
        called.append((src, dest))

    monkeypatch.setattr(cli, "scad_to_stl", fake_stl)

    cli.main()

    scad1 = tmp_path / "c_color1.scad"
    scad2 = tmp_path / "c_color2.scad"
    stl1 = tmp_path / "c_color1.stl"
    stl2 = tmp_path / "c_color2.stl"
    baseplate_scad = tmp_path / "c_baseplate.scad"
    baseplate_stl = tmp_path / "c_baseplate.stl"
    baseplate_src = (
        Path(__file__).resolve().parents[1] / "openscad" / "baseplate_2x6.scad"
    )

    assert scad1.read_text() == "// Generated by gitshelves\nL1\nL2"
    assert scad2.read_text() == "// Generated by gitshelves\nL3"
    assert baseplate_scad.read_text() == baseplate_src.read_text()
    assert called == [
        (str(scad1), str(stl1)),
        (str(scad2), str(stl2)),
        (str(baseplate_scad), str(baseplate_stl)),
    ]
    captured = capsys.readouterr()
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
    )
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)

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
    baseplate_src = (
        Path(__file__).resolve().parents[1] / "openscad" / "baseplate_2x6.scad"
    )

    assert scad.read_text() == "// Generated by gitshelves\nG"
    assert baseplate_scad.read_text() == baseplate_src.read_text()
    assert called == []
    out = capsys.readouterr().out
    assert f"Wrote {scad}" in out
    assert captured["groups"] == 2


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


def test_baseplate_source_reads_packaged_template():
    data = cli._baseplate_source()
    assert "Gridfinity 2×6 baseplate" in data


def test_baseplate_source_missing_template(monkeypatch):
    class FakePackage:
        class Missing:
            def is_file(self):
                return False

            def read_text(self):  # pragma: no cover - defensive guard
                raise AssertionError("read_text should not be called")

        def joinpath(self, name):
            return self.Missing()

    monkeypatch.setattr(cli.resources, "files", lambda _: FakePackage())

    with pytest.raises(FileNotFoundError):
        cli._baseplate_source()
