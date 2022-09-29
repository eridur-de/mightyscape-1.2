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

import sys
import inkex
import gettext
from lxml import etree
_ = gettext.gettext

class ClipEffect(inkex.EffectExtension):
    
    def __init__(self, dirmark):
        inkex.Effect.__init__(self)
        self.dirmark = dirmark

    def effect(self):
        defs = self.svg.getElement('//svg:defs')

        if len(self.svg.selected) != 1:
            die(_("Error: You must select exactly one path"))
        # Create the svg:clipPath inside of svg:defs
        pathId = list(self.svg.selected.values())[0].get('id')

        #inkex.utils.debug(pathId)
        clippath = etree.SubElement(defs, 'clipPath',
                {'clipPathUnits': 'userSpaceOnUse'
                ,'id': self.svg.get_unique_id("clipPath")})
        use = etree.SubElement(clippath, 'use',
                {inkex.addNS('href','xlink'): '#' + pathId
                ,'id': self.svg.get_unique_id("use")})

        # Find the target layer and set its clip-path attribute
        layer =  self.svg.selected[pathId].getparent()
        target = self.find_target(pathId)

        target.set('clip-path', 'url(#%s)' % clippath.get('id'))

        # Update layer names
        label_attr = inkex.addNS('label', 'inkscape')

        layer_label = layer.get(label_attr)
        layer.set(label_attr, layer_label + ' (c%s)' % self.dirmark)

        target_label = target.get(label_attr)
        target.set(label_attr, target_label + ' (C)')

def layername(layer):
    return layer.get(inkex.addNS('label','inkscape'))

def die(msg):
    inkex.errormsg(msg)
    sys.exit(1)

