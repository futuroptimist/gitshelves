import argparse
from pathlib import Path

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

    def fake_generate(counts):
        assert counts == {(2021, 2): 2}
        return "SCAD"

    args = argparse.Namespace(
        username="user",
        token="tok",
        start_year=2021,
        end_year=2021,
        output=str(output),
    )

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)
    monkeypatch.setattr(cli, "fetch_user_contributions", fake_fetch)
    monkeypatch.setattr(cli, "generate_scad_monthly", fake_generate)

    cli.main()

    assert output.read_text() == "SCAD"
    assert fetched_args["params"] == ("user", "tok", 2021, 2021)
    captured = capsys.readouterr()
    assert f"Wrote {output}" in captured.out


def test_cli_runpy(tmp_path, monkeypatch):
    output = tmp_path / "file.scad"
    args = argparse.Namespace(
        username="u",
        token=None,
        start_year=2021,
        end_year=2021,
        output=str(output),
    )

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: args)

    import sys, types, runpy

    fetch_mod = types.ModuleType("gitshelves.fetch")

    def fake_fetch(*a, **k):
        return [{"created_at": "2021-01-01T00:00:00Z"}]

    fetch_mod.fetch_user_contributions = fake_fetch

    scad_mod = types.ModuleType("gitshelves.scad")

    def fake_generate(counts):
        assert counts == {(2021, 1): 1}
        return "DATA"

    scad_mod.generate_scad_monthly = fake_generate

    sys.modules["gitshelves.fetch"] = fetch_mod
    sys.modules["gitshelves.scad"] = scad_mod
    sys.modules.pop("gitshelves.cli", None)

    runpy.run_module("gitshelves.cli", run_name="__main__")

    assert output.read_text() == "DATA"
