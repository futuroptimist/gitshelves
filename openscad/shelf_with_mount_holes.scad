// Simple shelf with drywall mounting holes
width = 200;       // shelf width in mm
depth = 100;       // shelf depth in mm
thickness = 10;    // shelf thickness in mm
hole_diameter = 5; // screw hole diameter
hole_spacing = 160; // distance between holes
hole_offset = (width - hole_spacing) / 2;

difference() {
  cube([width, depth, thickness], center = false);
  translate([hole_offset, depth / 2, 0])
    cylinder(h = thickness, d = hole_diameter);
  translate([hole_offset + hole_spacing, depth / 2, 0])
    cylinder(h = thickness, d = hole_diameter);
}
