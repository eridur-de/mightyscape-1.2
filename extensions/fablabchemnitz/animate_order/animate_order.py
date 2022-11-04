#!/usr/bin/env python3

import inkex
import subprocess
import shutil
import os
import sys
from lxml import etree
import warnings

"""
Extension for InkScape 1.X
Features
 - Create SVG preview file and show it in browser. Helps to quickly evaluate line order for cutting processes
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 21.04.2021
Last patch: 07.05.2021
License: GNU GPL v3

Used version of Vivus JS library: https://github.com/maxwellito/vivus/releases/tag/v0.4.6 - MIT License

Browser config:
Firefox via about:config -> privacy.file_unique_origin = false

ToDo:
 - adjust width and height (give options)
 - embed config buttons inside html to adjust time/type/... (more flexible than clicking from Inkscape)
    - we should do it the way like vivus instant -> http://maxwellito.github.io/vivus / https://maxwellito.github.io/vivus-instant
    - the generated SVGs can be downloaded again and include all animations!
 - calculate the total length of all paths and auto-adjust the speed to have good visibility
 - Possible feature request could be to handle "animate selected objects only". See "Export selection as ... " extension to steal that code.
"""
DETACHED_PROCESS = 0x00000008

class AnimateOrder(inkex.EffectExtension):

    def spawnIndependentProcess(self, args):
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"
        if os.name == 'nt':
            subprocess.Popen(args, close_fds=True, creationflags=DETACHED_PROCESS)
        else:
            subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        warnings.simplefilter("default", ResourceWarning)

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--time", type=float, default = 5.0, help="Duration (frames)")
        pars.add_argument("--fps", type=int, default = 60.0, help="Frames per second (fps)")
        pars.add_argument("--sequence_type", help="Sequence type")
        pars.add_argument("--reverse", type = inkex.Boolean, default = False, help="Reverse order")
        pars.add_argument("--browser", help="Select your desired browser (must be installed and must exist in %PATH% variable).")

    def effect(self):
        #write current SVG to extensions' directory. Target name must be "drawing.svg" because it is embedded in animate_order.html statically
        inFile = "drawing.svg"
        extension_dir = os.path.dirname(os.path.realpath(__file__))
        shutil.copy2(self.options.input_file, os.path.join(extension_dir, inFile))

        target_html = os.path.join(extension_dir, "animate_order.html")
        
        docTitle = self.document.getroot().get("{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname")
        animateId = self.document.getroot().get('id')
        if docTitle is None:
            title = "Animate Order - Vivus JS"
        else:
            title = "Animate Order - " + docTitle
        vivus_include = "./vivus-0.4.6/dist/vivus.js"
        
        duration = self.options.time  * self.options.fps # we guess we have 20 ... 60 fps. depends on performance of the machine
        frames_per_second = self.options.fps
        type = self.options.sequence_type
        reverse = str(self.options.reverse).lower()

        currentDoc = self.document_path()
        if currentDoc == "":
            self.msg("Your document is not saved as a permanent file yet. Please save first.")
            exit(1)

        svgfile = open(self.document_path(), 'r')
        #inkex.utils.debug(svgfile.read())
        svgContent = svgfile.read()
        svgfile.close()

        with open(target_html, "w") as text_file:
            print( '<html>'                                                                         , file=text_file)
            print( '    <head>'                                                                     , file=text_file)
            print( '        <meta charset="UTF-8">'                                                 , file=text_file)
            print( '        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">'         , file=text_file)
            print( '        <meta name="viewport" content="width=device-width, initial-scale=1.0">' , file=text_file)
            print(f'        <title>{title}</title>'                                                 , file=text_file)
            print( '        <meta name="description" content="SVG Drawing Animation">'              , file=text_file)
            print( '    </head>'                                                                    , file=text_file)                                                 
            print( '    <body>'                                                                     , file=text_file)                                                 
            print( '    <button onclick="vi.reset().play();">replay</button>'                       , file=text_file)
            print( '    <br/>'                                                                      , file=text_file)                                                 
            #print(f'    <object id="animate_order" type="image/svg+xml" data="{inFile}"></object>'  , file=text_file)
            print(svgContent                                                                        , file=text_file) 
            print(f'    <script src="{vivus_include}"></script>'                                    , file=text_file)
            print( '    <script>'                                                                   , file=text_file)
            print( "         var vi = new Vivus('" + f'{animateId}' + "', {type: '" + f'{type}' + "', \
duration:" + f'{duration}' + ", reverseStack:" + f'{reverse}' + "});" , file=text_file)
            print( '    </script>'                                                                  , file=text_file)
            print( '    </body>'                                                                    , file=text_file)
            print( '</html>'                                                                        , file=text_file)

        if os.path.exists(target_html) is False:
            inkex.utils.debug("Error. Target file does not exist!")
            exit(1)

        #now open firefox
        args = [self.options.browser, target_html]
        try:
            self.spawnIndependentProcess(args)
        except FileNotFoundError as e:
            inkex.utils.debug("Error. Check for correct browser installation and try again!")
            exit(1)

if __name__ == '__main__':
    AnimateOrder().run()