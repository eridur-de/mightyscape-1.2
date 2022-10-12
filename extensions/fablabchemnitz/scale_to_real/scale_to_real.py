"""
Copyright (C) 2015 Maren Hachmann, marenhachmann@yahoo.com
Copyright (C) 2010 Blair Bonnett, blair.bonnett@gmail.com (parts from multiscale extension)
Copyright (C) 2005 Aaron Spike, aaron@ekips.org (parts from perspective extension)
Copyright (C) 2015 Giacomo Mirabassi, giacomo@mirabassi.it (parts from jpeg export extension)
Copyright (C) 2016 Neon22 @github (scale ruler)
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import math
import inkex
from inkex import Transform
from inkex.paths import CubicSuperPath
from lxml import etree

### Scale Ruler
# inches = [1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128]
# metric = [1,2,5,10,20,50,100,200,250,500,1000,1250,2500]

# TODO: 
# - maybe turn dropdown for choosing scale type (metric/imperial/custom) into radio buttons?
# - scale font size
# - scale box-height better for small boxes
# - add ruler into current layer
# - add magnification e.g. 2:1 for small drawings

class ScaleToReal(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--length', type=float, default=100.0, help='Length of scaling path in real-world units')
        pars.add_argument('--unit', default='cm', help='Real-world unit')
        pars.add_argument('--showscale', default='false',  help='Show Scale Ruler')
        pars.add_argument('--choosescale', default='all',  help='Choose Scale')
        pars.add_argument('--metric', default='1', help='Common metric scales')
        pars.add_argument('--imperial',default='1', help='Common imperial scales')
        pars.add_argument('--custom_scale', type=float, default=45, help='Custom scale')
        pars.add_argument('--unitlength', type=int, default='1', help='Length of scale ruler')

    def calc_scale_center(self, p1x, p1y, p2x, p2y):
        """ Use straight line as scaling center.
            - determine which point is center on basis of quadrant the line is in.
            - approx this by using center of line
            0,0 corresponds to UL corner of page
        """
        scale_center = (0,0) # resulting scaling point
        # calc page center
        pagecenter_x = self.svg.unittouu(self.document.getroot().get('width'))/2
        pagecenter_y = self.svg.unittouu(self.document.getroot().get('height'))/2
        # calc minmax of straightline ref points
        minx = min(p1x, p2x)
        maxx = max(p1x, p2x)
        miny = min(p1y, p2y)
        maxy = max(p1y, p2y)
        # simplifiy calc by using center of line to determine quadrant
        line_x = p1x + (p2x - p1x)/2
        line_y = p1y + (p2y - p1y)/2
        # determine quadrant
        if line_x < pagecenter_x:
            # Left hand side
            if line_y < pagecenter_y:
                scale_center = (minx,miny) # UL
            else:
                scale_center = (minx,maxy) # LL
        else: # Right hand side
            if line_y < pagecenter_y:
                scale_center = (maxx,miny) # UR
            else:
                scale_center = (maxx,maxy) # LR
        #inkex.debug("%s  %s,%s" % (scale_center, pagecenter_x*2, pagecenter_y*2))
        return scale_center
    
    def create_ruler(self, parent, width, pos, value, drawing_scale):
        """ Draw Scale ruler
            - Position above user's straightline.
            - Ruler shows two units together. First one cut into 5
            - pos is a tuple e.g. (0,0)
            
            TODO:
            - Fix font size for large and small rulers
            - Fix line width for large and small rulers
        """
        " Ruler is always 2 units long with 5 divs in the left half "
        # Draw two boxes next to each other. Top half of right half of ruler is filled black
        line_width = self.svg.unittouu('0.25 mm')
        box_height = max(width/15, self.svg.unittouu('2 mm'))
        font_height = 8
        White = '#ffffff'
        Black = '#000000'
        t = 'translate' + str(pos)
        
        # create clip in order to get an exact ruler width (without the outer half of the stroke)
        path = '//svg:defs'
        defslist = self.document.getroot().xpath(path, namespaces=inkex.NSS)
        if len(defslist) > 0:
            defs = defslist[0]
        
        clipPathData = {inkex.addNS('label', 'inkscape'):'rulerClipPath', 'clipPathUnits':'userSpaceOnUse', 'id':'rulerClipPath'}
        clipPath = etree.SubElement(defs, 'clipPath', clipPathData)
        clipBox = {'x':str(-width), 'y':'0.0',
                'width':str(width*2), 'height':str(box_height),
                'style':'fill:%s; stroke:none; fill-opacity:1;' % (Black)}

        etree.SubElement(clipPath, 'rect', clipBox)

        # create groups for scale rule and ruler
        scale_group = etree.SubElement(parent, 'g', {inkex.addNS('label','inkscape'):'scale_group', 'transform':t})
        ruler_group = etree.SubElement(scale_group, 'g', {inkex.addNS('label','inkscape'):'ruler', 'clip-path':"url(#rulerClipPath)"})
        
        # box for right half of ruler
        boxR = {'x':'0.0', 'y':'0.0',
                'width':str(width), 'height':str(box_height),
                'style':'fill:%s; stroke:%s; stroke-width:%s; stroke-opacity:1; fill-opacity:1;' % (White, Black, line_width)}
        etree.SubElement(ruler_group, 'rect', boxR)
        # top half black
        boxRf = {'x':'0.0', 'y':'0.0',
                 'width':str(width), 'height':str(box_height/2),
                 'style':'fill:%s; stroke:none; fill-opacity:1;' % (Black)}
        etree.SubElement(ruler_group, 'rect', boxRf)
        # Left half of ruler
        boxL = {'x':str(-width), 'y':'0.0',
                'width':str(width), 'height':str(box_height),
                'style':'fill:%s; stroke:%s; stroke-width:%s; stroke-opacity:1; fill-opacity:1;' % (White, Black, line_width)}
        etree.SubElement(ruler_group, 'rect', boxL)
        # staggered black fills on left half
        start = -width
        for i in range(5):
            boxRf = {'x':str(start), 'y':str((i+1)%2 * box_height/2), 
                     'width':str(width/5), 'height':str(box_height/2),
                     'style':'fill:%s; stroke:none; fill-opacity:1;' % (Black)}
            etree.SubElement(ruler_group, 'rect', boxRf)
            start += width/5
        # text
        textstyle = {'font-size': str(font_height)+ " px",
                     'font-family': 'sans-serif',
                     'text-anchor': 'middle',
                     'text-align': 'center',
                     'fill': Black }
        text_atts = {'style': str(inkex.Style(textstyle)),
                     'x': '0', 'y': str(-font_height/2) }
        text = etree.SubElement(scale_group, 'text', text_atts)
        text.text = "0"
        text_atts = {'style': str(inkex.Style(textstyle)),
                     'x': str(width), 'y': str(-font_height/2) }
        text = etree.SubElement(scale_group, 'text', text_atts)
        text.text = str(value)

        text_atts = {'style':str(inkex.Style(textstyle)),
                     'x': str(-width), 'y': str(-font_height/2) }
        text = etree.SubElement(scale_group, 'text', text_atts)
        text.text = str(value)
        # Scale note
        text_atts = {'style':str(inkex.Style(textstyle)),
                     'x': '0', 'y': str(-font_height*2.5) }
        text = etree.SubElement(scale_group, 'text', text_atts)
        text.text = "Scale 1:" + str(drawing_scale) + " (" + self.options.unit + ")"


    def effect(self):
        if len(self.options.ids) != 2:
            inkex.errormsg("This extension requires two selected objects. The first selected object must be the straight line with two nodes.")
            exit()

        # drawing that will be scaled is selected second, must be a single object
        scalepath = self.svg.selected[self.options.ids[0]]
        drawing = self.svg.selected[self.options.ids[1]]

        if scalepath.tag != inkex.addNS('path','svg'):
            inkex.errormsg("The first selected object is not a path.\nPlease select a straight line with two nodes instead.")
            exit()

        # apply its transforms to the scaling path, so we get the correct coordinates to calculate path length
        scalepath.apply_transform()
        
        path = CubicSuperPath(scalepath.get('d'))
        if len(path) < 1 or len(path[0]) < 2:
            inkex.errormsg("This extension requires that the first selected path be two nodes long.")
            exit()

        # We imagine the path is in the root layer, with no transforms:
        # get its parent transforms (its own ones are already applied):
        ct = scalepath.composed_transform()
        # now we apply that matrix inversely to make it 
        # as large (or small) as it really is
        path = path.transform(ct)

        # calculate path length
        p1_x = path[0][0][1][0]
        p1_y = path[0][0][1][1]
        p2_x = path[0][1][1][0]
        p2_y = path[0][1][1][1]

        p_length = self.svg.unittouu(str(distance((p1_x, p1_y),(p2_x, p2_y))) + self.svg.unit)
        
        # Find Drawing Scale
        if self.options.choosescale == 'metric':
            drawing_scale = int(self.options.metric)
        elif self.options.choosescale == 'imperial':
            drawing_scale = int(self.options.imperial)
        elif self.options.choosescale == 'custom':
            drawing_scale = self.options.custom_scale
        
        # calculate scaling center
        center = self.calc_scale_center(p1_x, p1_y, p2_x, p2_y)

        # calculate scaling factor
        target_length = self.svg.unittouu(str(self.options.length) + self.options.unit)
        factor = (target_length / p_length) / drawing_scale
        # inkex.debug("%s, %s  %s" % (target_length, p_length, factor))
        
        # Add scale ruler
        if self.options.showscale == "true":
            dist = int(self.options.unitlength)
            
            ruler_length = self.svg.unittouu(str(dist) + self.options.unit) / drawing_scale
            ruler_pos = (p1_x + (p2_x - p1_x)/2, (p1_y + (p2_y - p1_y)/2) - self.svg.unittouu('4 mm'))
            
            # TODO: add into current layer instead
            self.create_ruler(self.document.getroot(), ruler_length, ruler_pos, dist, drawing_scale)

        # Get drawing and current transformations
        for obj in (scalepath, drawing):
            # Scale both objects about the center, first translate back to origin
            scale_matrix = [[1, 0.0, -center[0]], [0.0, 1, -center[1]]]
            obj.transform = Transform(scale_matrix) @ obj.transform 
            # Then scale
            scale_matrix = [[factor, 0.0, 0.0], [0.0, factor, 0.0]]
            obj.transform = Transform(scale_matrix) @ obj.transform 
            # Then translate back to original scale center location
            scale_matrix = [[1, 0.0, center[0]], [0.0, 1, center[1]]]
            obj.transform = Transform(scale_matrix) @ obj.transform 

# Helper function
def distance(xy0, xy1):
    x0, y0 = xy0
    x1, y1 = xy1
    return math.sqrt((x0-x1)*(x0-x1) + (y0-y1)*(y0-y1))

if __name__ == '__main__':
    ScaleToReal().run()