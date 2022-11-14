#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper functions

"""
import os
from abc import abstractmethod

from Path import Path, inkex, simplestyle

class Pattern(inkex.Effect):
    """ Class that inherits inkex.Effect and further specializes it for different
    Patterns generation

    Attributes
    ---------
    styles_dict: dict
            defines styles for every possible stroke. Default values are:
            styles_dict = {'m' : mountain_style,
                           'v' : valley_style,
                           'e' : edge_style}

    topgroup: inkex.etree.SubElement
            Top Inkscape group element

    path_tree: nested list 
        Contains "tree" of Path instances, defining new groups for each
        sublist

    translate: 2 sized tuple
        Defines translation to be added when drawing to Inkscape (default: 0,0)

    Methods
    ---------
    effect(self)
        Main function, called when the extension is run.

    create_styles_dict(self)
        Get stroke style parameters and use them to create the styles dictionary.

    calc_unit_factor(self)
        Return the scale factor for all dimension conversions

    add_text(self, node, text, position, text_height=12)
        Create and insert a single line of text into the svg under node.

    get_color_string(self, longColor, verbose=False)
        Convert the long into a #RRGGBB color value

    Abstract Methods
    ---------
    __init__(self)
        Parse all options

    generate_path_tree(self)
        Generate nested list of Path


    """
    
    @abstractmethod
    def generate_path_tree(self):
        """ Generate nested list of Path instances 
        Abstract method, must be defined in all child classes
        """
        pass

    @abstractmethod
    def __init__(self):
        """ Parse all common options 
        
        Must be reimplemented in child classes to parse specialized options
        """

        inkex.Effect.__init__(self)  # initialize the super class
        
        # backwards compatibility
        try:
            self.add_argument = self.arg_parser.add_argument
            self.str = str
            self.int = int
            self.float = float
            self.bool = inkex.Boolean
        except:
            self.add_argument = self.OptionParser.add_option
            self.str = "string"
            self.int = "int"
            self.float = "float"
            self.bool = "inkbool"

        # Two ways to get debug info:
        # OR just use inkex.debug(string) instead...
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.

        self.add_argument('-u', '--units', type=self.str, default='mm')

        # bypass most style options for OrigamiSimulator
        self.add_argument('--simulation_mode', type=self.bool, default=False)

        # mountain options
        self.add_argument('--mountain_stroke_color', type=self.str,  default=4278190335)  # Red
        self.add_argument('--mountain_stroke_width', type=self.float, default=0.1)
        self.add_argument('--mountain_dashes_len', type=self.float, default=1.0)
        self.add_argument('--mountain_dashes_duty', type=self.float, default=0.5)
        self.add_argument('--mountain_dashes_bool', type=self.bool, default=True)
        self.add_argument('--mountain_bool', type=self.bool, default=True)
        self.add_argument('--mountain_bool_only', type=self.bool, default=False)

        # valley options
        self.add_argument('--valley_stroke_color', type=self.str, default=65535)  # Blue
        self.add_argument('--valley_stroke_width', type=self.float, default=0.1)
        self.add_argument('--valley_dashes_len', type=self.float, default=1.0)
        self.add_argument('--valley_dashes_duty', type=self.float, default=0.25)
        self.add_argument('--valley_dashes_bool', type=self.bool, default=True)
        self.add_argument('--valley_bool', type=self.bool, default=True)
        self.add_argument('--valley_bool_only', type=self.bool, default=False)

        # edge options
        self.add_argument('--edge_stroke_color', type=self.str,  default=255)  # Black
        self.add_argument('--edge_stroke_width', type=self.float, default=0.1)
        self.add_argument('--edge_dashes_len', type=self.float, default=1.0)
        self.add_argument('--edge_dashes_duty', type=self.float, default=0.25)
        self.add_argument('--edge_dashes_bool', type=self.bool, default=False)
        self.add_argument('--edge_bool', type=self.bool, default=True)
        self.add_argument('--edge_bool_only', type=self.bool, default=False)
        self.add_argument('--edge_single_path', type=self.bool, default=True)

        # universal crease options
        self.add_argument('--universal_stroke_color', type=self.str, default=4278255615)  # Magenta
        self.add_argument('--universal_stroke_width', type=self.float, default=0.1)
        self.add_argument('--universal_dashes_len',  type=self.float,  default=1.0)
        self.add_argument('--universal_dashes_duty', type=self.float, default=0.25)
        self.add_argument('--universal_dashes_bool', type=self.bool, default=False)
        self.add_argument('--universal_bool', type=self.bool, default=True)
        self.add_argument('--universal_bool_only', type=self.bool, default=False)

        # semicrease options
        self.add_argument('--semicrease_stroke_color', type=self.str, default=4294902015)  # Yellow
        self.add_argument('--semicrease_stroke_width', type=self.float, default=0.1)
        self.add_argument('--semicrease_dashes_len', type=self.float, default=1.0)
        self.add_argument('--semicrease_dashes_duty', type=self.float, default=0.25)
        self.add_argument('--semicrease_dashes_bool', type=self.bool, default=False)
        self.add_argument('--semicrease_bool', type=self.bool, default=True)
        self.add_argument('--semicrease_bool_only', type=self.bool, default=False)

        # cut options
        self.add_argument('--cut_stroke_color', type=self.str, default=16711935)  # Green
        self.add_argument('--cut_stroke_width', type=self.float, default=0.1)
        self.add_argument('--cut_dashes_len', type=self.float, default=1.0)
        self.add_argument('--cut_dashes_duty', type=self.float, default=0.25)
        self.add_argument('--cut_dashes_bool', type=self.bool, default=False)
        self.add_argument('--cut_bool', type=self.bool, default=True)
        self.add_argument('--cut_bool_only', type=self.bool, default=False)

        # vertex options
        self.add_argument('--vertex_stroke_color', type=self.str, default=255)  # Black
        self.add_argument('--vertex_stroke_width', type=self.float, default=0.1)
        self.add_argument('--vertex_radius', type=self.float, default=0.1)
        self.add_argument('--vertex_dashes_bool', type=self.bool, default=False)
        self.add_argument('--vertex_bool', type=self.bool, default=True)
        self.add_argument('--vertex_bool_only', type=self.bool, default=False)

        # here so we can have tabs - but we do not use it directly - else error
        self.add_argument('--active-tab', type=self.str, default='title')  # use a legitimate default

        self.path_tree = []
        self.edge_points = []
        self.vertex_points = []
        self.translate = (0, 0)

    def effect(self):
        """ Main function, called when the extension is run.
        """
        # bypass most style options if simulation mode is choosen
        self.check_simulation_mode()

        # check if any selected to print only some of the crease types:
        bool_only_list = [self.options.mountain_bool_only,
                          self.options.valley_bool_only,
                          self.options.edge_bool_only,
                          self.options.universal_bool_only,
                          self.options.semicrease_bool_only,
                          self.options.cut_bool_only,
                          self.options.vertex_bool_only]
        if sum(bool_only_list) > 0:
            self.options.mountain_bool = self.options.mountain_bool and self.options.mountain_bool_only
            self.options.valley_bool = self.options.valley_bool and self.options.valley_bool_only
            self.options.edge_bool = self.options.edge_bool and self.options.edge_bool_only
            self.options.universal_bool = self.options.universal_bool and self.options.universal_bool_only
            self.options.semicrease_bool = self.options.semicrease_bool and self.options.semicrease_bool_only
            self.options.cut_bool = self.options.cut_bool and self.options.cut_bool_only
            self.options.vertex_bool = self.options.vertex_bool and self.options.vertex_bool_only

        # construct dictionary containing styles
        self.create_styles_dict()

        # get paths for selected origami pattern
        self.generate_path_tree()

        # ~ accuracy = self.options.accuracy
        # ~ unit_factor = self.calc_unit_factor()
        # what page are we on
        # page_id = self.options.active_tab # sometimes wrong the very first time

        # get vertex points and add them to path tree
        vertex_radius = self.options.vertex_radius * self.calc_unit_factor()
        vertices = []
        self.vertex_points = list(set([i for i in self.vertex_points])) # remove duplicates
        for vertex_point in self.vertex_points:
            vertices.append(Path(vertex_point, style='p', radius=vertex_radius))
        self.path_tree.append(vertices)


        # Translate according to translate attribute
        g_attribs = {inkex.addNS('label', 'inkscape'): '{} Origami pattern'.format(self.options.pattern),
                       # inkex.addNS('transform-center-x','inkscape'): str(-bbox_center[0]),
                       # inkex.addNS('transform-center-y','inkscape'): str(-bbox_center[1]),
                     inkex.addNS('transform-center-x', 'inkscape'): str(0),
                     inkex.addNS('transform-center-y', 'inkscape'): str(0),
                     'transform': 'translate(%s,%s)' % self.translate}

        # add the group to the document's current layer
        if type(self.path_tree) == list and len(self.path_tree) != 1:
            self.topgroup = inkex.etree.SubElement(self.get_layer(), 'g', g_attribs)
        else:
            self.topgroup = self.get_layer()

        if len(self.edge_points) == 0:
            Path.draw_paths_recursively(self.path_tree, self.topgroup, self.styles_dict)
        elif self.options.edge_single_path:
            edges = Path(self.edge_points, 'e', closed=True)
            Path.draw_paths_recursively(self.path_tree + [edges], self.topgroup, self.styles_dict)
        else:
            edges = Path.generate_separated_paths(self.edge_points, 'e', closed=True)
            Path.draw_paths_recursively(self.path_tree + edges, self.topgroup, self.styles_dict)

        # self.draw_paths_recursively(self.path_tree, self.topgroup, self.styles_dict)

    # compatibility hack, "affect()" is replaced by "run()"
    def draw(self):
        try:
            self.run() # new
        except:
            self.affect() # old
        # close(self.tty)
        self.tty.close()

    # compatibility hack
    def get_layer(self):
        try:
            return self.svg.get_current_layer() # new
        except:
            return self.current_layer # old

    def check_simulation_mode(self):
        if not self.options.simulation_mode:
            pass
        else:
            self.options.mountain_stroke_color = 4278190335
            self.options.mountain_dashes_len = 0
            self.options.mountain_dashes_bool = False
            self.options.mountain_bool_only = False
            self.options.mountain_bool = True

            self.options.valley_stroke_color = 65535
            self.options.valley_dashes_len = 0
            self.options.valley_dashes_bool = False
            self.options.valley_bool_only = False
            self.options.valley_bool = True

            self.options.edge_stroke_color = 255
            self.options.edge_dashes_len = 0
            self.options.edge_dashes_bool = False
            self.options.edge_bool_only = False
            self.options.edge_bool = True

            self.options.universal_stroke_color = 4278255615
            self.options.universal_dashes_len = 0
            self.options.universal_dashes_bool = False
            self.options.universal_bool_only = False
            self.options.universal_bool = True

            self.options.cut_stroke_color = 16711935
            self.options.cut_dashes_len = 0
            self.options.cut_dashes_bool = False
            self.options.cut_bool_only = False
            self.options.cut_bool = True

            self.options.vertex_bool = False


    def create_styles_dict(self):
        """ Get stroke style parameters and use them to create the styles dictionary, used for the Path generation
        """
        unit_factor = self.calc_unit_factor()

        def create_style(type):
            style = {'draw': getattr(self.options,type+"_bool"),
                     'stroke': self.get_color_string(getattr(self.options,type+"_stroke_color")),
                     'fill': 'none',
                     'stroke-width': getattr(self.options,type+"_stroke_width") * unit_factor}
            if getattr(self.options,type+"_dashes_bool"):
                dash_gap_len = getattr(self.options,type+"_dashes_len")
                duty = getattr(self.options,type+"_dashes_duty")
                dash = (dash_gap_len * unit_factor) * duty
                gap = (dash_gap_len * unit_factor) * (1 - duty)
                style['stroke-dasharray'] = "{} {}".format(dash, gap)
            return style

        self.styles_dict = {'m': create_style("mountain"),
                            'v': create_style("valley"),
                            'u': create_style("universal"),
                            's': create_style("semicrease"),
                            'c': create_style("cut"),
                            'e': create_style("edge"),
                            'p': create_style("vertex")}

    def get_color_string(self, longColor, verbose=False):
        """ Convert the long into a #RRGGBB color value
            - verbose=true pops up value for us in defaults
            conversion back is A + B*256^1 + G*256^2 + R*256^3
        """
        # compatibility hack, no "long" in Python 3
        try:
            longColor = long(longColor)
            if longColor < 0: longColor = long(longColor) & 0xFFFFFFFF
            hexColor = hex(longColor)[2:-3]
        except:
            longColor = int(longColor)
            hexColor = hex(longColor)[2:-2]
            inkex.debug = inkex.utils.debug

        hexColor = '#' + hexColor.rjust(6, '0').upper()
        if verbose: inkex.debug("longColor = {}, hex = {}".format(longColor,hexColor))

        return hexColor
    
    def add_text(self, node, text, position, text_height=12):
        """ Create and insert a single line of text into the svg under node.
        """
        line_style = {'font-size': '%dpx' % text_height, 'font-style':'normal', 'font-weight': 'normal',
                     'fill': '#F6921E', 'font-family': 'Bitstream Vera Sans,sans-serif',
                     'text-anchor': 'middle', 'text-align': 'center'}
        line_attribs = {inkex.addNS('label','inkscape'): 'Annotation',
                       'style': simplestyle.formatStyle(line_style),
                       'x': str(position[0]),
                       'y': str((position[1] + text_height) * 1.2)
                       }
        line = inkex.etree.SubElement(node, inkex.addNS('text','svg'), line_attribs)
        line.text = text

           
    def calc_unit_factor(self):
        """ Return the scale factor for all dimension conversions.

            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        # namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        # doc_units = self.getUnittouu(str(1.0) + namedView.get(inkex.addNS('document-units', 'inkscape')))
        # backwards compatibility
        try:
            return self.svg.unittouu(str(1.0) + self.options.units)
        except:
            try:
                return inkex.unittouu(str(1.0) + self.options.units)
            except AttributeError:
                return self.unittouu(str(1.0) + self.options.units)






