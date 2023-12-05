#!/usr/bin/env python3

import sys
import inkex
import os
import base64
import urllib.request as urllib
from PIL import Image
from io import BytesIO
from lxml import etree

"""
Extension for InkScape 1.X
Features
 - will vectorize your beautiful image into a more beautiful SVG trace with separated infills(break apart into single surfaces like a puzzle)
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 18.08.2020
Last patch: 24.04.2021
License: GNU GPL v3

Used version of imagetracerjs: https://github.com/jankovicsandras/imagetracerjs/commit/4d0f429efbb936db1a43db80815007a2cb113b34

"""

class Imagetracerjs(inkex.EffectExtension):

    def checkImagePath(self, element):
        xlink = element.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = element.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--keeporiginal", type=inkex.Boolean, default=False, help="Keep original image on canvas")
        pars.add_argument("--ltres", type=float, default=1.0, help="Error treshold straight lines")
        pars.add_argument("--qtres", type=float, default=1.0, help="Error treshold quadratic splines")
        pars.add_argument("--pathomit", type=int, default=8, help="Noise reduction - discard edge node paths shorter than")         
        pars.add_argument("--rightangleenhance", type=inkex.Boolean, default=True, help="Enhance right angle corners")
        pars.add_argument("--colorsampling", default="2",help="Color sampling")      
        pars.add_argument("--numberofcolors", type=int, default=16, help="Number of colors to use on palette")
        pars.add_argument("--mincolorratio", type=int, default=0, help="Color randomization ratio")
        pars.add_argument("--colorquantcycles", type=int, default=3, help="Color quantization will be repeated this many times")           
        pars.add_argument("--layering", default="0",help="Layering")
        pars.add_argument("--strokewidth", type=float, default=1.0, help="SVG stroke-width")
        pars.add_argument("--linefilter", type=inkex.Boolean, default=False, help="Noise reduction line filter")
        #pars.add_argument("--scale", type=float, default=1.0, help="Coordinate scale factor")
        pars.add_argument("--roundcoords", type=int, default=1, help="Decimal places for rounding")
        pars.add_argument("--viewbox", type=inkex.Boolean, default=False, help="Enable or disable SVG viewBox")
        pars.add_argument("--desc", type=inkex.Boolean, default=False, help="SVG descriptions")
        pars.add_argument("--blurradius", type=int, default=0, help="Selective Gaussian blur preprocessing")
        pars.add_argument("--blurdelta", type=float, default=20.0, help="RGBA delta treshold for selective Gaussian blur preprocessing")
  
    def effect(self):
                            
        # internal overwrite for scale:
        self.options.scale = 1.0
    
        if len(self.svg.selected) > 0:
            images = self.svg.selection.filter(inkex.Image).values()
            if len(images) > 0:
                for image in images:
                    self.path = self.checkImagePath(image)  # This also ensures the file exists
                    if self.path is None:  # check if image is embedded or linked
                        image_string = image.get('{http://www.w3.org/1999/xlink}href')
                        # find comma position
                        i = 0
                        while i < 40:
                            if image_string[i] == ',':
                                break
                            i = i + 1
                        img = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
                    else:
                        img = Image.open(self.path)
                    
                    # Write the embedded or linked image to temporary directory
                    if os.name == "nt":
                         exportfile = "imagetracerjs.png"
                    else:
                         exportfile ="/tmp/imagetracerjs.png"
                         
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(exportfile, "png")
           
                    nodeclipath = os.path.join("imagetracerjs-master", "nodecli", "nodecli.js")
                    
                    ## Build up imagetracerjs command according to your settings from extension GUI
                    command = "node --trace-deprecation " # "node.exe" or "node" on Windows or just "node" on Linux
                    if os.name=="nt": # your OS is Windows. We handle path separator as "\\" instead of unix-like "/"
                        command += str(nodeclipath).replace("\\", "\\\\")
                    else:
                        command += str(nodeclipath)
                    command += " " + exportfile
                    command += " ltres "             + str(self.options.ltres)
                    command += " qtres "             + str(self.options.qtres)
                    command += " pathomit "          + str(self.options.pathomit)
                    command += " rightangleenhance " + str(self.options.rightangleenhance).lower()
                    command += " colorsampling "     + str(self.options.colorsampling)
                    command += " numberofcolors "    + str(self.options.numberofcolors) 
                    command += " mincolorratio "     + str(self.options.mincolorratio)         
                    command += " numberofcolors "    + str(self.options.numberofcolors) 
                    command += " colorquantcycles "  + str(self.options.colorquantcycles)         
                    command += " layering "          + str(self.options.layering)          
                    command += " strokewidth "       + str(self.options.strokewidth)        
                    command += " linefilter "        + str(self.options.linefilter).lower()        
                    command += " scale "             + str(self.options.scale)   
                    command += " roundcoords "       + str(self.options.roundcoords)   
                    command += " viewbox "           + str(self.options.viewbox).lower()
                    command += " desc "              + str(self.options.desc).lower()
                    command += " blurradius "        + str(self.options.blurradius)   
                    command += " blurdelta "         + str(self.options.blurdelta)  
    
                    # Create the vector traced SVG file
                    with os.popen(command, "r") as tracerprocess:
                        result = tracerprocess.read()
                        if "was saved!" not in result:
                            self.msg("Error while processing input: " + result)
                            self.msg("Check the image file (maybe convert and save as new file) and try again.")
                            self.msg("\nYour parser command:")
                            self.msg(command)
    
    
                    # proceed if traced SVG file was successfully created
                    if os.path.exists(exportfile + ".svg"):
                        # Delete the temporary png file again because we do not need it anymore
                        if os.path.exists(exportfile):
                            os.remove(exportfile)
                        
                        # new parse the SVG file and insert it as new group into the current document tree
                        doc = etree.parse(exportfile + ".svg").getroot()
                        newGroup = self.document.getroot().add(inkex.Group())
                        trace_width = None
                        trace_height = None
                        if doc.get('width') is not None and doc.get('height') is not None:
                            trace_width = doc.get('width')
                            trace_height = doc.get('height')
                        else:
                            viewBox = doc.get('viewBox') #eg "0 0 700 600"
                            trace_width = viewBox.split(' ')[2]
                            trace_height = viewBox.split(' ')[3]
                        
                        # add transformation to fit previous XY coordinates and width/height
                        # image might also be influenced by other transformations from parent:
                        parent = image.getparent()
                        if parent is not None and parent != self.document.getroot():
                            tpc = parent.composed_transform()
                            x_offset = tpc.e
                            y_offset = tpc.f
                        else:
                            x_offset = 0.0
                            y_offset = 0.0              
                        img_w = image.get('width')
                        img_h = image.get('height')
                        img_x = image.get('x')
                        img_y = image.get('y')                                        
                        if img_w is not None and img_h is not None and img_x is not None and img_y is not None:
                            #if width/height are not unitless but end with px, mm, in etc. we have to convert to a float number
                            if img_w[-1].isdigit() is False:
                                img_w = self.svg.uutounit(img_w)
                            if img_h[-1].isdigit() is False:
                                img_h = self.svg.uutounit(img_h)
                            
                            transform = "matrix({:1.6f}, 0, 0, {:1.6f}, {:1.6f}, {:1.6f})"\
                            .format(float(img_w) / float(trace_width), float(img_h) / float(trace_height), float(img_x) + x_offset, float(img_y) + y_offset)
                            newGroup.attrib['transform'] = transform
                        else:
                            t = image.composed_transform()
                            img_w = t.a
                            img_h = t.d 
                            img_x = t.e
                            img_y = t.f
                            transform = "matrix({:1.6f}, 0, 0, {:1.6f}, {:1.6f}, {:1.6f})"\
                            .format(float(img_w) / float(trace_width), float(img_h) / float(trace_height), float(img_x) + x_offset, float(img_y) + y_offset)
                            newGroup.attrib['transform'] = transform
           
                        for child in doc.getchildren():
                            newGroup.append(child)
    
                        # Delete the temporary svg file
                        if os.path.exists(exportfile + ".svg"):
                            os.remove(exportfile + ".svg")
                    
                    #remove the old image or not                    
                    if self.options.keeporiginal is not True:
                        image.delete()
            else:
                self.msg("No images found in selection! Check if you selected a group instead.")      
        else:
            self.msg("Selection is empty. Please select one or more images.")  

if __name__ == '__main__':
    Imagetracerjs().run()