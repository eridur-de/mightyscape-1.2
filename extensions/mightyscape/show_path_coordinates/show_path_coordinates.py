#!/usr/bin/env python3
#
# curve xy co-ordinate export
# Authors:
# Jean Moreno <jean.moreno.fr@gmail.com>
# John Cliff <john.cliff@gmail.com>
# Neon22 <https://github.com/Neon22?tab=repositories>
# Jens N. Lallensack <jens.lallensack@gmail.com>
# Mario Voigt <mario.voigt@stadtfabrikanten.org>
#
# Copyright (C) 2011 Jean Moreno
# Copyright (C) 2011 John Cliff 
# Copyright (C) 2011 Neon22
# Copyright (C) 2019 Jens N. Lallensack
# Copyright (C) 2021 Mario Voigt

# Released under GNU GPL v3, see https://www.gnu.org/licenses/gpl-3.0.en.html for details.
#
import inkex
import sys
from inkex.paths import CubicSuperPath
from inkex import transforms

class ShowPathCoordinates(inkex.EffectExtension):
    
    def effect(self):
        if len(self.svg.selected) > 0:
            output_all = output_nodes = ""
            for node in self.svg.selection.filter(inkex.PathElement):
                node.apply_transform()
                p = CubicSuperPath(node.get('d'))
                for subpath in p:
                    for csp in subpath:
                        output_nodes += str(csp[1][0]) + "\t" + str(csp[1][1]) + "\n"
                output_nodes += "\n"                 
            sys.stderr.write(output_nodes.strip())
        else:
            inkex.errormsg('Please select some paths first.')
            return
        
if __name__ == '__main__':
    ShowPathCoordinates().run()