// openscad/baseplate_1x12.scad
// Render with:  openscad -o ../stl/YYYY/baseplate_1x12.stl $fn=120 baseplate_1x12.scad

use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

units_x = 12;
units_y = 1;

// Set to false for lighter plates
include_magnets = true;

gridfinityBaseplate(
    [units_x, units_y],
    l_grid,
    [0, 0],
    0,
    bundle_hole_options(
        refined_hole=false,
        magnet_hole=include_magnets,
        screw_hole=false,
        crush_ribs=true,
        chamfer=true,
        supportless=false
    ),
    0,
    [0, 0]
);
