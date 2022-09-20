#!/usr/bin/env python3

import os
import re
import random
import inkex
from lxml import etree

class SourceCodeText(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--directory", default='~/', help="Default directory")
        pars.add_argument("--pattern", default='py', help="File extension pattern")
        pars.add_argument("--wordsperpara", type=int, default=0, help="Maximum words per paragraph")
        pars.add_argument("--numparas", type=int, default=1, help="Number of paragraphs")

    def text_generation(self):
        #Get all the matching files. Then yield words one at a time. This can take a while if there are a lot of files, but shouldn't be too bad.
        matcher = re.compile('.+\.{}$'.format(self.options.pattern))
        matched_files = []
        for root, _, names in os.walk(os.path.expanduser(self.options.directory)):
            for name in names:
                if matcher.match(name):
                    matched_files.append(os.path.join(root, name))

        random.shuffle(matched_files)
        for path in matched_files:
            with open(path, encoding = 'utf-8') as file:
                for word in file.read().split():
                    yield word

    def add_text(self, node):
        #Add the text to the node
        word_generator = self.text_generation()
        for _ in range(self.options.numparas):
            words = []
            para = etree.SubElement(node, inkex.addNS('flowPara','svg'))
            if self.options.wordsperpara:
                try:
                    for _, word in zip(range(self.options.wordsperpara), word_generator):
                        words.append(next(word_generator))
                except: #Exception as e:
                    #inkex.errormsg(e)
                    pass
            else:
                words = word_generator

            if words:
                para.text = ' '.join(words)
                etree.SubElement(node, inkex.addNS('flowPara','svg'))
            else:
                break

    def effect(self):
        found=0
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('flowRoot','svg'):
                found+=1
                if found==1:
                    self.addText(node)
        if not found:
            #inkex.debug('No "flowRoot" elements selected. Unable to add text.')
            svg=self.document.getroot()
            gattribs = {inkex.addNS('label','inkscape'):'lorem ipsum',inkex.addNS('groupmode','inkscape'):'layer'}
            g=etree.SubElement(svg,inkex.addNS('g','svg'),gattribs)
            flowRoot=etree.SubElement(g,inkex.addNS('flowRoot','svg'),{inkex.addNS('space','xml'):'preserve'})
            flowRegion=etree.SubElement(flowRoot,inkex.addNS('flowRegion','svg'))
            rattribs = {'x':'0','y':'0','width':svg.get('width'),'height':svg.get('height')}
            rect=etree.SubElement(flowRegion,inkex.addNS('rect','svg'),rattribs)
            self.add_text(flowRoot)

if __name__ == '__main__':
    SourceCodeText().run()
