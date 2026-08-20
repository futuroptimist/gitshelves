// Reusable 1×1 contribution module using the pinned Gridfinity-Rebuilt API.
// "Cube" is product language: the body is one 42 mm cell and one 7 mm unit,
// plus the library's existing seating base and stackable lip.
include <lib/gridfinity-rebuilt/src/core/standard.scad>;
use <lib/gridfinity-rebuilt/src/core/bin.scad>;
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-holes.scad>;

contribution_module = new_bin(
    grid_size = [1, 1],
    height_mm = 7,
    include_lip = true,
    hole_options = bundle_hole_options()
);

bin_render(contribution_module);
