#!/usr/bin/env python3
"""
A Inkscape extension to generate the pieces for a leather case that can be laser cut. 

The leather case is intended to be used with up to 5 mobile phones.
"""

import inkex
import math
from lxml import etree

class LeatherCase(inkex.EffectExtension):
    height = -1.0
    
    def add_arguments(self, pars):
        pars.add_argument('-w', '--width', type=float, default=80, help='Width (mm)')
        pars.add_argument('-x', '--height', type=float, default=165, help='Height (mm)')
        pars.add_argument('-d', '--depth', type=float, default=10, help='Depth (mm)')
        pars.add_argument('-H', '--heightMargin', type=float, default=10, help='Height Margin (mm)')
        pars.add_argument('-r', '--cornerRoundness', type=float, default=10, help='Corner Roundness (mm)')
        pars.add_argument('-i', '--divisions', type=int, default=2, help='Divisions')
        pars.add_argument('-a', '--claspAmount', default=1, help='Number of Clasps')
        pars.add_argument('-p', '--extraTongueLength', type=float, default=10, help='Extra Tongue Length (mm)')
        pars.add_argument('-t', '--tipTongueLength', type=float,default=40, help='Tip Tongue Length (mm)')
        pars.add_argument('-e', '--extraEdgeWidth', type=float, default=10, help='Extra Edge Width (mm)')
        pars.add_argument('-o', '--makeHoles', default="true", help='Make Holes')
        pars.add_argument('-g', '--groupObjects', default="false", help='Group Objects')

    def effect(self):
        width = self.options.width 
        height = self.options.height 
        depth = self.options.depth 
        heightMargin = self.options.heightMargin 
        cornerRoundness = self.options.cornerRoundness
        divisions = self.options.divisions
        oneClasp = self.options.claspAmount == "1"
        extraTongueLength = self.options.extraTongueLength
        tipTongueLength = self.options.tipTongueLength
        extraEdgeWidth = self.options.extraEdgeWidth
        makeHoles = self.options.makeHoles == "true"
        group = self.options.groupObjects == "true"
        
        parent = self.svg.get_current_layer()

        if group: 
            parent = etree.SubElement(parent, 'g')
            
        line_style = { 'stroke-width': self.svg.unittouu(str(0.1) + "mm"), 'stroke':'#FF0000', 'fill':'none'}

        verticalLine1Size = width - cornerRoundness - 1
        
        hole = ''
        
        if makeHoles:
            if oneClasp:
                hole = ' m ' + str((height + heightMargin * 2) / 2)  + ',' + str(extraTongueLength + 13) + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2'
            else:
                hole = (' m ' + str((height + heightMargin * 2) / 2 - 55)  + ',' + str(extraTongueLength + 13) + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2' +
                        ' m 110,0' + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2' 
                    )
            
        firstPiece_attribs = {'style' : str(inkex.Style(line_style)), 
                        'd' : 'M 0,0 l 0,' + str(verticalLine1Size) +
                        ' c 0,' + str(cornerRoundness / 2.0) + ' ' + str(cornerRoundness / 2) + ',' + str(cornerRoundness) + ' ' + str(cornerRoundness) + ',' + str(cornerRoundness) +
                        ' l ' + str(height + heightMargin * 2 - cornerRoundness * 2) + ',0' +
                        ' c ' + str(cornerRoundness / 2) + ',0 ' + str(cornerRoundness) + ',' + str(-cornerRoundness / 2) + ' ' + str(cornerRoundness) + ',' + str(-cornerRoundness) +
                        ' l 0,' + str(-verticalLine1Size) + ' Z' +
                        hole
                        }


        firstPiece = etree.SubElement(parent, inkex.addNS('path','svg'), firstPiece_attribs )
        
        
        # Intermediate pieces
        for x in range(1, divisions):
            intermediatePiece_attribs = {'style' : str(inkex.Style(line_style)),
                        'd' : 'M ' + str(10 + x*5) + ',' + str(10 + x*5) + ' l 0,' + str(verticalLine1Size) +
                        ' c 0,' + str(cornerRoundness / 2.0) + ' ' + str(cornerRoundness / 2) + ',' + str(cornerRoundness) + ' ' + str(cornerRoundness) + ',' + str(cornerRoundness) +
                        ' l ' + str(height + heightMargin * 2 - cornerRoundness * 2) + ',0' +
                        ' c ' + str(cornerRoundness / 2) + ',0 ' + str(cornerRoundness) + ',' + str(-cornerRoundness / 2) + ' ' + str(cornerRoundness) + ',' + str(-cornerRoundness) +
                        ' l 0,' + str(-verticalLine1Size) + ' Z' 
                        }


            intermediatePiece = etree.SubElement(parent, inkex.addNS('path','svg'), intermediatePiece_attribs )
        
        
        line_style2 = { 'stroke-width': self.svg.unittouu(str(0.1) + "mm"), 'stroke':'#00FF00', 'fill':'none'}
        plainTongueLength = depth * divisions + extraTongueLength - 1 + (divisions - 1)
        totalWidth = height + heightMargin * 2;
        hole = ''
        
        if makeHoles:
            if oneClasp:
                hole = ' m 30,' + str(-50 -(plainTongueLength + tipTongueLength - 10)) + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2'
            else:
                hole = (' m -25,' + str(-50 -(plainTongueLength + tipTongueLength - 10)) + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2' + 
                ' m 110,0' + ' c 1,0 2,1 2,2 0,1 -1,2 -2,2 -1,0 -2,-1 -2,-2 0,-1 1,-2 2,-2')
                
        
        if oneClasp:
            tongue = (' 0,' + str(-plainTongueLength) + 
                    ' c 0,' + str(-tipTongueLength / 2) + ' ' + str(-totalWidth / 4) + ',' + str(-tipTongueLength) + ' ' + str(-totalWidth / 2) + ',' + str(-tipTongueLength) + 
                    ' ' + str(-totalWidth / 4) + ',0 ' + str(-totalWidth / 2) + ',' + str(tipTongueLength / 2) + ' ' + str(-totalWidth / 2) + ',' + str(tipTongueLength) +
                    ' l 0,' + str(plainTongueLength)
                    )
        else:
            tongue = (' 0,' + str(-(plainTongueLength + tipTongueLength - cornerRoundness)) +
                      ' c 0,' + str(-cornerRoundness / 2) + ' ' + str(-cornerRoundness / 2) + ',' + str(-cornerRoundness) + ' ' + str(-cornerRoundness) + ',' + str(-cornerRoundness) +
                      ' l ' + str(-(height + heightMargin * 2 - cornerRoundness * 2)) + ',0' +
                      ' c ' + str(-cornerRoundness / 2) + ',0 ' + str(-cornerRoundness) + ',' + str(cornerRoundness / 2) + ' ' + str(-cornerRoundness) + ',' + str(cornerRoundness) +
                      ' l 0,' + str(plainTongueLength + tipTongueLength - cornerRoundness)
                      )
            
        secondPiece_attribs = {'style' : str(inkex.Style(line_style2)),
                        'd' : 'M -5,-4 l 0,' + str(verticalLine1Size - 1) +
                        ' c 0,' + str(cornerRoundness / 2.0) + ' ' + str(cornerRoundness / 2) + ',' + str(cornerRoundness) + ' ' + str(cornerRoundness) + ',' + str(cornerRoundness) +
                        ' l ' + str(height + heightMargin * 2 - cornerRoundness * 2) + ',0' +
                        ' c ' + str(cornerRoundness / 2) + ',0 ' + str(cornerRoundness) + ',' + str(-cornerRoundness / 2) + ' ' + str(cornerRoundness) + ',' + str(-cornerRoundness) +
                        ' l 0,' + str(-(verticalLine1Size-1)) + 
                        ' -1,-1' + ' 1,-1' +
                        tongue +
                        ' 1,1 -1,1 m ' + 
                        str(totalWidth / 2 - 30) +',-1 c 0.25,0 0.5,0.25 0.5,0.5 0,0.25 -0.25,0.5 -0.5,0.5 -0.25,0 -0.5,-0.25 -0.5,-0.5 0,-0.25 0.25,-0.5 0.5,-0.5 ' +
                        'm 60,0 c 0.25,0 0.5,0.25 0.5,0.5 0,0.25 -0.25,0.5 -0.5,0.5 -0.25,0 -0.5,-0.25 -0.5,-0.5 0,-0.25 0.25,-0.5 0.5,-0.5' +
                        'm 0,50 c 0.25,0 0.5,0.25 0.5,0.5 0,0.25 -0.25,0.5 -0.5,0.5 -0.25,0 -0.5,-0.25 -0.5,-0.5 0,-0.25 0.25,-0.5 0.5,-0.5'
                        'm -60,0 c 0.25,0 0.5,0.25 0.5,0.5 0,0.25 -0.25,0.5 -0.5,0.5 -0.25,0 -0.5,-0.25 -0.5,-0.5 0,-0.25 0.25,-0.5 0.5,-0.5' +
                        hole
                        }
        
        secondPiece = etree.SubElement(parent, inkex.addNS('path','svg'), secondPiece_attribs )
        
        line_style3 = { 'stroke-width': self.svg.unittouu(str(0.1) + "mm"), 'stroke':'#0000FF', 'fill':'none'}
        edgeLength = (width - cornerRoundness) * 2 + height + heightMargin * 2 - cornerRoundness * 2 + 3.14159 * cornerRoundness
        edgeWidth = depth * divisions + divisions - 1 + extraEdgeWidth
        
        thirdPiece_attribs = {'style' : str(inkex.Style(line_style3)),
                        'd' : 'M 5,5 l 0,' + str(edgeWidth) +
                        ' ' + str(edgeLength) + ',0' +
                        ' 0,' + str(-edgeWidth) + ' Z'
                        }
        
        thirdPiece = etree.SubElement(parent, inkex.addNS('path','svg'), thirdPiece_attribs )
        
        line_style4 = { 'stroke-width': self.svg.unittouu(str(0.1) + "mm"), 'stroke':'#FF00FF', 'fill':'none'}
        edgeLength = 70
        edgeWidth = 60
        
        fourthPiece_attribs = {'style' : str(inkex.Style(line_style4)),
                        'd' : 'M 10,10 l 0,' + str(edgeWidth) +
                        ' ' + str(edgeLength) + ',0' +
                        ' 0,' + str(-edgeWidth) + ' Z'
                        }
        
        fourthPiece = etree.SubElement(parent, inkex.addNS('path','svg'), fourthPiece_attribs )
              
if __name__ == '__main__':
    LeatherCase().run()