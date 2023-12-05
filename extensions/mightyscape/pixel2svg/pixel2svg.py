#!/usr/bin/env python3
"""
Pixel2SVG - Convert the pixels of bitmap images to SVG rects

Idea and original implementation as standalone script:
Copyright (C) 2011 Florian Berger <fberger@florian-berger.de>
Homepage: <http://florian-berger.de/en/software/pixel2svg>

Rewritten as Inkscape extension:
Copyright (C) 2012 ~suv <suv-sf@users.sourceforge.net>

'getFilePath()' is based on code from 'extractimages.py':
Copyright (C) 2005 Aaron Spike, aaron@ekips.org

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
"""

import os
import sys
import base64
from io import StringIO, BytesIO
import urllib.request as urllib
import inkex
from PIL import Image
from lxml import etree

DEBUG = False

#   int r = ( hexcolor >> 16 ) & 0xFF;
#   int g = ( hexcolor >> 8 ) & 0xFF;
#   int b = hexcolor & 0xFF;
#   int hexcolor = (r << 16) + (g << 8) + b;

def hex_to_int_color(v):
    if (v[0] == '#'):
        v = v[1:]
    assert(len(v) == 6)
    return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16)

class Pixel2SVG(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("-s", "--squaresize", type=int, default="5", help="Width and height of vector squares in pixels")
        pars.add_argument("--same_like_original", type=inkex.Boolean, default=True, help="Same size as original")
        pars.add_argument("--transparency", type=inkex.Boolean, default=True, help="Convert transparency to 'fill-opacity'")
        pars.add_argument("--overlap", type=inkex.Boolean, default=False, help="Overlap vector squares by 1px")
        pars.add_argument("--offset_image", type=inkex.Boolean, default=True, help="Offset traced image")
        pars.add_argument("--delete_image", type=inkex.Boolean, default=False, help="Delete bitmap image")
        pars.add_argument("--maxsize", type=int, default="256", help="Max. image size (width or height)")
        pars.add_argument("--verbose", type=inkex.Boolean, default=False)
        pars.add_argument("--color_mode", default="all", help="Which colors to trace.")
        pars.add_argument("--color", default="FFFFFF", help="Special color")
        pars.add_argument("--tab")

    def checkImagePath(self, node):
        """Embed the data of the selected Image Tag element"""
        xlink = node.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = node.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path

    def drawFilledRect(self, parent, svgpx):
        """
        Draw rect based on ((x, y), (width,height), ((r,g,b),a)), add to parent
        """
        style = {}
        pos = svgpx[0]
        dim = svgpx[1]
        rgb = svgpx[2][0]
        alpha = svgpx[2][1]

        style['stroke'] = 'none'

        if len(rgb) == 3:
            # fill: rgb tuple
            style['fill'] = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
        elif len(rgb) == 1:
            # fill: color name, or 'none'
            style['fill'] = rgb[0]
        else:
            # fill: 'Unset' (no fill defined)
            pass

        if alpha < 255:
            # only write 'fill-opacity' for non-default value
            style['fill-opacity'] = '%s' % round(alpha/255.0, 8)

        rect_attribs = {'x': str(pos[0]),
                        'y': str(pos[1]),
                        'width': str(dim[0]),
                        'height': str(dim[1]),
                        'style': str(inkex.Style(style)), }

        rect = etree.SubElement(parent, inkex.addNS('rect', 'svg'), rect_attribs)

        return rect

    def vectorizeImage(self, node):
        """
        Parse RGBA values of linked bitmap image, create a group and
        draw the rectangles (SVG pixels) inside the new group
        """
        self.path = self.checkImagePath(node)  # This also ensures the file exists
        if self.path is None:  # check if image is embedded or linked
            image_string = node.get('{http://www.w3.org/1999/xlink}href')
            # find comma position
            i = 0
            while i < 40:
                if image_string[i] == ',':
                    break
                i = i + 1
            image = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
        else:
            image = Image.open(self.path)

        if image:
            # init, set limit (default: 256)
            pixel2svg_max = self.options.maxsize

            if self.options.verbose:
                inkex.utils.debug("ID: %s" % node.get('id'))
                inkex.utils.debug("Image size:\t%dx%d" % image.size)
                inkex.utils.debug("Image format:\t%s" % image.format)
                inkex.utils.debug("Image mode:\t%s" % image.mode)
                inkex.utils.debug("Image info:\t%s" % image.info)

                if (image.mode == 'P' and 'transparency' in image.info):
                    inkex.utils.debug(
                        "Note: paletted image with an alpha channel is handled badly with " +
                        "current PIL:\n" +
                        "<http://stackoverflow.com/questions/12462548/pil-image-mode-p-rgba>")
                elif not image.mode in ('RGBA', 'LA'):
                    inkex.utils.debug("No alpha channel or transparency found")

            image = image.convert("RGBA")
            (width, height) = image.size

            if width <= pixel2svg_max and height <= pixel2svg_max:

                # color trace modes
                trace_color = []
                if self.options.color:
                    trace_color = hex_to_int_color(self.options.color)

                # get RGBA data
                rgba_values = list(image.getdata())

                # create group
                nodeParent = node.getparent()
                nodeIndex = nodeParent.index(node)
                pixel2svg_group = etree.Element(inkex.addNS('g', 'svg'))
                pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
                nodeParent.insert(nodeIndex + 1, pixel2svg_group)
                  
                # draw bbox rectangle at the bottom of group
                pixel2svg_bbox_fill = ('none', )
                pixel2svg_bbox_alpha = 255
                pixel2svg_bbox = ((0, 0),
                                  (width * self.options.squaresize,
                                   height * self.options.squaresize),
                                  (pixel2svg_bbox_fill, pixel2svg_bbox_alpha))
                self.drawFilledRect(pixel2svg_group, pixel2svg_bbox)

                img_w = node.get('width')
                img_h = node.get('height')
                img_x = node.get('x')
                img_y = node.get('y')                   
                if img_w is not None and img_h is not None and img_x is not None and img_y is not None:
                    #if width/height are not unitless but end with px, mm, in etc. we have to convert to a float number
                    if img_w[-1].isdigit() is False:
                        img_w = self.svg.uutounit(img_w)
                    if img_h[-1].isdigit() is False:
                        img_h = self.svg.uutounit(img_h)
                    if self.options.same_like_original is True:   
                        scale_x = float(img_w) / pixel2svg_bbox[1][0] #px
                        scale_y = float(img_h) / pixel2svg_bbox[1][1] #px
                    else:
                        scale_x = 1.0
                        scale_y = 1.0
                    # move group beside original image
                    if self.options.offset_image:
                        pixel2svg_offset = float(img_w)
                    else:
                        pixel2svg_offset = 0.0
                    # add transformation to fit previous XY coordinates and width/height
                    # image might also be influenced by other transformations from parent:
                    if nodeParent is not None and nodeParent != self.document.getroot():
                        tpc = nodeParent.composed_transform()
                        x_offset = tpc.e + pixel2svg_offset
                        y_offset = tpc.f
                    else:
                        x_offset = 0.0 + pixel2svg_offset
                        y_offset = 0.0
                    transform = "matrix({:1.6f}, 0, 0, {:1.6f}, {:1.6f}, {:1.6f})"\
                    .format(scale_x, scale_y, float(img_x) + x_offset, float(img_y) + y_offset)
                else:
                    t = node.composed_transform()
                    img_w = t.a
                    img_h = t.d 
                    img_x = t.e
                    img_y = t.f
                    if self.options.same_like_original is True:   
                        scale_x = float(img_w) / pixel2svg_bbox[1][0] #px
                        scale_y = float(img_h) / pixel2svg_bbox[1][1] #px
                    else:
                        scale_x = 1.0
                        scale_y = 1.0
                    # move group beside original image
                    if self.options.offset_image:
                        pixel2svg_offset = float(img_w)
                    else:
                        pixel2svg_offset = 0.0
                    # add transformation to fit previous XY coordinates and width/height
                    # image might also be influenced by other transformations from parent:
                    if nodeParent is not None and nodeParent != self.document.getroot():
                        tpc = nodeParent.composed_transform()
                        x_offset = tpc.e + pixel2svg_offset
                        y_offset = tpc.f
                    else:
                        x_offset = 0.0 + pixel2svg_offset
                        y_offset = 0.0
                    transform = "matrix({:1.6f}, 0, 0, {:1.6f}, {:1.6f}, {:1.6f})"\
                    .format(scale_x, scale_y, float(img_x) + x_offset, float(img_y) + y_offset)
                pixel2svg_group.attrib['transform'] = transform

                # reverse list (performance), pop last one instead of first
                rgba_values.reverse()
                # loop through pixels (per row)
                rowcount = 0
                while rowcount < height:
                    colcount = 0
                    while colcount < width:
                        rgba_tuple = rgba_values.pop()
                        # Omit transparent pixels
                        if rgba_tuple[3] > 0:
                            # color options
                            do_trace = True
                            if (self.options.color_mode != "all"):
                                if (trace_color == rgba_tuple[:3]):
                                    # colors match
                                    if (self.options.color_mode == "other"):
                                        do_trace = False
                                else:
                                    # colors don't match
                                    if (self.options.color_mode == "this"):
                                        do_trace = False
                            if do_trace:
                                # position
                                svgpx_x = colcount * self.options.squaresize
                                svgpx_y = rowcount * self.options.squaresize
                                # dimension + overlap
                                svgpx_size = self.options.squaresize + self.options.overlap
                                # get color, ignore alpha
                                svgpx_rgb = rgba_tuple[:3]
                                svgpx_a = 255
                                # transparency
                                if self.options.transparency:
                                    svgpx_a = rgba_tuple[3]
                                svgpx = ((svgpx_x, svgpx_y),
                                         (svgpx_size, svgpx_size),
                                         (svgpx_rgb, svgpx_a)
                                         )
                                # draw square in group
                                self.drawFilledRect(pixel2svg_group, svgpx)
                        colcount = colcount + 1
                    rowcount = rowcount + 1

                # all done
                if DEBUG:
                    inkex.utils.debug("All rects drawn.")

                if self.options.delete_image:
                    nodeParent.remove(node)

            else:
                # bail out with larger images
                inkex.errormsg(
                    "Bailing out: this extension is not intended for large images.\n" +
                    "The current limit is %spx for either dimension of the bitmap image."
                    % pixel2svg_max)
                sys.exit(0)

            # clean-up?
            if DEBUG:
                inkex.utils.debug("Done.")

        else:
            inkex.errormsg("Bailing out: No supported image file or data found")
            sys.exit(1)

    def effect(self):
        """
        Pixel2SVG - Convert the pixels of bitmap images to SVG rects
        """
        found_image = False
        if (self.options.ids):
            for node in self.svg.selected.values():
                if node.tag == inkex.addNS('image', 'svg'):
                    found_image = True
                    self.vectorizeImage(node)

        if not found_image:
            inkex.errormsg("Please select one or more bitmap image(s) for Pixel2SVG")
            sys.exit(0)

if __name__ == '__main__':
    Pixel2SVG().run()