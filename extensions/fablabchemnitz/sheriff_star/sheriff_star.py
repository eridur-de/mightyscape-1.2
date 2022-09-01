#!/usr/bin/env python3
"""
Sheriff Star
Create n-pointed sheriff star.
"""
import inkex
from math import *
from lxml import etree

def addPathCommand(a, cmd):
    for x in cmd:
        a.append(str(x))

class SheriffStar(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--points', type=int, default=5, help='Number of points (or sides)')
        pars.add_argument('--star_tip_ratio', type=float, default=10, help='Star tip circle % (star tip circle radius as a percentage of the outer radius)')
        pars.add_argument('--inner_ratio', type=float, default=58, help='Inner circle % (inner radius as a percentage of the outer radius)')
        pars.add_argument('--show_inner_circle', type=inkex.Boolean, default=False, help='Show inner circle')

    def effect(self):
        layer = self.svg.get_current_layer();

        if len(self.svg.selected) == 0:
            inkex.errormsg('Please select a circle or ellipse.')
            exit()

        numValid = 0
        for id, obj in self.svg.selected.items():
            cx,cy, rx,ry = 0,0, 0,0
            style = ''
            isValid = False
            if obj.tag == inkex.addNS('circle','svg'):
                isValid = True
                cx = float(obj.get('cx'))
                cy = float(obj.get('cy'))
                rx = float(obj.get('r'))
                ry = rx
            elif obj.tag == inkex.addNS('ellipse', 'svg'):
                isValid = True
                cx = float(obj.get('cx'))
                cy = float(obj.get('cy'))
                rx = float(obj.get('rx'))
                ry = float(obj.get('ry'))
            elif obj.tag == inkex.addNS('path', 'svg'):
                if obj.get(inkex.addNS('type', 'sodipodi')) == 'arc':
                    isValid = True
                    cx = float(obj.get(inkex.addNS('cx', 'sodipodi')))
                    cy = float(obj.get(inkex.addNS('cy', 'sodipodi')))
                    rx = float(obj.get(inkex.addNS('rx', 'sodipodi')))
                    ry = float(obj.get(inkex.addNS('ry', 'sodipodi')))

            if not isValid:
                continue;

            numValid += 1
            style = obj.get('style')
            transform = obj.get('transform')
            isEllipse = False
            if rx != ry:
                isEllipse = True

            skip = 1
            sides = self.options.points
            innerRatio = float(self.options.inner_ratio) / 100.0
            starTipRatio = float(self.options.star_tip_ratio) / 100.0
            showInnerCircle = self.options.show_inner_circle

            if showInnerCircle:
                if not isEllipse:
                    cin =etree.SubElement(layer, inkex.addNS('circle','svg'))
                    cin.set('r', str(rx * innerRatio))
                else:
                    cin =etree.SubElement(layer, inkex.addNS('ellipse','svg'))
                    cin.set('rx', str(rx * innerRatio))
                    cin.set('ry', str(ry * innerRatio))
                cin.set('cx', str(cx))
                cin.set('cy', str(cy))
                cin.set('style', style)
                if transform:
                    cin.set('transform', transform)

            tau = 2*pi
            origin = -(tau / 4)
            out_pts = []
            in_pts = []
            for i in range(sides):
                # Outer points (on outer circle)
                theta = (i * (tau / sides))
                px = cx + rx * cos(origin + theta)
                py = cy + ry * sin(origin + theta)
                out_pts.append([px, py])

                # Inner points (on inner circle)
                theta = ((i + (skip / 2.0)) * (tau / sides))
                px = cx + rx * innerRatio * cos(origin + theta)
                py = cy + ry * innerRatio * sin(origin + theta)
                in_pts.append([px, py])

            # Add circles at each star tip.
            for pt in out_pts:
                cin =etree.SubElement(layer, inkex.addNS('circle','svg'))
                cin.set('r', str(rx * starTipRatio))
                cin.set('cx', str(pt[0]))
                cin.set('cy', str(pt[1]))
                cin.set('style', style)
                if transform:
                    cin.set('transform', transform)

            pts = []
            pt_done = {}
            for i in range(sides):
                if i in pt_done:
                    continue;

                p1 = out_pts[i]
                addPathCommand(pts, ['M', p1[0], p1[1]])

                pt_done[i] = True
                start_index = i
                curr = start_index
                next = (curr + skip) % sides
                while next != start_index:
                    p = out_pts[next]
                    pt_done[next] = True

                    addPathCommand(pts, ['L', in_pts[curr][0], in_pts[curr][1]])
                    addPathCommand(pts, ['L', p[0], p[1]])

                    curr = next
                    next = (curr + skip) % sides
                addPathCommand(pts, ['L', in_pts[curr][0], in_pts[curr][1]])
                addPathCommand(pts, ['z'])

            # Create star polygon as a single path.
            l1 =etree.SubElement(layer, inkex.addNS('path','svg'))
            l1.set('style', style)
            if transform:
                l1.set('transform', transform)
            l1.set('d', ' '.join(pts))

        if numValid == 0:
            inkex.errormsg('Selection must contain a circle or ellipse.')

if __name__ == '__main__':
    SheriffStar().run()