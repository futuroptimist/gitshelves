// openscad/contrib_cube.scad
include <lib/gridfinity-rebuilt/gridfinity-rebuilt-bin.scad>;

bin(
    ux = 1, uy = 1, uh = 1,              // 1×1 base, 1 unit high
    walls = 1.2, floor = 1.6, lid = "none",
    magnet_pockets = false,              // cubes don’t need magnets
    stackable = true                     // preserves Gridfinity lip
);
