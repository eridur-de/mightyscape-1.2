#!/usr/bin/env python3

'''
svgPianoScale.py
Inkscape generator plugin for automatic creation schemes of musical scales and chords.

Copyright (C) 2011 Iljin Alexender <piroxiljin(a)gmail.com>

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

__version__ = "1.0.1"
# Original by Alexander Iljin
# Some mods to 0.91 by Neon22 2016

import inkex
import re
import math
from datetime import *
from lxml import etree

notes =        ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
keys_color =   ('W', 'B', 'W',  'B', 'W', 'W',  'B',  'W', 'B',  'W', 'B',  'W') # 12 notes
keys =         {'C':'W', 'C#':'B',  'D':'W', 'D#':'B',  'E':'W', 'F':'W', 'F#':'B', 'G':'W',
                'G#':'B',  'A':'W', 'A#':'B',  'B':'W' }
keys_numbers = {'C':'0', 'C#':'0',  'D':'1', 'D#':'1',  'E':'2', 'F':'3', 'F#':'3', 'G':'4',
                'G#':'4',  'A':'5', 'A#':'5',  'B':'6' }
keys_order =   {'C':'0', 'C#':'1',  'D':'2', 'D#':'3',  'E':'4', 'F':'5', 'F#':'6', 'G':'7',
                'G#':'8',  'A':'9', 'A#':'10',  'B':'11' }

intervals = ("2212221", "2122212", "1222122", "2221221", "2212212", "2122122", "1221222")

# Drawing style
White = '#ffffff'
Black = '#000000'
Marker_color =  '#b3b3b3'  # Ellipse fill color

helpSheets = [["Ionian (major) scale",          "2212221"],
              ["Dorian scale",                  "2122212"],
              ["Phrygian scale",                "1222122"],
              ["Lydian scale",                  "2221221"],
              ["Mixolydian scale",              "2212212"],
              ["Aeolian (natural minor) scale", "2122122"],
              ["Locrian scale",                 "1221222"]
             ]

def keyNumberFromNote(note):
    """ Given a note such as C1 or C#1 where:
        - the 1 defines the octave (starts from 1)
        - the # defines note is sharp
        return the notes numeric value, from 0
    """
    note = note.upper().strip()
    octave = 1
    if '#' in note : # sharp
        if (len(note) > 2) and note[2].isdigit():
                octave = int(note[2])
        note = note[0:2]
    else:
        if (len(note) > 1) and note[1].isdigit():
                octave = int(note[1])
        note = note[0]
    return int(keys_order[note])+(octave-1)*12

def whiteKeyCountInRange(firstNote, lastNote):
    """ Count the White notes between 
        - used by createPiano 
    """
    count = 0
    for key in range(firstNote, lastNote+1):
        if keys_color[key%12] == "W":
            count += 1
    return count

def colorFromKey(keyNumber):
    """ Return B or W based on key. Use octaves 
        - used by create_markers 
    """
    return keys_color[keyNumber%12]
    
class PianoScale(inkex.EffectExtension):
    marker_radius_factor = 0.42   # position marker in X on piano key
    marker_y_offset_factor = 0.92 # position marker in Y

    def add_arguments(self, pars):
        pars.add_argument("--firstNote", default="C1")
        pars.add_argument("--lastNote", default="B2")
        pars.add_argument("--tab")
        pars.add_argument("--intervals")
        pars.add_argument("--keynote")
        pars.add_argument("--scale", type=int)
        pars.add_argument("--helpSheet", type=int)

    def calculate_size_and_positions(self):
        " Determine page size and define key dimensions "
        self.doc_width = self.svg.unittouu(self.document.getroot().get('width'))
        self.doc_height = self.svg.unittouu(self.document.getroot().get('height'))
        # Size of the keys
        self.black_key_width = self.svg.unittouu('3.6 mm');
        self.white_key_width = self.svg.unittouu('6 mm');
        self.black_key_height = self.svg.unittouu('18 mm');
        self.white_key_height = self.svg.unittouu('30 mm');

    def createBlackKey(self, parent, number):
        """ Insert Black key into scene
            - number times width is X position
        """
        key_atts = {'x':str(self.white_key_width * number + self.white_key_width - self.black_key_width/2),
                    'y':'0.0',
                    'width':str(self.black_key_width),
                    'height':str(self.black_key_height),
                    'ry':str(self.svg.unittouu('0.7 mm')),
                    'style':'fill:%s;stroke:%s;stroke-width:%s;stroke-opacity:1;fill-opacity:1' %(Black, Black, self.svg.unittouu('0.1 mm')) }
        white_key = etree.SubElement(parent, 'rect', key_atts)

    def createWhiteKey(self, parent, number):
        """ Insert White key into scene
            - number times width is X position
        """
        key_atts = {'x':str(self.white_key_width * number),
                    'y':'0.0',
                    'width':str(self.white_key_width),
                    'height':str(self.white_key_height),
                    'ry':str(self.svg.unittouu('0.7 mm')),
                    'style':'fill:%s;stroke:%s;stroke-width:%s;stroke-opacity:1;fill-opacity:1' % (White, Black, self.svg.unittouu('0.25 mm'))}
        white_key = etree.SubElement(parent, 'rect', key_atts)

    def createKeyByNumber(self, parent, keyNumber):
        """ Use Keynumber to detrmine octave and position within
            - draw correct key on basis of note in octave sequence.
        """
        octave = math.floor(keyNumber / 12) + 1
        note = keyNumber % 12
        key =  int(keys_numbers[notes[note]])
        if keys_color[note] == "W":
            self.createWhiteKey(parent, key+7*(octave-1))
        else:
            self.createBlackKey(parent, key+7*(octave-1))

    def createKeyInRange(self, parent, firstKeyNum, lastKeyNum):
        """ Draw keys in a range 
            - do it twice so Black keys are drawn over White ones
        """
        for key in range(firstKeyNum, lastKeyNum+1):
            if keys_color[key % 12] == 'W':
                self.createKeyByNumber(parent, key)
        for key in range(firstKeyNum, lastKeyNum+1):
            if keys_color[key % 12] == 'B':
                self.createKeyByNumber(parent, key)

    def createPiano(self, parent):
        """ Draw keys defined by options
            - add Piano 'box' above
        """
        firstKeyNumber = keyNumberFromNote(self.options.firstNote)
        lastKeyNumber =  keyNumberFromNote(self.options.lastNote)
        self.createKeyInRange(parent, firstKeyNumber, lastKeyNumber)
        # Draw the Piano box above keys
        rectBump = (self.white_key_width - self.black_key_width/2)
        rectBump = self.svg.unittouu('1 mm')
        rect_x1 = self.white_key_width * (whiteKeyCountInRange(0, firstKeyNumber)-1)- rectBump
        rect_y1 = self.svg.unittouu('-3 mm')
        rect_width = self.white_key_width * (whiteKeyCountInRange(firstKeyNumber, lastKeyNumber)) + rectBump*2
        rect_height = self.svg.unittouu('4 mm')
        rect_atts = {'x':str(rect_x1), 
                     'y':str(rect_y1), 
                     'width':str(rect_width), 
                     'height':str(rect_height),
                     'ry':str(0),
                     'style':'fill:%s;stroke:none;fill-opacity:1' %(White) }
        rect = etree.SubElement(parent, 'rect', rect_atts)
        path_atts = {'style':'fill:%s;stroke:%s;stroke-width:%s;stroke-opacity:1' %(White, Black, self.svg.unittouu('0.25 mm')),
                     'd':'m %s,%s l 0,%s %s,0 0, %s' % (rect_x1, rect_y1, rect_height, rect_width, -rect_height) }
        path = etree.SubElement(parent, 'path', path_atts)

    def createMarkerAt(self, parent, x, y, radius, markerText):
        " Draw a Marker at position x,y "
        markerGroup = etree.SubElement(parent, 'g')
        # should replace with svg:circle
        ellipce_atts = {
            inkex.addNS('cx','sodipodi'):str(x),
            inkex.addNS('cy','sodipodi'):str(y),
            inkex.addNS('rx','sodipodi'):str(radius),
            inkex.addNS('ry','sodipodi'):str(radius),
            inkex.addNS('type','sodipodi'):'arc',
                'd':'m %s,%s a %s,%s 0 1 1 %s,0 %s,%s 0 1 1 %s,0 z' %(x+radius, y, x, y, -radius*2, x, y, radius*2),
                'style':'fill:%s;stroke:%s;stroke-width:%s;stroke-opacity:1;fill-opacity:1' %(Marker_color, Black, self.svg.unittouu('0.125 mm'))}
        ellipse = etree.SubElement(markerGroup, 'path', ellipce_atts)
        # draw the text
        textstyle = {'font-size': '4px',
                     'font-family': 'arial',
                     'text-anchor': 'middle',
                     'text-align': 'center',
                     'fill': Black }
        text_atts = {'style':str(inkex.Style(textstyle)),
                     'x': str(x),
                     'y': str(y + radius*0.5) }
        text = etree.SubElement(markerGroup, 'text', text_atts)
        text.text = str(markerText)

    def createMarkerOnWhite(self, parent, whiteNumber, markerText):
        " Position Marker on White key "
        radius = self.white_key_width * self.marker_radius_factor
        center_x = self.white_key_width * (whiteNumber + 0.5)
        center_y = self.white_key_height * self.marker_y_offset_factor - radius 
        self.createMarkerAt(parent, center_x, center_y, radius, markerText)

    def createMarkerOnBlack(self, parent, whiteNumber, markerText):
        " Position Marker on Black key "
        radius = self.white_key_width * self.marker_radius_factor
        center_x = self.white_key_width * (whiteNumber + 1)
        center_y = self.black_key_height * self.marker_y_offset_factor - radius 
        self.createMarkerAt(parent, center_x, center_y, radius, markerText)

    def createMarkers(self, parent, keyNumberList, markerTextList):
        current=0
        for key in keyNumberList:
            octave = math.floor(key/12)
            if colorFromKey(key) == "W":
                self.createMarkerOnWhite(parent, int(keys_numbers[notes[key%12]])+(octave)*7, markerTextList[current])
            else:
                self.createMarkerOnBlack(parent, int(keys_numbers[notes[key%12]])+(octave)*7, markerTextList[current])
            current += 1;

    def createMarkersFromIntervals(self, parent, intervals):
        """ Check intervals.
            Then gather keys which need markers
             and the text for each one.
            Make markers.
        """
        # Check intervals are well defined and markers are legit.
        intervalSumm = sum([int(i) for i in intervals])
        if intervalSumm != 12:
            inkex.debug("Warning! Scale must have 12 half-tones. But %d defined."%(intervalSumm))
            
        firstKeyNum = keyNumberFromNote(self.options.firstNote)
        lastKeyNum  = keyNumberFromNote(self.options.lastNote)

        markedKeys = ()
        markerText = ()
        if keyNumberFromNote(self.options.keynote) in range(firstKeyNum, lastKeyNum+1):
            currentKey = keyNumberFromNote(self.options.keynote)
            markedKeys = (currentKey,)
            markerText = ('1',)
            currentInterval = 0
            for key in range(keyNumberFromNote(self.options.keynote), lastKeyNum+1):
                if key - currentKey == int(intervals[currentInterval]):
                    markedKeys += (key,)
                    currentInterval += 1
                    markerText += (str(currentInterval+1),)
                    if currentInterval == len(intervals):
                        currentInterval = 0
                    currentKey = key
            #
            currentKey = keyNumberFromNote(self.options.keynote)
            currentInterval = len(intervals)-1
            for key in range(keyNumberFromNote(self.options.keynote), firstKeyNum-1, -1):
                if currentKey - key == int(intervals[currentInterval]):
                    markedKeys += (key,)
                    markerText += (str(currentInterval+1),)
                    currentInterval -= 1
                    if currentInterval == -1:
                        currentInterval = len(intervals)-1
                    currentKey = key
        # make the markers
        self.createMarkers(parent, markedKeys, markerText)

    def createHelpSheet(self, parent, title, intervals):
        """ Draw big text Label and draw 12 different scales
        """
        textstyle = {'font-size': '22px',
                     'font-family': 'arial',
                     'text-anchor': 'middle',
                     'text-align': 'center',
                     'fill': Black }
        text_atts = {'style':str(inkex.Style(textstyle)),
                     'x': str( self.doc_width/2 ),
                     'y': str( self.black_key_height) }
        text = etree.SubElement(parent, 'text', text_atts)
        text.text = title
        #
        for i in range(0, 12):
            # override the ui input value for each note in the scale
            self.options.keynote = notes[i]
            # calculate the piano position on the page
            if keys_color[i] == "W":
                t = 'translate(%s,%s)' % (self.doc_width/2,
                                          self.doc_height - self.white_key_height*1.5 
                                          - (self.white_key_height + self.svg.unittouu('7 mm')) * int(keys_numbers[self.options.keynote]) )
            else: # Black key
                t = 'translate(%s,%s)' % (self.svg.unittouu('7 mm'), 
                                          self.doc_height- self.white_key_height*1.5
                                          - (self.white_key_height+self.svg.unittouu('7 mm')) * int(keys_numbers[self.options.keynote]) - self.white_key_height*0.5 )
            group = etree.SubElement(parent, 'g', { 'transform':t})
            # Create a piano using that keynote in the Scale (defined in intervals)
            self.createPiano(group)
            self.createMarkersFromIntervals(group, intervals)

    def effect(self):
        self.calculate_size_and_positions()
        parent = self.document.getroot()
        if str(self.options.tab) == "scale":
            t = 'translate(%s,%s)' % (self.svg.namedview.center[0],  self.svg.namedview.center[1])
            group = etree.SubElement(parent, 'g', { 'transform':t})
            self.createPiano(group)
            self.createMarkersFromIntervals(group, intervals[self.options.scale])
        elif str(self.options.tab) == "helpSheet":
            t = 'translate(%s,%s)' % (self.svg.unittouu('5 mm'), self.svg.unittouu('5 mm'))
            group = etree.SubElement(parent, 'g', { 'transform':t})
            scale_index = self.options.helpSheet
            self.createHelpSheet(group, helpSheets[scale_index][0], helpSheets[scale_index][1])
        else: # direct intervals
            t = 'translate(%s,%s)' % (self.svg.namedview.center[0], self.svg.namedview.center[1])
            group = etree.SubElement(parent, 'g', { 'transform':t})
            self.createPiano(group)
            self.createMarkersFromIntervals(group, self.options.intervals)

if __name__ == '__main__':
    PianoScale().run()