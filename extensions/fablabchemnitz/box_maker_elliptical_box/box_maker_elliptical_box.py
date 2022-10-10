#!/usr/bin/env python3

from inkscape_helper.Coordinate import Coordinate
import inkscape_helper.Effect as eff
import inkscape_helper.SVG as svg
from inkscape_helper.Ellipse import Ellipse

from inkscape_helper.Line import Line
from inkscape_helper.EllipticArc import EllipticArc

from math import *
import inkex

#Note: keep in mind that SVG coordinates start in the top-left corner i.e. with an inverted y-axis

# first define some SVG primitives
greenStyle = svg.green_style

def _makeCurvedSurface(topLeft, w, h, cutSpacing, hCutCount, thickness, parent, invertNotches = False, centralRib = False):
    width = Coordinate(w, 0)
    height = Coordinate(0, h)
    wCutCount = int(floor(w / cutSpacing))
    if wCutCount % 2 == 0:
        wCutCount += 1    # make sure we have an odd number of cuts
    xCutDist = w / wCutCount
    xSpacing = Coordinate(xCutDist, 0)
    ySpacing = Coordinate(0, cutSpacing)
    cut = height / hCutCount - ySpacing
    plateThickness = Coordinate(0, thickness)
    notchEdges = []
    topHCuts = []
    bottomHCuts = []

    p = svg.Path()

    for cutIndex in range(wCutCount):
        if (cutIndex % 2 == 1) != invertNotches:  # make a notch here
            inset = plateThickness
        else:
            inset = Coordinate(0, 0)

        # A-column of cuts
        aColStart = topLeft + xSpacing * cutIndex
        notchEdges.append((aColStart - topLeft).x)

        if cutIndex > 0: # no cuts at x == 0
            p.move_to(aColStart, True)
            p.line_to(cut / 2)

            for j in range(hCutCount - 1):
                pos = aColStart + cut / 2 + ySpacing + (cut + ySpacing) * j
                p.move_to(pos, True)
                p.line_to(cut)

            p.move_to(aColStart + height - cut / 2, True)
            p.line_to(cut / 2)


        # B-column of cuts, offset by half the cut length; these cuts run in the opposite direction
        bColStart = topLeft + xSpacing * cutIndex + xSpacing / 2
        for j in reversed(range(hCutCount)):
            end = bColStart + ySpacing / 2 + (cut + ySpacing) * j
            start = end + cut
            if centralRib and hCutCount % 2 == 0 and cutIndex % 2 == 1:
                holeTopLeft = start + (ySpacing - plateThickness - xSpacing) / 2
                if j == hCutCount // 2 - 1:
                    start -= plateThickness / 2
                    p.move_to(holeTopLeft + plateThickness + xSpacing, True)
                    p.line_to(-xSpacing)

                    p.move_to(holeTopLeft, True)
                    p.line_to(xSpacing)

                elif j == hCutCount // 2:
                    end += plateThickness / 2
            if j == 0:  # first row
                end += inset
            elif j == hCutCount - 1:  # last row
                start -= inset
            p.move_to(start, True)
            p.line_to(end, True)

        #horizontal cuts (should be done last)
        topHCuts.append((aColStart + inset, aColStart + inset + xSpacing))
        bottomHCuts.append((aColStart + height - inset, aColStart + height - inset + xSpacing))

    # draw the outline
    for c in reversed(bottomHCuts):
        p.move_to(c[1], True)
        p.line_to(c[0], True)

    p.move_to(topLeft + height, True)
    p.line_to(-height)

    for c in topHCuts:
        p.move_to(c[0], True)
        p.line_to(c[1], True)

    p.move_to(topLeft + width, True)
    p.line_to(height)


    group = svg.group(parent)
    p.path(group)

    notchEdges.append(w)
    return notchEdges

def _makeNotchedEllipse(center, ellipse, start_theta, thickness, notches, parent, invertNotches):
    start_theta += pi # rotate 180 degrees to put the lid on the topside

    ell_radius = Coordinate(ellipse.x_radius, ellipse.y_radius)
    ell_radius_t = ell_radius + Coordinate(thickness, thickness)

    theta = ellipse.theta_from_dist(start_theta, notches[0])
    ell_point = center + ellipse.coordinate_at_theta(theta)
    prev_offset = ellipse.tangent(theta) * thickness

    p = svg.Path()
    p.move_to(ell_point, absolute=True)

    for n in range(len(notches) - 1):
        theta = ellipse.theta_from_dist(start_theta, notches[n + 1])
        ell_point = center + ellipse.coordinate_at_theta(theta)
        notch_offset = ellipse.tangent(theta) * thickness
        notch_point = ell_point + notch_offset

        if (n % 2 == 0) != invertNotches:
            p.arc_to(ell_radius, ell_point, absolute=True)
            prev_offset = notch_offset

        else:
            p.line_to(prev_offset)
            p.arc_to(ell_radius_t, notch_point, absolute=True)
            p.line_to(-notch_offset)

    p.path(parent)



class EllipticalBox(eff.Effect):
    """
    Creates a new layer with the drawings for a parametrically generaded box.
    """
    def __init__(self):
        options = [
            ['unit', str, 'mm', 'Unit, one of: cm, mm, in, ft, ...'],
            ['thickness', float, '3.0', 'Material thickness'],
            ['width', float, '100', 'Box width'],
            ['height', float, '100', 'Box height'],
            ['depth', float, '100', 'Box depth'],
            ['cut_dist', float, '1.5', 'Distance between cuts on the wrap around. Note that this value will change slightly to evenly fill up the available space.'],
            ['auto_cut_dist', inkex.Boolean, 'false', 'Automatically set the cut distance based on the curvature.'], # in progress
            ['cut_nr', int, '3', 'Number of cuts across the depth of the box.'],
            ['lid_angle', float, '120', 'Angle that forms the lid (in degrees, measured from centerpoint of the ellipse)'],
            ['body_ribcount', int, '0', 'Number of ribs in the body'],
            ['lid_ribcount', int, '0', 'Number of ribs in the lid'],
            ['invert_lid_notches', inkex.Boolean, 'false', 'Invert the notch pattern on the lid (keeps the lid from sliding sideways)'],
            ['central_rib_lid', inkex.Boolean, 'false', 'Create a central rib in the lid'],
            ['central_rib_body', inkex.Boolean, 'false', 'Create a central rib in the body']
        ]
        eff.Effect.__init__(self, options)


    def effect(self):
        """
        Draws as basic elliptical box, based on provided parameters
        """

        # input sanity check
        error = False
        if min(self.options.height, self.options.width, self.options.depth) == 0:
            eff.errormsg('Error: Dimensions must be non zero')
            error = True

        if self.options.cut_nr < 1:
            eff.errormsg('Error: Number of cuts should be at least 1')
            error = True

        if (self.options.central_rib_lid or self.options.central_rib_body) and self.options.cut_nr % 2 == 1:
            eff.errormsg('Error: Central rib is only valid with an even number of cuts')
            error = True

        if self.options.unit not in self.knownUnits:
            eff.errormsg('Error: unknown unit. '+ self.options.unit)
            error = True

        if error:
            exit()


        # convert units
        unit = self.options.unit
        H = self.svg.unittouu(str(self.options.height) + unit)
        W = self.svg.unittouu(str(self.options.width) + unit)
        D = self.svg.unittouu(str(self.options.depth) + unit)
        thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        cutSpacing = self.svg.unittouu(str(self.options.cut_dist) + unit)
        cutNr = self.options.cut_nr

        doc_root = self.document.getroot()
        layer = svg.layer(doc_root, 'Elliptical Box')

        ell = Ellipse(W/2, H/2)

        #body and lid
        lidAngleRad = self.options.lid_angle * 2 * pi / 360
        lid_start_theta = ell.theta_at_angle(pi / 2 - lidAngleRad / 2)
        lid_end_theta = ell.theta_at_angle(pi / 2 + lidAngleRad / 2)

        lidLength = ell.dist_from_theta(lid_start_theta, lid_end_theta)
        bodyLength = ell.dist_from_theta(lid_end_theta, lid_start_theta)

        # do not put elements right at the edge of the page
        xMargin = 3
        yMargin = 3

        bottom_grp = svg.group(layer)
        top_grp = svg.group(layer)

        bodyNotches = _makeCurvedSurface(Coordinate(xMargin, yMargin), bodyLength, D, cutSpacing, cutNr,
                                         thickness, bottom_grp, False, self.options.central_rib_body)
        lidNotches = _makeCurvedSurface(Coordinate(xMargin, D + 2 * yMargin), lidLength, D, cutSpacing, cutNr,
                                        thickness, top_grp, not self.options.invert_lid_notches,
                                        self.options.central_rib_lid)

        # create elliptical sides
        sidesGrp = svg.group(layer)

        elCenter = Coordinate(xMargin + thickness + W / 2, 2 * D + H / 2 + thickness + 3 * yMargin)

        # indicate the division between body and lid
        p = svg.Path()
        if self.options.invert_lid_notches:
            p.move_to(elCenter + ell.coordinate_at_theta(lid_start_theta + pi), True)
            p.line_to(elCenter, True)
            p.line_to(elCenter + ell.coordinate_at_theta(lid_end_theta + pi), True)

        else:
            angleA = ell.theta_from_dist(lid_start_theta, lidNotches[1])
            angleB = ell.theta_from_dist(lid_start_theta, lidNotches[-2])

            p.move_to(elCenter + ell.coordinate_at_theta(angleA + pi), True)
            p.line_to(elCenter, True)
            p.line_to(elCenter + ell.coordinate_at_theta(angleB + pi), True)

        _makeNotchedEllipse(elCenter, ell, lid_end_theta, thickness, bodyNotches, sidesGrp, False)
        _makeNotchedEllipse(elCenter, ell, lid_start_theta, thickness, lidNotches, sidesGrp,
                            not self.options.invert_lid_notches)

        p.path(sidesGrp, greenStyle)

        # ribs
        if self.options.central_rib_lid or self.options.central_rib_body:
            innerRibCenter = Coordinate(xMargin + thickness + W / 2, 2 * D +  1.5 * (H + 2 *thickness) + 4 * yMargin)
            innerRibGrp = svg.group(layer)

            outerRibCenter = Coordinate(2 * xMargin + 1.5 * (W + 2 * thickness),
                                        2 * D + 1.5 * (H + 2 * thickness) + 4 * yMargin)
            outerRibGrp = svg.group(layer)


        if self.options.central_rib_lid:
            _makeNotchedEllipse(innerRibCenter, ell, lid_start_theta, thickness, lidNotches, innerRibGrp, False)
            _makeNotchedEllipse(outerRibCenter, ell, lid_start_theta, thickness, lidNotches, outerRibGrp, True)

        if self.options.central_rib_body:
            spacer = Coordinate(0, 10)
            _makeNotchedEllipse(innerRibCenter + spacer, ell, lid_end_theta, thickness, bodyNotches, innerRibGrp, False)
            _makeNotchedEllipse(outerRibCenter + spacer, ell, lid_end_theta, thickness, bodyNotches, outerRibGrp, True)

        if self.options.central_rib_lid or self.options.central_rib_body:
            svg.text(sidesGrp, elCenter, 'side (duplicate this)')
            svg.text(innerRibGrp, innerRibCenter, 'inside rib')
            svg.text(outerRibGrp, outerRibCenter, 'outside rib')

if __name__ == '__main__':
    EllipticalBox().run()