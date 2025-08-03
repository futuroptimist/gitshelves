// Gridfinity 2×6 baseplate for Bambu Lab A1 (fits 256 mm² bed)
include <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

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

// grid_x = columns, grid_y = rows
gridfinity_baseplate(grid_x = 6,
                     grid_y = 2,
                     u_height = 6,          // keep stock 6-U thickness
                     lip = true,            // stacking lip
                     magnet_style = "gridfinity_refine",
                     magnets_corners_only = false,
                     screw_holes = false);
