// Gridfinity 2×6 baseplate: 256 × 88 mm outline, not physical-fit approval
use <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-holes.scad>;

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
            refined_hole = include_magnets && magnet_style == "gridfinity_refine",
            magnet_hole = include_magnets && magnet_style != "gridfinity_refine",
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
u_height = 6; // preserve the existing 6 mm border height

// Preserve 2 mm padding; the resulting 256 mm width has no spare bed margin.
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
    translate([-grid_x * l_grid / 2 - padding,
               -grid_y * l_grid / 2 - padding, 0])
        linear_extrude(height = u_height)
            difference() {
                square([grid_x * l_grid + 2 * padding,
                        grid_y * l_grid + 2 * padding]);
                translate([padding, padding])
                    square([grid_x * l_grid,
                            grid_y * l_grid]);
            }
}
