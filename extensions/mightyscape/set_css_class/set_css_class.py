#!/usr/bin/env python3

"""
Sets a css class on selected elements, while optionally removing the elements' styling.
If inline styles are not removed, the css class might not have effect.

Inspired by MergeStyles (and best used together with it).
"""

__author__ = "Mois Moshev"
__email__ = "mois@monomon.me"
__copyright__ = "Copyright (C) 2017 Mois Moshev"
__license__ = "GPL"

import inkex
import sys

class SetCSSClass(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--name", help="Name of css class to apply")
        pars.add_argument("--clear_styles", type=inkex.Boolean, default=True, help="Name of css class to apply")

    def effect(self):
        newclass = self.options.name
        elements = self.svg.selected.values()

        for el in elements:
            current_classes = el.attrib.has_key("class") and el.attrib["class"].split() or []

            if newclass not in current_classes:
                current_classes.append(newclass)

            if self.options.clear_styles:
                el.attrib.pop("style", None)

            el.attrib["class"] = " ".join(current_classes)

if __name__ == "__main__":
    SetCSSClass().run()
