#!/usr/bin/env python3

import sys
import inkex
import os
import base64
import urllib.request as urllib
from PIL import Image
from io import BytesIO
from lxml import etree
from inkex import Color

"""
Extension for InkScape 1.X
Features
 - Primitive - Reproducing images with geometric primitives written in Go.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 21.08.2020
Last patch: 23.08.2020
License: GNU GPL v3

Used version of Primitive: https://github.com/fogleman/primitive/commit/0373c216458be1c4b40655b796a3aefedf8b7d23
"""

class Primitive (inkex.EffectExtension):

    def rgbToHex(self, pickerColor):
        longcolor = int(pickerColor)
        if longcolor < 0:
            longcolor = longcolor & 0xFFFFFFFF
        return '#' + format(longcolor >> 8, '06X')

    def checkImagePath(self, node):
        xlink = node.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = node.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path
  
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--keeporiginal", type=inkex.Boolean, default=False, help="Keep original image on canvas")
        pars.add_argument("--cliprect", type=inkex.Boolean, default=True, help="Draw clipping rectangle")
        pars.add_argument("--n", type=int, default=100, help="Number of shapes")
        pars.add_argument("--m", default=1, help="Mode")
        pars.add_argument("--rep", type=int, default=0,help="Extra shapes/iteration")
        pars.add_argument("--r", type=int, default=256, help="Resize to size before processing (px)")
        pars.add_argument("--s", type=int, default=1024, help="Output image size (px)")    
        pars.add_argument("--a", type=int, default=128, help="Color alpha")
        pars.add_argument("--bg_enabled", type=inkex.Boolean, default=True, help="Use average starting background color")
        pars.add_argument("--bg", type=Color, default=255, help="Starting background color")
        pars.add_argument("--j", type=int, default=0, help="Number of parallel workers") 
  
    def effect(self):
    
        if (self.options.ids):
            for node in self.svg.selected.values():
                if node.tag == inkex.addNS('image', 'svg'):
                    self.path = self.checkImagePath(node)  # This also ensures the file exists
                    if self.path is None:  # check if image is embedded or linked
                        image_string = node.get('{http://www.w3.org/1999/xlink}href')
                        # find comma position
                        i = 0
                        while i < 40:
                            if image_string[i] == ',':
                                break
                            i = i + 1
                        image = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
                    else:
                        image = Image.open(self.path)
                                      
                    if node.get('width')[-1].isdigit() is False or node.get('height')[-1].isdigit() is False:
                        inkex.utils.debug("Image seems to have some weird dimensions in XML structure. Please remove units from width and height attributes at <svg:image>")
                        return
                    
                    parent = node.getparent()
                    if parent is not None and parent != self.document.getroot():
                        tpc = parent.composed_transform()
                        x_offset = tpc.e
                        y_offset = tpc.f
                    else:
                        x_offset = 0.0
                        y_offset = 0.0    
                    
                    # Write the embedded or linked image to temporary directory
                    if os.name == "nt":
                        exportfile = "Primitive.png"
                    else:
                        exportfile = "/tmp/Primitive.png"
                        
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image.save(exportfile, "png")
           
                    ## Build up Primitive command according to your settings from extension GUI
                    if os.name == "nt":
                        command  = "primitive"
                    else:
                        command  = "./primitive"
                    command += " -m "   + str(self.options.m)
                    command += " -rep " + str(self.options.rep)
                    command += " -r "   + str(self.options.r)
                    command += " -s "   + str(self.options.s) 
                    command += " -a "   + str(self.options.a)         
                    if not self.options.bg_enabled:
                        command += " -bg "  + self.rgbToHex(self.options.bg) 
                    command += " -j "   + str(self.options.j)         
                    command += " -i " + exportfile
                    command += " -o "   + exportfile + ".svg"
                    command += " -n "   + str(self.options.n)
   
                    #inkex.utils.debug(command)
                    
                    # Create the vector new SVG file
                    with os.popen(command, "r") as proc:
                        result = proc.read()
                        #inkex.utils.debug(result)

                    # proceed if new SVG file was successfully created
                    doc = None
                    if os.path.exists(exportfile + ".svg"):
                        # Delete the temporary png file again because we do not need it anymore
                        if os.path.exists(exportfile):
                            os.remove(exportfile)
 
                        # new parse the SVG file and insert it as new group into the current document tree
                        doc = etree.parse(exportfile + ".svg").getroot()
                            
                        newGroup = self.document.getroot().add(inkex.Group())          
                        newGroup.attrib['transform'] = "matrix({:0.6f}, 0, 0, {:0.6f}, {:0.6f}, {:0.6f})".format(
                            float(node.get('width')) / float(doc.get('width')),
                            float(node.get('height')) / float(doc.get('height')),
                            float(node.get('x')) + x_offset,
                            float(node.get('y')) + y_offset
                            )
                        
                        for children in doc:
                            newGroup.append(children)

                        # Delete the temporary svg file
                        if os.path.exists(exportfile + ".svg"):
                            try:
                                os.remove(exportfile + ".svg")
                            except:
                                pass
                    
                    else:
                        inkex.utils.debug("Error while creating output file! :-( The \"primitive\" executable seems to be missing, has no exec permissions or platform is imcompatible.")
                        exit(1)
                    #remove the old image or not                    
                    if self.options.keeporiginal is not True:
                        node.delete()

                    # create clip path to remove the stuffy surroundings
                    if self.options.cliprect:
                        path = '//svg:defs'
                        defslist = self.document.getroot().xpath(path, namespaces=inkex.NSS)
                        if len(defslist) > 0:
                            defs = defslist[0]
                        clipPathData = {inkex.addNS('label', 'inkscape'):'imagetracerClipPath', 'clipPathUnits':'userSpaceOnUse', 'id':'imagetracerClipPath'}
                        clipPath = etree.SubElement(defs, 'clipPath', clipPathData)
                        #inkex.utils.debug(image.width)
                        clipBox = {
                                'x':str(0), 
                                'y':str(0),
                                'width':str(doc.get('width')), 
                                'height':str(doc.get('height')),
                                'style':'fill:#000000; stroke:none; fill-opacity:1;'
                                }
                        etree.SubElement(clipPath, 'rect', clipBox)
                        #etree.SubElement(newGroup, 'g', {inkex.addNS('label','inkscape'):'imagetracerjs', 'clip-path':"url(#imagetracerClipPath)"})
                        newGroup.set('clip-path','url(#imagetracerClipPath)')
        else:
            inkex.utils.debug("No image found for tracing. Please select an image first.")        

if __name__ == '__main__':
    Primitive().run()