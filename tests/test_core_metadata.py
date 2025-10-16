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
    assert payload["zero_months"] == [{"year": 2021, "month": 1}]
    captured = capsys.readouterr().out
    assert f"Wrote {metadata_path}" in captured


def test_metadata_writer_unlink(tmp_path):
    scad_path = tmp_path / "sample.scad"
    json_path = scad_path.with_suffix(".json")
    json_path.write_text("{}")

    MetadataWriter.unlink_for(scad_path)

    assert not json_path.exists()
