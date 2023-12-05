#!/usr/bin/env python3

import inkex

"""
Extension for InkScape 1.0

This extension is totally minimal. It will just clean the whole document from groups without content (dangling groups). That usually happens if you have a group but remove its paths for example. The group will possibly stay in the XML tree. This also applies for layers because layers are just special types of groups. This effect applies to the whole document ONLY!
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.08.2020
Last Patch: 23.04.2022
License: GNU GPL v3

Thanks to Cyrille
"""

class RemoveEmptyGroups(inkex.EffectExtension):
     
    def effect(self):
        # gets all group elements in document, at any/all nested levels
        groups = self.document.xpath('//svg:g',namespaces=inkex.NSS)

        # end if there are no groups
        if len(groups) == 0:
            return

        # loop through groups
        for group in groups:

            # checks if item is empty leaf, and if so prune up branch
            while len(group.getchildren()) == 0:
                # this group is empty, delete it
                parent = group.getparent()
                parent.remove(group)
                # see if we should delete the parent too, recursively
                group = parent

if __name__ == '__main__':
    RemoveEmptyGroups().run()