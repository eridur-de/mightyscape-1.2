#! /usr/bin/env python3
'''
Copyright (C) 2019 Grant Patterson <grant@revoltlabs.co>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

from math import copysign, cos, pi, sin
from inkex import Transform

def rotate_matrix(node, a):
    bbox = node.bounding_box()
    cx = bbox.center_x
    cy = bbox.center_y
    return Transform([[cos(a), -sin(a), cx], [sin(a), cos(a), cy]]) @ Transform([[1, 0, -cx], [0, 1, -cy]])
	
def optimal_rotations(node, precision):
    step = pi / float(precision)
    bbox = node.bounding_box()
    min_width = bbox.right - bbox.left
    min_width_angle = None
    min_bbox_area = min_width * (bbox.bottom - bbox.top)
    min_bbox_area_angle = None

    for i in range(precision):
        angle = -pi/2.0 + i*step
        rotated = node.bounding_box(rotate_matrix(node, angle))		
		
        width = rotated.width
        height = rotated.height
        bbox_area = width * height

        if width < min_width:
            min_width = width
            min_width_angle = angle
        if bbox_area < min_bbox_area:
            if width > height:
                # To keep results similar to min_width_angle, rotate by an
                # additional 90 degrees which doesn't affect bbox area.
                angle -= copysign(pi/2.0, angle)
                
            min_bbox_area = bbox_area
            min_bbox_area_angle = angle

    return min_width_angle, min_bbox_area_angle