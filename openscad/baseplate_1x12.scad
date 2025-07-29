// openscad/baseplate_1x12.scad
// Render with:  openscad -o ../stl/YYYY/baseplate_1x12.stl $fn=120 baseplate_1x12.scad

use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

units_x = 12;
units_y = 1;

// zero means stock magnet pockets; set to false for lighter plates
include_magnets = true;

baseplate(
    ux = units_x,
    uy = units_y,
    magnet_pockets = include_magnets
);
