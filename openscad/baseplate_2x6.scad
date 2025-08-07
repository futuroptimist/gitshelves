// Gridfinity 2×6 baseplate for Bambu Lab A1 (fits 256 mm² bed)
use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

// Grid unit length (mm) from Gridfinity specification
l_grid = 42;

// Compatibility wrapper for gridfinityRebuilt's camelCase API
module gridfinity_baseplate(grid_x = 1,
                            grid_y = 1,
                            u_height = 6,
                            lip = true,
                            magnet_style = "gridfinity_refine",
                            magnets_corners_only = false,
                            screw_holes = false) {
    include_magnets = !magnets_corners_only;
    gridfinityBaseplate(
        [grid_x, grid_y],
        l_grid,
        [0, 0],
        0,
        bundle_hole_options(
            refined_hole = magnet_style == "gridfinity_refine",
            magnet_hole = include_magnets,
            screw_hole = screw_holes,
            crush_ribs = true,
            chamfer = true,
            supportless = false
        ),
        0,
        [0, 0]
    );
}

grid_x = 6;
grid_y = 2;
u_height = 6; // keep stock 6-U thickness

// Extra padding fits the 252 mm×84 mm grid into the A1's 256 mm square bed
padding = (256 - grid_x * l_grid) / 2;

union() {
    gridfinity_baseplate(grid_x = grid_x,
                         grid_y = grid_y,
                         u_height = u_height,
                         lip = true,            // stacking lip
                         magnet_style = "gridfinity_refine",
                         magnets_corners_only = false,
                         screw_holes = false);

    // border ring providing extra bed adhesion
    translate([-padding, -padding, 0])
        linear_extrude(height = u_height)
            difference() {
                square([grid_x * l_grid + 2 * padding,
                        grid_y * l_grid + 2 * padding]);
                translate([padding, padding])
                    square([grid_x * l_grid,
                            grid_y * l_grid]);
            }
}
