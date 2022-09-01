#!/usr/bin/env python3

import os
import inkex
from lxml import etree

class Reload(inkex.EffectExtension):

    '''
        This extension gets the current doc path and reads it as doc
        Then we clear the recent document from all items except basic stuff like root (svg:svg), defs and namedview
        finally we overwrite all attributes from svg:svg, defs and namedview to the recent
    '''

    def effect(self):
        currentDoc = self.document_path()
        if currentDoc == "":
            self.msg("Your document is not saved as a permanent file yet. Cannot reload.")
            exit(1)
        
        originalRoot = self.document.getroot()   
        originalNamedview = self.svg.namedview
        originalDefs = originalRoot.find("{http://www.w3.org/2000/svg}defs")
        originalRoot.clear() #drop all children and attributes from root

        if not os.path.exists(currentDoc):
            self.msg("The input file does not exist (anymore). Please check and try again.")
            exit(1)

        with open(currentDoc, 'r') as stream:
            try:
                doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
            except Exception as e:
                inkex.utils.debug("Malformed file: {}".format(e))
                exit(1)
      
        copyRoot = doc.getroot()
        copyNamedview = copyRoot.find(inkex.addNS('namedview', 'sodipodi'))
        copyDefs = copyRoot.find("{http://www.w3.org/2000/svg}defs")
        for child in copyRoot.getchildren():
            originalRoot.append(child)
        
        #update all attributes in originalSVG
        for copyAttrib in copyRoot.attrib:
            originalRoot.attrib[copyAttrib] = copyRoot.attrib[copyAttrib]

        #update all attributes in originalNamedview
        for copyAttrib in copyNamedview.attrib:
            originalNamedview.attrib[copyAttrib] = copyNamedview.attrib[copyAttrib]
               
        #update all attributes in originalDefs
        for copyAttrib in copyDefs.attrib:
            originalDefs.attrib[copyAttrib] = copyDefs.attrib[copyAttrib]

if __name__ == '__main__':
    Reload().run()