module draw_cone(R,n,h,thickness){
    difference(){
    cylinder(h=h, r1=R+thickness, r2=R+thickness, center=true, $fn=n);
    cylinder(h=h, r1=R, r2=R, center=true, $fn=n);
    cylinder(h=h, r1=R, r2=R, center=true, $fn=n);
    }
}

module draw_cut_boxes(R, n, thickness, slot_height, slot_width){
    union(){
        for (i=[0: n/2]){
            rotate(a=i*360/n, v=[0,0,1])
            cube([2*(R+thickness),slot_height,slot_width], center=true);
        }
    }
}

module draw_belt(R, n, h, thickness, slot_height, slot_width){
    difference(){
        rotate(a=180/n, v=[0,0,1]) draw_cone(R, n, h, thickness);
        draw_cut_boxes(R, n, thickness, slot_height, slot_width);
    }
}








