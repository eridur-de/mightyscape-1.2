#! /usr/bin/env python3
import random
rr = random.randint(1,10)
import inkex
from lxml import etree

class Streaks(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--blur', type = int, default = 2)
        pars.add_argument('--linno', type = int, default = 50)
        pars.add_argument('--xrand', type = inkex.Boolean, default = True)
        pars.add_argument('--pagep', type = inkex.Boolean, default = True)
        pars.add_argument('--cusx', type = int, default = 500)
        pars.add_argument('--cusy', type = int, default = 500)
        pars.add_argument('--segLen', type = int, default = 8)
        pars.add_argument('--yrand', type = inkex.Boolean, default = True)
        pars.add_argument('--dashp', type = inkex.Boolean, default = True)
        pars.add_argument('--blankp', type = inkex.Boolean, default = True)
        pars.add_argument('--dotp', type = inkex.Boolean, default = True)
        pars.add_argument('--dots', type = int, default = 100)
        pars.add_argument('--strokeColor', default = 255)
        pars.add_argument('--strokeWidth', type = int, default = 2)
        pars.add_argument("--Nmain", default='title')

    def effect(self):
        blur = int(self.options.blur)
        linno = int(self.options.linno)
        xrand = bool(self.options.xrand)
        pagep = bool(self.options.pagep)
        cusx = int(self.options.cusx)
        cusy = int(self.options.cusy)
        segLen = int(self.options.segLen)
        yrand = bool(self.options.yrand)
        dashp = bool(self.options.dashp)
        blankp = bool(self.options.blankp)
        dotp = bool(self.options.dotp)
        dots = int(self.options.dots)
        strokeColor = int(self.options.strokeColor)
        strokeWidth = int(self.options.strokeWidth)

        # Get access to main SVG document element and get its dimensions.
        svg = self.document.getroot()

        if pagep :
            try :
                width  = self.svg.unittouu(svg.get('width'))
                height = self.svg.unittouu(svg.attrib['height'])
            except AttributeError :
                width  = self.unittouu(svg.get('width'))
                height = self.unittouu(svg.attrib['height'])
#                inkex.errormsg("Page size %d %d" % (width, height))
        else :
            width = cusx
            height = cusy

            
        # Find defs node.
        for child in svg :
            if -1 != child.tag.find("defs") :
                break
        else:
            inkex.errormsg("No defs child found")
        defs = child

        if blur :
            filter = etree.SubElement(defs, "filter")
            filter.set(inkex.addNS('collect', 'inkscape'), 'always')
            filname = self.svg.get_unique_id('filter')
            filter.set('id' , filname)

            finfo = etree.SubElement(filter, 'feGaussianBlur')
            finfo.set(inkex.addNS('collect', 'inkscape'), 'always')
            finfo.set('stdDeviation', str(blur))

        """ Debug
        for i in range(len(svg)) :
            k = svg[i].attrib 
            for ky in k :
                inkex.errormsg(ky)

        # Clean any old layers
        flag = False
        for i in range(len(svg)) :
            dic = svg[i].attrib
            for key in dic:
                if -1 != key.find("label") :
                    if 'Streak Layer' == dic[key] :
                        del svg[i]
                        flag = True
        if flag :
            inkex.errormsg("Found old Streak layer")
        else:
            inkex.errormsg("Clean")
        """            
        # Create a new layer.
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), 'Streak Layer')
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')

        # Create path element
        path = etree.Element(inkex.addNS('path','svg'))

        alpha = strokeColor & 255
        color = (strokeColor >> 8) & int('ffffff', 16)
        style = {
            'stroke'        : '#%06X' % color,
            'stroke-width'  : "{}px".format(strokeWidth),
            }
        #inkex.errormsg("Colour %s" % strokeColor)

        if blur : style['filter'] = 'url(#' + filname +')'


        path.set('style', str(inkex.Style(style)))
        
        pathstring = ''
        seglim = int(height / segLen)
        ditlen = int(height / dots)

        xco = 0
        while xco < width :
            y = 0
            flag = random.randint(0, 2)
            while y < height :
                if yrand :
                    yinc = random.randint(1, seglim)
                else :
                    yinc = seglim
                if flag == 1 and dashp: #Draw dash
                    pathstring += ' M '+str(xco)+','+str(y)+' L '+str(xco)+','+str(min(y + yinc, height))
                    y += yinc + ditlen
                elif flag == 2 and dotp: #Draw dots
                    ylim = min(y + yinc, height)
                    while y < ylim :
                        pathstring += ' M '+str(xco)+','+str(y)+' L '+str(xco)+','+str(min(y + ditlen, height))
                        y += 2*ditlen
                elif flag == 0 and blankp :
                    y += yinc #Adding blank space 
                elif not (dashp or dotp or blankp) : #Squiggle if user turns them off
                    sdit = str(2*ditlen)+' '
                    pathstring += ' M '+str(xco)+','+str(y)+' q '+ 2*sdit + '0 ' +sdit
                    for i in range(int(height/(2*ditlen))) :
                        pathstring += 't 0 '+sdit
                    y = height
                flag = (flag + 1)%3
            if xrand :
                xco += random.randint(0, int(2 * width / linno))
            else :
                xco += width / linno
        path.set('d', pathstring)

        # Connect elements together.
        layer.append(path)

if __name__ == '__main__':
    Streaks().run()