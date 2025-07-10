from gitshelves.scad import blocks_for_contributions

def test_blocks_for_contributions():
    assert blocks_for_contributions(0) == 0
    assert blocks_for_contributions(1) == 1
    assert blocks_for_contributions(9) == 1
    assert blocks_for_contributions(10) == 2
    assert blocks_for_contributions(99) == 2
    assert blocks_for_contributions(100) == 3
