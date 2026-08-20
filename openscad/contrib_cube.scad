// openscad/contrib_cube.scad
// Dimensions cross-checked with vector76/gridfinity_openscad.
include <lib/gridfinity-rebuilt/src/core/standard.scad>;
use <lib/gridfinity-rebuilt/src/core/bin.scad>;
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-utility.scad>;
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-holes.scad>;

// A reusable, solid 1×1×1U module. The library's include_lip field preserves
// the vertical Gridfinity stacking interface; empty hole options omit magnets.
module_config = new_bin(
    grid_size = [1, 1],
    height_mm = fromGridfinityUnits(1),
    fill_height = 0,
    include_lip = true,
    hole_options = bundle_hole_options(
        refined_hole=false,
        magnet_hole=false,
        screw_hole=false,
        crush_ribs=false,
        chamfer=false,
        supportless=false
    )
);

bin_render(module_config);
