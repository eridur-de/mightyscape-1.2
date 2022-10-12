#!/usr/bin/env python3

import inkex
import measure
from inkex.paths import Path
from inkex import paths

def getArea(path):
    return abs(measure.csparea(paths.CubicSuperPath(path + "z")))

class OptimizeSequenceLasercutSequence(inkex.EffectExtension):

    def effect(self):
        elements = self.document.xpath('//svg:path',namespaces=inkex.NSS)
        for el in elements:
            oldpathstring = el.attrib['d']
            nodes = Path(oldpathstring).to_arrays()
            currentSection = []
            sections = [currentSection]
            for node in nodes:
                command = node.pop(0)
                currentSection.append(command + ' ' + ' '.join(list(map(lambda c: ','.join(map(str, c)), node))))
                if command.lower() == 'z':
                    currentSection = []
                    sections.append(currentSection)
            
            sections = list(map(lambda n: ' '.join(n), filter(lambda n: len(n) > 0, sections)))

            if (sections[-1][-2].lower() != 'z'):
                nonClosedSection = ' ' + sections.pop()
            else:
                nonClosedSection = ''
                
            sections = filter(lambda s: s[0].lower() != 'z', sections)
            sections = sorted(sections, key=getArea)
            newpathstring = "z ".join(sections) + nonClosedSection
            el.set('d', newpathstring)
        
if __name__ == '__main__':
    OptimizeSequenceLasercutSequence().run()