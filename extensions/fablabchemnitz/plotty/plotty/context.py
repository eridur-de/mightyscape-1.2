from math import *
import sys

class GCodeContext:
    def __init__(self, xy_feedrate, delay, pen_up, pen_down, x_home, y_home):
      self.xy_feedrate = xy_feedrate
      self.delay = delay
      self.pen_up = pen_up
      self.pen_down = pen_down
      self.x_home = x_home
      self.y_home = y_home
      
      self.drawing = False
      self.last = None

      self.sheet_header = [
        "{}; pen up".format(self.pen_up),
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
        "G28 X Y; Home the axes",
        "G21; metric ftw",
        "G90; absolute mode",
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
        "G1 X40; move aside to avoid collisions with magnets",
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
      ]

      self.sheet_footer = [
        "{}; pen up".format(self.pen_up),
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
        "G1 X0 Y0 F{:.2f}".format(self.xy_feedrate),
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
        "G1 X{:.2f} Y{:.2f} F{:.2f}; go home".format(self.x_home, self.y_home, self.xy_feedrate),
        "{}; pen up".format(self.pen_up),
        "G4 P{}; wait {}ms".format(self.delay, self.delay),
        "G28 X Y; home XY",
        "{}; pen down (sink into counter-magnet with hole)".format(self.pen_down),
        "M18; drives off",
      ]

      self.codes = []

    def generate(self):
      codesets = []
      codesets.append(self.sheet_header)
      codesets.append(self.codes)
      codesets.append(self.sheet_footer)

      for codeset in codesets:
        for line in codeset:
          print(line)

    def start(self):
      self.codes.append("G4 P{}; wait {}ms".format(self.delay, self.delay))
      self.codes.append("{}; pen down".format(self.pen_down))
      self.drawing = True

    def go_to_point(self, x, y, stop=False):
      if self.last == (x,y):
        return
      else:
        if self.drawing:
            self.codes.append("G4 P{}; wait {}ms".format(self.delay, self.delay))
            self.codes.append("{}; pen up".format(self.pen_up))
            self.codes.append("G4 P{}; wait {}ms".format(self.delay, self.delay))
            self.drawing = False
        self.codes.append("G1 X{:.2f} Y{:.2f} F{:.2f}".format(x, y, self.xy_feedrate))
      self.last = (x,y)

    def draw_to_point(self, x, y, stop=False):
      if self.last == (x,y):
          return
      else:
        if self.drawing == False:
            self.codes.append("G4 P{}; wait {}ms".format(self.delay, self.delay))
            self.codes.append("{}; pen down".format(self.pen_down))
            self.codes.append("G4 P{}; wait {}ms".format(self.delay, self.delay))
            self.drawing = True
        self.codes.append("G1 X{:.2f} Y{:.2f} F{:.2f}".format(x, y, self.xy_feedrate))
      self.last = (x,y)