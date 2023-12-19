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

import clip
import inkex
import gettext
_ = gettext.gettext

class ClipAboveEffect(clip.ClipEffect):
    def __init__(self):
        clip.ClipEffect.__init__(self, '+')

    def find_target(self, pathId):
        layer = self.svg.selected[pathId].getparent()
        parent = layer.getparent()
        if parent.get(inkex.addNS('groupmode','inkscape')) != 'layer':
            clip.die(_("Error: Layer '%s' has no parent layer") % clip.layername(layer))
        if parent is None:
            clip.die(_("Error: no parent layer in selection."))   
        children = parent.getchildren()
        children.reverse()
        last = children[0]
        for child in children:
            if child == layer and last is not None:
                return last
            last = child

        clip.die(_("Error: There is no layer above '%s'") % clip.layername(layer))

# Create effect instance and apply it.
ClipAboveEffect().run()