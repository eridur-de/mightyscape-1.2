include <Belt.scad>

// Input parameters
R = 35;
n = 8;
height = 7; // height of support
thickness = 1; // thickness of belt

// square cuts to be pierced by support ring
slot_height=3; // must be smaller than height
slot_width=3;

draw_belt(R, n, height, thickness, slot_height, slot_width);