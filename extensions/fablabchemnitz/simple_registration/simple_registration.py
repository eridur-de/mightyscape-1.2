#!/usr/bin/env python3
#
# Copyright (C) [2021] [Matt Cottam], [mpcottam@raincloud.co.uk]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

##############################################################################
# Simple Registration - Registration Marks Across Objects
##############################################################################

import inkex
from inkex import command, Group

# Python Standard Library
import tempfile
from lxml import etree
import random

unit_conversions = {
    'in': 96.0,
    'pt': 1.3333333333333333,
    'px': 1.0,
    'mm': 3.779527559055118,
    'cm': 37.79527559055118,
    'm': 3779.527559055118,
    'km': 3779527.559055118,
    'Q': 0.94488188976378,
    'pc': 16.0,
    'yd': 3456.0,
    'ft': 1152.0,
    '': 1.0,  # Default px
}

crosshair_path = "m 1.0583333,3.0583334 h 4.0000001 m -2,-2.0000001 v 4.0000001 m 0.25,-2 a 0.25,0.25 0 0 1 -0.25," \
                 "0.25 0.25,0.25 0 0 1 -0.25,-0.25 0.25,0.25 0 0 1 0.25,-0.25 0.25,0.25 0 0 1 0.25,0.25 z m 0.75," \
                 "0 a 1,1 0 0 1 -1,1 1,1 0 0 1 -1,-1 1,1 0 0 1 1,-1 1,1 0 0 1 1,1 z m 0.5,0 a 1.5,1.5 0 0 1 -1.5," \
                 "1.5 1.5,1.5 0 0 1 -1.5,-1.5 1.5,1.5 0 0 1 1.5,-1.5 1.5,1.5 0 0 1 1.5,1.5 z "

spiral_path = "m 2.8602054,2.8871104 c 0.0099,0.108862 -0.155578,0.06596 -0.197873,0.0151 -0.11462,-0.137812 0.0156," \
              "-0.320651 0.164837,-0.376975 0.266943,-0.100751 0.549334,0.08169 0.626652,0.316559 0.113468," \
              "0.344685 -0.163181,0.687127 -0.527545,0.769055 -0.485643,0.109197 -0.954879,-0.216671 -1.055435," \
              "-0.648222 -0.126538,-0.543064 0.310663,-1.059761 0.890257,-1.161135 0.701965,-0.122775 1.363419," \
              "0.351433 1.484214,0.979887 0.142351,0.740611 -0.457969,1.433888 -1.252965,1.553212 -0.917855," \
              "0.137765 -1.7729561,-0.486089 -1.9129951,-1.311549 -0.15912096,-0.93794 0.6052021,-1.8086111 " \
              "1.6156751,-1.9452921 1.133598,-0.15333396 2.182944,0.6207011 2.341774,1.6432131 0.176331," \
              "1.135182 -0.752397,2.183635 -1.978384,2.33737 "

star_path = "m 4.2951254,5.0575354 -1.236268,-0.682814 -1.235872,0.683612 0.235648,-1.447143 -1.0002991,-1.024496 1.3819041,-0.211573 0.617649,-1.3167881 0.618418,1.3163901 1.382026,0.210678 -0.999698,1.025144 z"

circle_path = "m 5.0583334,3.0583334 a 2,2 0 0 1 -2,2 2,2 0 0 1 -2.0000001,-2 2,2 0 0 1 2.0000001,-2.0000001 2,2 0 0 1 2,2.0000001 z"

square_path = "M 1.0583333,1.0583333 H 5.0583334 V 5.0583334 H 1.0583333 Z"

chevron_path = "m 1.0583333,1.0583333 3.9999999,2 -3.9999999,1.9999999"


def add_reg_object(self, reg_path):
    # parent = self.svg.get_current_layer()
    parent = self.svg
    my_reg_object = etree.SubElement(parent, inkex.addNS('path', 'svg'))
    reg_path = eval(reg_path)
    my_reg_object.path = reg_path
    my_reg_object.attrib['id'] = 'my_reg_object'
    my_reg_object.style['fill'] = 'none'
    # my_reg_object.style['stroke-width'] = '0.1'
    my_reg_object.style['stroke-width'] = '0.05'
    my_reg_object.style['stroke'] = self.options.color_picker_reg_object
    my_reg_object.transform.add_scale(self.options.reg_mark_scale)

    return my_reg_object

def add_tick_labels(self):
    my_objects = self.svg.selected.rendering_order()
    parent = self.svg.get_current_layer()

    object_count = 1
    for my_object in my_objects:
        text_label = etree.SubElement(parent, inkex.addNS('text', 'svg'))
        text_label.text = str(object_count)
        text_label.style['font-size'] = self.options.tick_text_label_font_size
        text_label.attrib['id'] = 'tick_label_temp' + str(object_count)
        text_label.style['text-anchor'] = 'middle'
        text_label.style['dominant-baseline'] = 'middle'

        object_count += 1


def create_new_group(self, prefix, mode):
    group_id = str(prefix) + '_' + str(random.randrange(100000, 999999))
    new_group = self.svg.add(Group.new('#' + group_id))
    new_group.set('inkscape:groupmode', str(mode))
    new_group.attrib['id'] = group_id

    return new_group


def apply_translate(self, parent, my_object, my_transform):
    bodge_group = create_new_group(self, 'bodge_group', 'group')
    bodge_group.append(my_object)
    bodge_group.transform = bodge_group.transform @ my_transform
    my_inherited_object_transform = my_object.composed_transform()
    parent.append(my_object)
    my_object.transform = my_inherited_object_transform
    bodge_group.delete()

def random_rgb(self):
    random_red = random.randrange(0, 255)
    random_green = random.randrange(0, 255)
    random_blue = random.randrange(0, 255)

    return f'rgb({random_red}, {random_green}, {random_blue})'


def query_all_bbox(self):
    my_file_path = self.options.input_file

    with tempfile.NamedTemporaryFile(mode='r+', suffix='.svg') as temp_svg_file:
        # Write the contents of the updated svg to a tempfile to use with command line
        my_svg_string = self.svg.root.tostring().decode("utf-8")
        temp_svg_file.write(my_svg_string)
        temp_svg_file.read()
        my_query = inkex.command.inkscape(temp_svg_file.name, '--query-all')
        # Account for versions of inkey.py which return query as bytes
        if type(my_query) != str:
            my_query = my_query.decode("utf-8")
        # --query-all produces multiline output of the following format
        # path853,172.491,468.905,192.11,166.525 - as string
        # ElementId, Top, Left, Width, Height

        # Make a list splitting by each new line
        my_query_items = my_query.split('\n')
        my_element_bbox_dict = {}

        for my_query_item in my_query_items:
            # Create a comma separated list item for each line
            my_element = my_query_item.split(',')
            # Make a dictionary for all elements, rejected malformed elements.
            if len(my_element) > 4:
                my_element_bbox_dict[my_element[0]] = {}
                # Create Dictionary entry in anticlockwise format
                # x1 = TopLeft, x2 = BottomLeft, x3 = BottomRight, x4 = TopRight, mid_x and mid_y

                # First convert all values to float, skipping element id ( first entry )
                my_element_bbox = [float(x) for x in my_element[1:]]

                width = my_element_bbox[2]
                height = my_element_bbox[3]

                x1 = my_element_bbox[0]
                y1 = my_element_bbox[1]
                x2 = x1
                y2 = y1 + height
                x3 = x1 + width
                y3 = y2
                x4 = x1 + width
                y4 = y1
                mid_x = x1 + width / 2
                mid_y = y1 + height / 2

                my_element_bbox_dict[my_element[0]].update(x1=x1, y1=y1, x2=x2, y2=y2, x3=x3, y3=y3, x4=x4, y4=y4,
                                                           mid_x=mid_x, mid_y=mid_y, width=width, height=height)
        # Return dictionary
        return my_element_bbox_dict


def reg_mark_to_corners(self, all_bbox, max_bbox, my_reg_object, my_object, cf, parent):

    reg_mark_x_shift = self.options.reg_mark_x_shift
    reg_mark_y_shift = self.options.reg_mark_y_shift

    # get width and height of reg object
    my_reg_object_width = all_bbox[my_reg_object.get_id()]['width']
    my_reg_object_height = all_bbox[my_reg_object.get_id()]['height']

    my_reg_object_mid_x = all_bbox[my_reg_object.get_id()]['mid_x']
    my_reg_object_mid_y = all_bbox[my_reg_object.get_id()]['mid_y']

    my_object_id = my_object.get_id()

    new_reg_group = create_new_group(self, 'reg_group', 'group')
    # new_group.append(my_object)

    for corner_no in range(1, 5):
        registration_object = my_reg_object.duplicate()
        registration_object.style['stroke-width'] = '0.2'

        registration_object_original_composed_transform = registration_object.composed_transform()

        my_translate_text = str(
            (max_bbox['x' + str(corner_no)] - (my_reg_object_mid_x)) / cf) + ',' + str(
            (max_bbox['y' + str(corner_no)] - (my_reg_object_mid_y)) / cf)

        my_translate_text = f'Transform(\'translate({my_translate_text})\')'

        apply_translate(self, parent, registration_object, my_translate_text)

        new_reg_group.append(registration_object)

    return new_reg_group


def draw_ticks(self, all_bbox, my_reg_object, max_bbox,object_count, number_of_objects, my_object, cf):
    parent = self.svg.get_current_layer()

    tick_color = self.options.color_picker_tick

    tick_dict = {}

    # Get the right edge of the top left registration mark
    # my_element_bbox_dict[my_element[0]].update(x1=x1, y1=y1, x2=x2, y2=y2, x3=x3, y3=y3, x4=x4, y4=y4,
    #                                            mid_x=mid_x, mid_y=mid_y, width=width, height=height)

    my_reg_object_width = all_bbox[my_reg_object.get_id()]['width'] / cf
    my_reg_object_height = all_bbox[my_reg_object.get_id()]['height'] / cf
    # tl_re = top left right edge, tr_le = top right left edge
    tl_re_x = (max_bbox['x1'] / cf + my_reg_object_width)
    tl_re_y = (max_bbox['y1']) / cf
    tr_le_x = (max_bbox['x4'] / cf - my_reg_object_width)
    tr_le_y = (max_bbox['y4']) / cf
    bl_re_x = (max_bbox['x2']) / cf
    bl_re_y = (max_bbox['y2']) / cf
    br_le_x = (max_bbox['x3'] / cf )
    br_le_y = (max_bbox['y3'] / cf )

    # Get the distance between top left right edge and top right left edge
    top_bar_reg_fraction = 1  # Set to 1 to prevent division by zero
    left_bar_reg_fraction = 1  # Set to 1 to prevent division by zero
    top_bar_length = tr_le_x - tl_re_x

    if number_of_objects > 1:
        top_bar_reg_fraction = top_bar_length / (number_of_objects - 1)


    left_bar_length = (bl_re_y - (my_reg_object_height)) - (tl_re_y + (my_reg_object_height))
    if number_of_objects > 1:
        left_bar_reg_fraction = left_bar_length / (number_of_objects - 1)

    my_circle_radius = self.options.tick_circle_radius / cf

    my_circle = etree.SubElement(parent, inkex.addNS('circle', 'svg'))
    # my_circle.attrib['cx'] = str(tl_re_x + my_circle_radius)
    my_circle.attrib['cx'] = str(tl_re_x + (top_bar_reg_fraction * object_count))
    my_circle.attrib['cy'] = str(tl_re_y)
    my_circle.attrib['r'] = str(my_circle_radius / cf)
    my_circle.style['stroke'] = tick_color
    if self.options.tick_color_random_checkbox == 'true':
        my_circle.style['stroke'] = random_rgb(self)

    my_circle.style['stroke-width'] = '0.2'
    my_circle.style['fill'] = 'none'

    if self.options.tick_top_checkbox == 'true':
        object_id = my_object.get_id()
        circle_top = my_circle.duplicate()
        circle_top.attrib['id'] = str(object_id) + '_tick_circle_top_' + str(object_count + 1)
        tick_dict['tick_top'] = circle_top

        tick_label_top = self.svg.getElementById('tick_label_temp' + str(object_count + 1)).duplicate()
        tick_label_top.attrib['x'] = circle_top.attrib['cx']
        tick_label_top.attrib['y'] = circle_top.attrib['cy']
        tick_label_top.attrib['id'] = str(object_id) + '_tick_label_top_' + str(object_count + 1)
        tick_dict['tick_label_top'] = tick_label_top

    if self.options.tick_left_checkbox == 'true':
        circle_left = my_circle.duplicate()
        circle_left.attrib['cx'] = str(bl_re_x)
        circle_left.attrib['cy'] = str(tl_re_y + my_reg_object_height + (left_bar_reg_fraction * object_count))
        circle_left.attrib['id'] = str(object_id) + '_tick_circle_left_' + str(object_count + 1)
        tick_dict['tick_left'] = circle_left

        tick_label_left = self.svg.getElementById('tick_label_temp' + str(object_count + 1)).duplicate()
        tick_label_left.attrib['x'] = circle_left.attrib['cx']
        tick_label_left.attrib['y'] = circle_left.attrib['cy']
        tick_label_left.attrib['id'] = str(object_id) + '_tick_label_left_' + str(object_count + 1)
        tick_dict['tick_label_left'] = tick_label_left

    if self.options.tick_bottom_checkbox == 'true':
        circle_bottom = my_circle.duplicate()
        circle_bottom.attrib['cx'] = str(tl_re_x + (top_bar_reg_fraction * object_count))
        circle_bottom.attrib['cy'] = str(bl_re_y)
        circle_bottom.attrib['id'] = str(object_id) + '_tick_circle_bottom_' + str(object_count + 1)
        tick_dict['tick_bottom'] = circle_bottom

        tick_label_bottom = self.svg.getElementById('tick_label_temp' + str(object_count + 1)).duplicate()
        tick_label_bottom.attrib['x'] = circle_bottom.attrib['cx']
        tick_label_bottom.attrib['y'] = circle_bottom.attrib['cy']
        tick_label_bottom.attrib['id'] = str(object_id) + '_tick_label_bottom_' + str(object_count + 1)
        tick_dict['tick_label_bottom'] = tick_label_bottom

    if self.options.tick_right_checkbox == 'true':
        circle_right = my_circle.duplicate()
        circle_right.attrib['cx'] = str(br_le_x)
        circle_right.attrib['cy'] = str(br_le_y - my_reg_object_height - (left_bar_reg_fraction * object_count))
        circle_right.attrib['id'] = str(object_id) + '_tick_circle_right_' + str(object_count + 1)
        tick_dict['tick_right'] = circle_right

        tick_label_right = self.svg.getElementById('tick_label_temp' + str(object_count + 1)).duplicate()
        tick_label_right.attrib['x'] = circle_right.attrib['cx']
        tick_label_right.attrib['y'] = circle_right.attrib['cy']
        tick_label_right.attrib['id'] = str(object_id) + '_tick_label_right_' + str(object_count + 1)
        tick_dict['tick_label_right'] = tick_label_right

    my_circle.delete()

    return tick_dict

def get_max_bbox(self, all_bbox):
    my_objects = self.svg.selected.rendering_order()

    reg_mark_x_shift = self.options.reg_mark_x_shift
    reg_mark_y_shift = self.options.reg_mark_y_shift

    # Find extent of bounding box for combined selection
    bbox_list_x = []
    bbox_list_y = []
    for my_object in my_objects:
        my_object_id = my_object.get_id()
        if my_object_id == '':
            continue
        # bbox_list_x.append(all_bbox[my_object_id]['x1']) + (reg_mark_x_shift * -1)
        # bbox_list_x.append(all_bbox[my_object_id]['x4']) + (reg_mark_x_shift)
        # bbox_list_y.append(all_bbox[my_object_id]['y1']) + (reg_mark_y_shift * -1)
        # bbox_list_y.append(all_bbox[my_object_id]['y2']) + (reg_mark_y_shift)

        bbox_list_x.append(all_bbox[my_object_id]['x1'] + (reg_mark_x_shift * -1))
        bbox_list_x.append(all_bbox[my_object_id]['x4'] + (reg_mark_x_shift))
        bbox_list_y.append(all_bbox[my_object_id]['y1'] + (reg_mark_y_shift * -1))
        bbox_list_y.append(all_bbox[my_object_id]['y2'] + (reg_mark_y_shift))

    bboxes_min_x = min(bbox_list_x)
    bboxes_max_x = max(bbox_list_x)
    bboxes_min_y = min(bbox_list_y)
    bboxes_max_y = max(bbox_list_y)
    bboxes = {'x1': bboxes_min_x, 'y1': bboxes_min_y, 'x2': bboxes_min_x, 'y2': bboxes_max_y, 'x3': bboxes_max_x,
              'y3': bboxes_max_y, 'x4': bboxes_max_x, 'y4': bboxes_min_y}

    return bboxes


# Create a group or layer to contain each object and marks
def group_layer_loop(self, all_bbox, max_bbox, my_reg_object, cf):
    my_objects = self.svg.selected.rendering_order()
    number_of_objects = len(my_objects)

    object_count = 0

    for my_object in my_objects:
        my_object_id = my_object.get_id()
        master_group = create_new_group(self, my_object_id + '_group', 'group')
        tick_group = create_new_group(self, my_object_id + '_ticks', 'group')
        tick_labels_group = create_new_group(self, my_object_id + '_tick_labels', 'group')
        new_layer = create_new_group(self, my_object_id + '_layer', 'layer')

        # Create corner reg marks
        reg_mark_group = reg_mark_to_corners(self, all_bbox, max_bbox, my_reg_object, my_object, cf, master_group)

        master_group.append(reg_mark_group)

        # Create ticks
        tick_dict = draw_ticks(self, all_bbox, my_reg_object, max_bbox, object_count, number_of_objects, my_object, cf)

        if 'tick_top' in tick_dict:
            tick_group.append(tick_dict['tick_top'])
        if 'tick_left' in tick_dict:
            tick_group.append(tick_dict['tick_left'])
        if 'tick_bottom' in tick_dict:
            tick_group.append(tick_dict['tick_bottom'])
        if 'tick_right' in tick_dict:
            tick_group.append(tick_dict['tick_right'])

        if 'tick_label_top' in tick_dict:
            tick_labels_group.append(tick_dict['tick_label_top'])
        if 'tick_label_left' in tick_dict:
            tick_labels_group.append(tick_dict['tick_label_left'])
        if 'tick_label_bottom' in tick_dict:
            tick_labels_group.append(tick_dict['tick_label_bottom'])
        if 'tick_label_right' in tick_dict:
            tick_labels_group.append(tick_dict['tick_label_right'])

        # Add object to group
        master_group.append(tick_labels_group)
        master_group.append(tick_group)

        if self.options.correct_layer_transform_checkbox == 'true':
            my_object_composed_transform = my_object.composed_transform()
            master_group.append(my_object)
            my_object.transform = my_object_composed_transform
        else:
            master_group.append(my_object)

        # Add master group to layer for that object
        new_layer.append(master_group)

        object_count += 1

    # Remove temp text labels and reg object
    my_temp_labels = self.svg.xpath("//*[contains(@id, 'tick_label_temp')]")
    for item in my_temp_labels:
        item.delete()
    my_reg_object.delete()

class SimpleRegistration2(inkex.EffectExtension):

    def add_arguments(self, pars):

        pars.add_argument("--simple_registration_notebook", default=0)
        pars.add_argument("--color_picker_reg_object", type=inkex.colors.Color, default=0)
        pars.add_argument("--reg_mark_type", default='crosshair_path')
        pars.add_argument("--reg_mark_scale", type=float,  default=1)
        pars.add_argument("--reg_mark_x_shift", type=float, default=10)
        pars.add_argument("--reg_mark_y_shift", type=float, default=10)
        pars.add_argument("--correct_layer_transform_checkbox")
        pars.add_argument("--color_picker_tick", type=inkex.colors.Color, default=0)
        pars.add_argument("--tick_color_random_checkbox", type=str)
        pars.add_argument("--tick_text_labels_checkbox", type=str)
        pars.add_argument("--tick_text_label_font_size", type=float, default=0)
        pars.add_argument("--tick_type", default='chevron_path')
        pars.add_argument("--tick_circle_radius", type=float, default=5)
        pars.add_argument("--tick_top_checkbox")
        pars.add_argument("--tick_left_checkbox")
        pars.add_argument("--tick_bottom_checkbox")
        pars.add_argument("--tick_right_checkbox")

    def effect(self):
        # Exit if nothing is selected
        if len(self.svg.selected) < 1:
            return

        # Get document units, and conversion factor from pixels.
        found_units = self.svg.unit
        # Unit conversion factor cf
        cf = unit_conversions[found_units]

        # Add mark objects before command line --query-all
        # This returns all bounding boxes taking stroke into account
        # Also works for text bounding box, which is not possible to obtain from extension system

        my_reg_object = add_reg_object(self, self.options.reg_mark_type)
        # my_side_object = add_side_object(self, self.options.tick_type)

        if self.options.tick_text_labels_checkbox == 'true':
            my_labels = add_tick_labels(self)

        # Get bounding boxes for all elements
        all_bbox = query_all_bbox(self)
        # Get max bbox, taking into account user x and y shift
        max_bbox = get_max_bbox(self, all_bbox)

        # inkex.errormsg(max_bbox)
        group_layer_loop(self, all_bbox, max_bbox, my_reg_object, cf)

if __name__ == '__main__':
    SimpleRegistration2().run()
