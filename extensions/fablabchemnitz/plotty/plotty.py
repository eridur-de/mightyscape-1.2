#!/usr/bin/env python3

import inkex
from math import *
from plotty.context import GCodeContext
from plotty.svg_parser import SvgParser
from plotty.routefinder import RouteFinder

class Plotty(inkex.Effect):
  def __init__(self):
    inkex.Effect.__init__(self)
    self.arg_parser.add_argument("--pen-up", type=str, dest="pen_up", default="M340 P0 S500", help="Pen Up Command")
    self.arg_parser.add_argument("--pen-down", type=str, dest="pen_down", default="M340 P0 S1500", help="Pen Down Command")
    self.arg_parser.add_argument("--delay", type=float, dest="delay", default="100.0", help="Delay after before down command before movement in milliseconds")
    self.arg_parser.add_argument("--xy-feedrate", type=float, dest="xy_feedrate", default="7000.0", help="XY axes feedrate in mm/min")
    self.arg_parser.add_argument("--x-home", type=float, dest="x_home", default="0.0", help="Starting X position")
    self.arg_parser.add_argument("--y-home", type=float, dest="y_home", default="0.0", help="Starting Y position")
    self.arg_parser.add_argument("--pause-on-layer-change", type=str, dest="pause_on_layer_change", default="false", help="Pause on layer changes.")
    self.arg_parser.add_argument("--tab", type=str, dest="tab")
    self.gcode_output = ""

  def effect(self):
    self.context = GCodeContext(self.options.xy_feedrate,
                           self.options.delay, 
                           self.options.pen_up, 
                           self.options.pen_down,
                           self.options.x_home, 
                           self.options.y_home
                           )
    parser = SvgParser(self.document.getroot(), self.options.pause_on_layer_change)
    parser.parse()

    if len(parser.entities) > 1:
      distance_matrix = parser.get_distance_matrix()

      route_finder = RouteFinder(distance_matrix, parser.entities, iterations=5)
      best_distance, best_route = route_finder.solve()

      for entity in best_route:
        entity.get_gcode(self.context)
    else:
      for entity in parser.entities:
        entity.get_gcode(self.context)
    
    self.gcode_output = self.context.generate()

  def save(self, stream):
    output = self.gcode_output if self.gcode_output else "(Error: G-code generation failed or yielded empty output)"
    stream.write(output.encode('utf-8'))

if __name__ == '__main__':
  Plotty().run()