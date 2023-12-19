
from os.path import join, basename
from math import sqrt, floor

from color.colors import *
from color import mixers
from palette.storage.storage import *

try:
    from tinycss import make_parser, color3
    css_support = True
except ImportError:
    print("TinyCSS is not available")
    css_support = False

class CSS(Storage):
    name = 'css'
    title = _("CSS cascading stylesheet")
    filters = ["*.css"]
    can_load = css_support
    can_save = True

    @staticmethod
    def check(filename):
        return True

    def save(self, file_w):
        pf = open(file_w, 'w')

        for i, row in enumerate(self.palette.slots):
            for j, slot in enumerate(row):
                user = "-user" if slot.mode == USER_DEFINED else ""
                hex = slot.color.hex()
                s = ".color-{}-{}{} {{ color: {} }};\n".format(i,j, user, hex)
                pf.write(s)

        pf.close()

    def load(self, mixer, file_r, options=None):
        self.palette = Palette(mixer)
        self.palette.ncols = None

        all_slots = []
        colors = []

        def add_color(clr):
            for c in colors:
                if c.getRGB() == clr.getRGB():
                    return None
            colors.append(clr)
            return clr

        parser = make_parser('page3')
        css = parser.parse_stylesheet_file(file_r) 
        for ruleset in css.rules:
            #print ruleset
            if ruleset.at_keyword:
                continue
            for declaration in ruleset.declarations:
                #print declaration
                for token in declaration.value:
                    #print token
                    css_color = color3.parse_color(token)
                    if not isinstance(css_color, color3.RGBA):
                        continue
                    r,g,b = css_color.red, css_color.green, css_color.blue
                    color = Color()
                    color.setRGB1((clip(r), clip(g), clip(b)))
                    color = add_color(color)
                    if not color:
                        continue
                    slot = Slot(color, user_defined=True)
                    all_slots.append(slot)
        n_colors = len(all_slots)
        if n_colors > MAX_COLS:
            self.palette.ncols = max( int( floor(sqrt(n_colors)) ), 1)
        else:
            self.palette.ncols = n_colors
        self.palette.setSlots(all_slots)
        self.palette.meta["SourceFormat"] = "CSS"
        print("Loaded palette: {}x{}".format( self.palette.nrows, self.palette.ncols ))
        return self.palette

