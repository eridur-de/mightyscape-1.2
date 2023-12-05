#!/usr/bin/env python3
# Copyright (c) 2012 Stuart Pernsteiner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import inkex

class GroupToLayer(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('-d', '--depth', type = int, default = 1, help = 'Convert nested group up to DEPTH layers deep')

    def effect(self):
        depth = self.options.depth
        self.tag_g = inkex.addNS('g', 'svg')
        if len(self.svg.selected) > 0:
            for node in self.svg.selected.values():
                self.convert_group(node, depth)
        else:
            inkex.errormsg('Please select some objects first.')
            return

    def convert_group(self, node, depth):
        if depth <= 0:
            return
        if node.tag != self.tag_g:
            return
        node.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        for child in node:
            self.convert_group(child, depth - 1)

if __name__ == '__main__':
    GroupToLayer().run()