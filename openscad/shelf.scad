// Simple shelf with drywall mounting holes
// dimensions in millimeters

length = 180;
depth = 80;
thickness = 15;

hole_d = 5;
head_d = 9;
head_depth = 3;
offset = 20;

module shelf() {
    difference() {
        cube([length, depth, thickness]);
        for (x = [offset, length - offset])
            translate([x, depth / 2, 0])
                cylinder(h = thickness, d = hole_d);
        for (x = [offset, length - offset])
            translate([x, depth / 2, thickness - head_depth])
                cylinder(h = head_depth, d = head_d);
    }
}

shelf();
