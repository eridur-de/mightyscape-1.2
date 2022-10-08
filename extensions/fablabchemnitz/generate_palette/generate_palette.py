#! /usr/bin/env python3

import os
import sys
import inkex

def log(text):
    inkex.utils.debug(text)


def abort(text):
    inkex.errormsg(_(text))
    exit()


class GeneratePalette(inkex.EffectExtension):


    def add_arguments(self, pars):
        pars.add_argument('--name', help='Palette name')
        pars.add_argument('--property', help='Color property')
        pars.add_argument('--default', type=inkex.Boolean, help='Default grays')
        pars.add_argument('--sort', help='Sort type')
        pars.add_argument('--replace', type=inkex.Boolean, dest='replace', help='Replace existing')


    def get_palettes_path(self):
        if sys.platform.startswith('win'):
            path = os.path.join(os.environ['APPDATA'], 'inkscape', 'palettes')
        else:
            path = os.environ.get('XDG_CONFIG_HOME', '~/.config')
            path = os.path.join(path, 'inkscape', 'palettes')
    
        return os.path.expanduser(path)


    def get_file_path(self):
        name = str(self.options.name).replace(' ', '-')
        return "%s/%s.gpl" % (self.palettes_path, name)


    def get_default_colors(self):
        colors = [
          "  0   0   0  Black",
          " 26  26  26  90% Gray",
          " 51  51  51  80% Gray",
          " 77  77  77  70% Gray",
          "102 102 102  60% Gray",
          "128 128 128  50% Gray",
          "153 153 153  40% Gray",
          "179 179 179  30% Gray",
          "204 204 204  20% Gray",
          "230 230 230  10% Gray",
          "236 236 236  7.5% Gray",
          "242 242 242  5% Gray",
          "249 249 249  2.5% Gray",
          "255 255 255  White"
        ]
    
        return colors if self.options.default else []


    def get_node_prop(self, node, property):
        attr = node.attrib.get('style')
        style = dict(inkex.Style.parse_str(attr))
    
        return style.get(property, 'none')


    def get_node_index(self, item):
        node = item[1]
        id = node.attrib.get('id')
        
        return self.options.ids.index(id)


    def get_node_x(self, item):
        node = item[1]
        return node.bounding_box().center_x


    def get_node_y(self, item):
        node = item[1]
        return node.bounding_box().center_y
  

    def get_formatted_color(self, color):
        rgb = inkex.Color(color).to_rgb()
        
        if self.options.sort == 'hsl':
            key = inkex.Color(color).to_hsl()
            key = "{:03d}{:03d}{:03d}".format(*key)
        else:      
            key = "{:03d}{:03d}{:03d}".format(*rgb)
                
        rgb = "{:3d} {:3d} {:3d}".format(*rgb)
        color = str(color).upper()
        name = str(inkex.Color(color).to_named()).upper()
        
        if name != color:
            name = "%s (%s)" % (name.capitalize(), color)
    
        return "%s  %s  %s" % (key, rgb, name)


    def get_selected_colors(self):
        colors   = []
        selected = list(self.svg.selected.items())
    
        if self.options.sort == 'y_location':
            selected.sort(key=self.get_node_x)
            selected.sort(key=self.get_node_y)
        elif self.options.sort == 'x_location':
            selected.sort(key=self.get_node_y)
            selected.sort(key=self.get_node_x)
        else:
            selected.sort(key=self.get_node_index)
    
        for id, node in selected:
            if self.options.property in ['fill', 'both']:
                fill = self.get_node_prop(node, 'fill')
    
            if inkex.colors.is_color(fill):   
                if fill != 'none' and fill not in colors:
                    colors.append(fill)
    
            if self.options.property in ['stroke', 'both']:
                stroke = self.get_node_prop(node, 'stroke')
    
                if inkex.colors.is_color(stroke):
                    if stroke != 'none' and stroke not in colors:
                        colors.append(stroke)
    
        colors = list(map(self.get_formatted_color, colors))
    
        if self.options.sort == 'hsl' or self.options.sort == 'rgb':
            colors.sort()
    
        return list(map(lambda x : x[11:], colors))


    def write_palette(self):
        file = open(self.file_path, 'w')
        try:
            file.write("GIMP Palette\n")
            file.write("Name: %s\n" % self.options.name)
            file.write("#\n# Generated with Inkscape Generate Palette\n#\n")
    
            for color in self.default_colors:
                file.write("%s\n" % color)
    
            for color in self.selected_colors:
                if color[:11] not in list(map(lambda x : x[:11], self.default_colors)):
                    file.write("%s\n" % color)
        finally:
            file.close()


    def effect(self):
        self.palettes_path = self.get_palettes_path()
        self.file_path = self.get_file_path()
        self.default_colors  = self.get_default_colors()
        self.selected_colors = self.get_selected_colors()
    
        if not self.options.replace and os.path.exists(self.file_path):
            abort('Palette already exists!')
    
        if not self.options.name:
            abort('Please enter a palette name.')
    
        if len(self.options.ids) < 2:
            abort('Please select at least 2 objects.')
    
        if not len(self.selected_colors):
            abort('No colors found in selected objects!')
    
        self.write_palette()

if __name__ == '__main__':
    GeneratePalette().run()
