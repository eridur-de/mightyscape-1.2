#!/usr/bin/env python3

import inkex
import os
import lxml

class ImportAttributes(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--data", default="", help="data file")

    def effect(self):
        
        if not os.path.exists(self.options.data):
            self.msg("The input file does not exist. Please select a proper file and try again.")
            exit(1)
            
        if os.path.isdir(self.options.data):
            self.msg("You must specify a file, not a directory!")
            exit(1)
            
        with open(self.options.data, 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                #split on , max 2+1 = 3 items
                parts = line.split(",", 2)
                if len(parts) >= 3:
                    id = parts[0]
                    attribute = parts[1]
                    value = parts[2]
                    try:
                        node = self.svg.getElementById(id)
                        if node is not None:
                            try: 
                                node.set(attribute, value)
                            except AttributeError:
                                inkex.utils.debug("Unknown Attribute")
                    except AttributeError:
                        inkex.utils.debug("element with id '" + id + "' not found in current selection.")
                    except lxml.etree.XPathEvalError:
                        inkex.utils.debug("invalid input file")
                        exit(1)
                        
if __name__ == '__main__':
    ImportAttributes().run()