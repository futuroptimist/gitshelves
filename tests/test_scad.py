from gitshelves.scad import blocks_for_contributions, generate_scad_monthly


def test_blocks_for_contributions():
    assert blocks_for_contributions(0) == 0
    assert blocks_for_contributions(1) == 1
    assert blocks_for_contributions(9) == 1
    assert blocks_for_contributions(10) == 2
    assert blocks_for_contributions(99) == 2
    assert blocks_for_contributions(100) == 3


def test_generate_scad_monthly():
    counts = {
        (2021, 1): 1,
        (2022, 1): 10,
    }
    scad = generate_scad_monthly(counts)
    assert "translate([0, 0, 0]) cube(10);" in scad
    assert "translate([0, 12, 0]) cube(10);" in scad
    assert "translate([0, 12, 10]) cube(10);" in scad
