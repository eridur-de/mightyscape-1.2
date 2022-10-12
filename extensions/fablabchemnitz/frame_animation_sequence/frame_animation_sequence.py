#!/usr/bin/env python3
#
# Copyright (C) 2021 roberta bennett repeatingshadow@protonmail.com
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
"""
Create svg path animation as SMIL from frames.

Place each frame of the animation in a layer named 'frame'.
Each of these layers should have the same number of paths,
and each path should have the same number of points as the corresponding
path in other layers.
Note if there are more than one path in the frames, the Z order of the paths
must match. It helps to use the XML editor option to observe the z order.

The animation is applied to the paths in the first layer in the sequence, so the
properties of that layer are used. In particular, the first layer ought to be set 
visible. 

Animations with different numbers of frames can be put into different sequences, 
named 'sequence', using sub-groups:

Layers:
 not_animated_layer1
 sequence
  frame
   path1a
   path2a
  frame
   path1b
   path2b
  frame
   path1c
   path2c
  frame
   path1d
   path2d
 sequence
  frame
  frame
  frame 

Layer names must contain 'frame' and groups names contain 'sequence',
eg, frame1 frame 2 frame 30, sequence 1, rythm sequence, rocket sequence  


"""

import inkex

class AnimateElement(inkex.BaseElement):
    """animation Elements do not have a visible representation on the canvas"""
    tag_name = 'animate'
    @classmethod
    def new(cls, **attrs):
        return super().new( **attrs)
        
        
class AnimationExtension(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--delete", type=inkex.Boolean, help="Remove frames")
        pars.add_argument("--begin_str", default="0", help="begin string: eg 0;an2.end;an3.begin")
        pars.add_argument("--repeat_str", default="indefinite", help="indefinite or an integer")
        pars.add_argument("--dur_str",  default="7.9", help="duration in seconds. Do not decorate with units")         
          

    def crunchFrames(self,frames):
        if frames is None:
            raise inkex.AbortExtension("layer named frame does not exist.")
        frame0paths = frames[0].findall('svg:path')
        Dlists = ["{}".format(p.get_path()) for p in frame0paths]
        for frame in frames[1:]:
            paths = frame.findall("svg:path")
            for i, p in enumerate(paths):
                Dlists[i] += ";\n{}".format(p.get_path())
        for i, dl in enumerate(Dlists):    
            animel = AnimateElement(
                attributeName="d",
                attributeType="XML",
                begin=self.options.begin_str,
                dur=self.options.dur_str,
                repeatCount=self.options.repeat_str,
                values=dl)
            frame0paths[i].append(animel)
        for frame in frames[1:]:
            if self.options.delete:
                frame.delete()
        return         


    def effect(self):
        sequences = [ elem for elem in self.svg.findall("svg:g[@inkscape:label]")
                          if "sequence" in (elem.get('inkscape:label'))
                    ]
        if len(sequences)==0:
            frames = [ elem for elem in self.svg.findall("svg:g[@inkscape:label]")
                            if "frame" in (elem.get('inkscape:label'))
                     ]
            self.crunchFrames(frames)
            return
        for sequence in sequences:
            frames = [ elem for elem in sequence.findall("svg:g[@inkscape:label]")
                            if "frame" in (elem.get('inkscape:label'))
                     ]
            self.crunchFrames(frames)     
     
                    
if __name__ == '__main__':
    AnimationExtension().run()