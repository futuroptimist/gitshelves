import json

import pytest

from gitshelves.core.metadata import MetadataWriter


@pytest.fixture
def writer() -> MetadataWriter:
    counts = {(2021, 1): 0, (2021, 2): 10}
    daily = {(2021, 2, 1): 3, (2021, 2, 2): 7}
    return MetadataWriter(
        username="user",
        start_year=2021,
        end_year=2021,
        monthly_counts=counts,
        daily_counts=daily,
        months_per_row=12,
        calendar_days_per_row=5,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )


def test_metadata_writer_produces_monthly_and_daily_payload(writer: MetadataWriter):
    monthly = writer.monthly_contributions()
    assert monthly[0] == {"year": 2021, "month": 1, "count": 0, "blocks": 0}
    assert monthly[1]["blocks"] == 2  # 10 contributions -> 2 blocks

    february_daily = writer.daily_contributions(year=2021, month=2)
    assert {entry["day"] for entry in february_daily} == {1, 2}


def test_metadata_writer_daily_contributions_filters(writer: MetadataWriter):
    all_daily = writer.daily_contributions()
    assert len(all_daily) == 2
    assert all_daily[0]["day"] == 1

    yearly = writer.daily_contributions(year=2021)
    assert {entry["month"] for entry in yearly} == {2}

    assert writer.daily_contributions(year=2021, month=1) == []


def test_metadata_writer_writes_json(tmp_path, writer: MetadataWriter, capsys):
    scad_path = tmp_path / "example.scad"
    scad_path.write_text("// test")

    writer.write_scad(
        scad_path,
        kind="monthly",
        monthly_contributions=writer.monthly_contributions(),
        daily_contributions=writer.daily_contributions(year=2021, month=2),
    )

    metadata_path = scad_path.with_suffix(".json")
    assert metadata_path.exists()
    payload = json.loads(metadata_path.read_text())
    assert payload["kind"] == "monthly"
    assert payload["stl_generated"] is False
    assert payload["stl"] is None
    assert payload["colors"] == 1
    assert payload["color_groups"] == 1
    assert payload["zero_months"] == [{"year": 2021, "month": 1}]
    captured = capsys.readouterr().out
    assert f"Wrote {metadata_path}" in captured


def test_metadata_writer_unlink(tmp_path):
    scad_path = tmp_path / "sample.scad"
    json_path = scad_path.with_suffix(".json")
    json_path.write_text("{}")

    MetadataWriter.unlink_for(scad_path)

    assert not json_path.exists()


def test_metadata_writer_run_summary(tmp_path, writer: MetadataWriter, capsys):
    scad_path = tmp_path / "example.scad"
    scad_path.write_text("// test")

    writer.write_scad(
        scad_path,
        kind="monthly",
        monthly_contributions=writer.monthly_contributions(),
    )

    summary_path = tmp_path / "run.json"
    writer.write_run_summary(summary_path)

    payload = json.loads(summary_path.read_text())
    assert payload["outputs"]
    assert payload["color_groups"] == 1
    monthly_entry = next(
        (entry for entry in payload["outputs"] if entry["kind"] == "monthly"),
        None,
    )
    assert monthly_entry is not None
    assert monthly_entry["scad"] == str(scad_path)
    assert monthly_entry["metadata"] == str(scad_path.with_suffix(".json"))
    assert monthly_entry["color_groups"] == 1
    captured = capsys.readouterr().out
    assert f"Wrote {summary_path}" in captured


def test_metadata_writer_includes_gridfinity_rows_in_summary(tmp_path, capsys):
    counts = {(2025, month): 0 for month in range(1, 13)}
    writer = MetadataWriter(
        username="user",
        start_year=2025,
        end_year=2025,
        monthly_counts=counts,
        daily_counts={},
        months_per_row=12,
        calendar_days_per_row=12,
        colors=1,
        gridfinity_layouts=True,
        gridfinity_columns=4,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    scad_path = tmp_path / "gridfinity_plate.scad"
    scad_path.write_text("// gridfinity")
    writer.write_scad(scad_path, kind="gridfinity-layout")

    summary_path = tmp_path / "summary.json"
    writer.write_run_summary(summary_path)

    summary = json.loads(summary_path.read_text())
    assert summary["gridfinity"]["layouts"] is True
    assert summary["gridfinity"]["columns"] == 4
    assert summary["gridfinity"]["rows"] == 3
    captured = capsys.readouterr().out
    assert f"Wrote {summary_path}" in captured


def test_metadata_writer_includes_rows_without_layouts(tmp_path, capsys):
    counts = {(2026, month): 0 for month in range(1, 13)}
    writer = MetadataWriter(
        username="user",
        start_year=2026,
        end_year=2026,
        monthly_counts=counts,
        daily_counts={},
        months_per_row=12,
        calendar_days_per_row=12,
        colors=1,
        gridfinity_layouts=False,
        gridfinity_columns=3,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    scad_path = tmp_path / "example.scad"
    scad_path.write_text("// monthly")
    writer.write_scad(scad_path, kind="monthly")

    summary_path = tmp_path / "summary.json"
    writer.write_run_summary(summary_path)

    summary = json.loads(summary_path.read_text())
    assert summary["gridfinity"]["layouts"] is False
    assert summary["gridfinity"]["columns"] == 3
    assert summary["gridfinity"]["rows"] == 4
    captured = capsys.readouterr().out
    assert f"Wrote {summary_path}" in captured


def test_metadata_writer_color_groups_match_active_levels():
    counts = {(2022, month): 0 for month in range(1, 13)}
    counts[(2022, 2)] = 25  # two blocks
    counts[(2022, 3)] = 400  # three blocks
    writer = MetadataWriter(
        username="user",
        start_year=2022,
        end_year=2022,
        monthly_counts=counts,
        daily_counts={},
        months_per_row=12,
        calendar_days_per_row=12,
        colors=5,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    assert writer.color_groups == 2

    empty_counts = {(2023, month): 0 for month in range(1, 13)}
    empty_writer = MetadataWriter(
        username="user",
        start_year=2023,
        end_year=2023,
        monthly_counts=empty_counts,
        daily_counts={},
        months_per_row=12,
        calendar_days_per_row=12,
        colors=4,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    assert empty_writer.color_groups == 0


def test_metadata_writer_color_groups_disabled_with_no_colors():
    counts = {(2024, 1): 1}

    writer = MetadataWriter(
        username="user",
        start_year=2024,
        end_year=2024,
        monthly_counts=counts,
        daily_counts={},
        months_per_row=12,
        calendar_days_per_row=12,
        colors=0,
        gridfinity_layouts=False,
        gridfinity_columns=6,
        gridfinity_cubes=False,
        baseplate_template="baseplate_2x6.scad",
    )

    assert writer.color_groups == 0


def test_metadata_writer_includes_zero_months_in_color_metadata(
    tmp_path, writer: MetadataWriter
):
    scad_path = tmp_path / "color1.scad"
    scad_path.write_text("// color")

    writer.write_scad(
        scad_path,
        kind="monthly-color",
        color_index=1,
        monthly_contributions=writer.monthly_contributions(),
        daily_contributions=writer.daily_contributions(),
    )

    metadata_path = scad_path.with_suffix(".json")
    payload = json.loads(metadata_path.read_text())
    assert payload["zero_months"] == writer.zero_months()
