// Reusable 1×1×1U contribution module using the pinned Gridfinity-Rebuilt API.
// Product language calls this a cube; the exact module includes the standard
// base seating profile and regular stackable lip.
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-utility.scad>;
use <lib/gridfinity-rebuilt/src/core/gridfinity-rebuilt-holes.scad>;

hole_options = bundle_hole_options(
    refined_hole = false,
    magnet_hole = false,
    screw_hole = false,
    crush_ribs = false,
    chamfer = true,
    supportless = false
);

gridfinityInit(1, 1, height(1), 0, sl = 0) { // 1U, regular stackable lip
}
gridfinityBase([1, 1], hole_options = hole_options);
