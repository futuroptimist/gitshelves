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
            translate([x, 0, thickness / 2])
                rotate([-90, 0, 0])
                    cylinder(h = depth, d = hole_d);
        for (x = [offset, length - offset])
            translate([x, 0, thickness / 2])
                rotate([-90, 0, 0])
                    cylinder(h = head_depth, d = head_d);
    }
}

shelf();
