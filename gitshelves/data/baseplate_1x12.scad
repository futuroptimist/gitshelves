// Gridfinity 1×12 baseplate for tall single-row displays
use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

// Grid unit length (mm) from the Gridfinity specification
l_grid = 42;

units_x = 12;
units_y = 1;

// Toggle to drop magnet recesses when weight is low
include_magnets = true;

gridfinityBaseplate(
    [units_x, units_y],
    l_grid,
    [0, 0],
    0,
    bundle_hole_options(
        refined_hole = false,
        magnet_hole = include_magnets,
        screw_hole = false,
        crush_ribs = true,
        chamfer = true,
        supportless = false
    ),
    0,
    [0, 0]
);
