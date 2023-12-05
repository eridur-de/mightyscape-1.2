#!/usr/bin/python

import math
import os
import numpy as np
import scipy.signal as scipySignal

import inkscapeMadeEasy.inkscapeMadeEasy_Base as inkBase
import inkscapeMadeEasy.inkscapeMadeEasy_Draw as inkDraw
import inkscapeMadeEasy.inkscapeMadeEasy_Plot as inkPlot


# least common multiplier
def myLcm(x, y):
    return x * y / math.gcd(int(x), int(y))


# ---------------------------------------------
# noinspection PyAttributeOutsideInit
class Spirograph(inkBase.inkscapeMadeEasy):
    def __init__(self):
        inkBase.inkscapeMadeEasy.__init__(self)

        self.arg_parser.add_argument("--curveType", type=str, dest="curveType", default='resistor')
        self.arg_parser.add_argument("--radius_R", type=float, dest="radius_R", default=10.0)
        self.arg_parser.add_argument("--radius_r", type=float, dest="radius_r", default=5.0)
        self.arg_parser.add_argument("--detailLevel", type=float, dest="detailLevel", default=1.0)
        self.arg_parser.add_argument("--adaptiveTheta", type=self.bool, dest="adaptiveTheta", default=False)
        self.arg_parser.add_argument("--pencil_distance", type=float, dest="pencil_distance", default=1.0)
        self.arg_parser.add_argument("--drawBaseCircles", type=self.bool, dest="drawBaseCircles", default=False)
        self.arg_parser.add_argument("--animate", type=self.bool, dest="animate", default=False)
        self.arg_parser.add_argument("--directory", type=str, dest="directory", default='./')

    def effect(self):
        so = self.options

        # sets the position to the viewport center, round to next 10.
        position = [self.svg.namedview.center[0], self.svg.namedview.center[1]]
        position[0] = int(math.ceil(position[0] / 10.0)) * 10
        position[1] = int(math.ceil(position[1] / 10.0)) * 10

        root_layer = self.document.getroot()
        group = self.createGroup(root_layer, 'Spiro')

        # curve parameters
        R = so.radius_R
        r = so.radius_r
        d = so.pencil_distance
        finalTheta = 2 * np.pi * myLcm(abs(r), R) / R

        if 'hypo' in so.curveType.lower():
            typeCurve = 'hypo'
        if 'epi' in so.curveType.lower():
            typeCurve = 'epi'

        # markers and linestyles
        Lgray = inkDraw.color.gray(0.8)
        Dgray = inkDraw.color.gray(0.3)
        # wheel
        markerCenterDisk = inkDraw.marker.createDotMarker(self, nameID='diskCenter', scale=0.3, RenameMode=1, strokeColor=Dgray,
                                                          fillColor=inkDraw.color.defined('white'))
        markerPen = inkDraw.marker.createDotMarker(self, nameID='diskPen', scale=0.3, RenameMode=1, strokeColor=Dgray,
                                                   fillColor=inkDraw.color.defined('white'))
        [startArrowMarker, endArrowMarker] = inkDraw.marker.createArrow1Marker(self, nameID='arrowRot', RenameMode=1, scale=0.3, strokeColor=Dgray,
                                                                               fillColor=Dgray)

        if typeCurve == 'hypo':
            self.lineStyleArrow = inkDraw.lineStyle.set(lineWidth=r / 40, lineColor=Dgray, markerStart=startArrowMarker, markerEnd=None)
        else:
            self.lineStyleArrow = inkDraw.lineStyle.set(lineWidth=r / 40, lineColor=Dgray, markerStart=None, markerEnd=endArrowMarker)

        self.lineStyleARM = inkDraw.lineStyle.set(lineWidth=r / 40, lineColor=Dgray, markerStart=markerCenterDisk, markerEnd=markerPen)
        self.lineStyleDisk = inkDraw.lineStyle.set(lineWidth=r / 40, lineColor=None, fillColor=Lgray)

        # curve
        self.lineStyleCurve = inkDraw.lineStyle.set(lineWidth=0.8, lineColor=inkDraw.color.defined('red'), markerStart=None, markerEnd=None,
                                                    markerMid=None)
        self.lineStyleCurve2 = inkDraw.lineStyle.set(lineWidth=0.8, lineColor=inkDraw.color.defined('Dgreen'), markerStart=None, markerEnd=None,
                                                     markerMid=None)
        self.lineStyleCurve3 = inkDraw.lineStyle.set(lineWidth=0.8, lineColor=inkDraw.color.defined('blue'), markerStart=None, markerEnd=None,
                                                     markerMid=None)

        self.lineStylePre = inkDraw.lineStyle.set(lineWidth=1, lineColor=inkDraw.color.defined('red'))
        self.constructionLine = inkDraw.lineStyle.set(lineWidth=0.5, lineColor=Dgray)

        # draft Points
        if so.adaptiveTheta:
            nPrePoints = 10 * so.detailLevel  # number of pre points per turn
            thetasDraft = np.linspace(0, finalTheta, int(nPrePoints * finalTheta / (2 * np.pi)))

            [pointsDraft, _, curvatureDraft] = self.calcCurve__trochoid(typeCurve, R, r, d, thetasDraft)

            # find sampling points based on local curvature
            nSamples = np.ones(curvatureDraft.shape)*min(2,so.detailLevel)
            detailFactor=5
            # treshold normalized curvatures
            nSamples[curvatureDraft>0.8] *=detailFactor
            detailFactor = 2.5
            # check if vector changed direction abuptly
            for i,p in enumerate(pointsDraft):
                if i==0:
                    v1=pointsDraft[i+1]-pointsDraft[i]
                    v2=pointsDraft[i]-pointsDraft[-1]
                elif i < len(pointsDraft)-1:
                    v1=pointsDraft[i+1]-pointsDraft[i]
                    v2=pointsDraft[i]-pointsDraft[i-1]
                else:
                    v1=pointsDraft[0]-pointsDraft[i]
                    v2=pointsDraft[i]-pointsDraft[i-1]

                v1=v1/np.linalg.norm(v1)
                v2=v2/np.linalg.norm(v2)
                if np.dot(v1,v2)<0.5:
                    nSamples[i] *=detailFactor

            thetasFinal = np.array([])
            for i in range(len(nSamples) - 1):
                thetasFinal = np.append(thetasFinal, np.linspace(thetasDraft[i], thetasDraft[i + 1], int(nSamples[i]), endpoint=False))

            thetasFinal = np.append(thetasFinal, finalTheta)
            # filter the sampled angles to have a smooth transition.
            Ntaps = 5
            gaussWindow = scipySignal.gaussian(Ntaps, std=5)
            gaussWindow = gaussWindow / np.sum(gaussWindow)

            # inkPlot.plot.cartesian(self, root_layer, np.arange(thetasFinal.shape[0]), thetasFinal * 180 / np.pi, position, xTicks=False, yTicks=True, xTickStep=thetasFinal.shape[0]/10, yTickStep=120.0, xScale=10, yScale=10,xGrid=True, yGrid=True, forceXlim=None, forceYlim=None)
            thetasFinal = scipySignal.filtfilt(gaussWindow, np.array([1]), thetasFinal)

            # inkPlot.plot.cartesian(self, root_layer, np.arange(thetasFinal.shape[0]), thetasFinal * 180 / np.pi, position, xTicks=False, yTicks=True,xTickStep=thetasFinal.shape[0]/10, yTickStep=120.0, xScale=10, yScale=10, xGrid=True, yGrid=True, forceXlim=None, forceYlim=None,drawAxis=False)
        else:
            nPrePoints = 20 * so.detailLevel  # number of pre points per turn
            thetasFinal = np.linspace(0, finalTheta, int(nPrePoints * finalTheta / (2 * np.pi)))

        # final shape
        [PointsFinal, CentersFinal, curvatureFinal] = self.calcCurve__trochoid(typeCurve, R, r, d, thetasFinal)
        [PointsFinal2, CentersFinal2, curvatureFinal2] = self.calcCurve__trochoid(typeCurve, R, r, -d, thetasFinal)
        [PointsFinal3, CentersFinal3, curvatureFinal3] = self.calcCurve__trochoid(typeCurve, R, r, r, thetasFinal)

        if so.animate:
            animGroup = self.createGroup(group, 'Anim')

            circle_R = inkDraw.circle.centerRadius(parent=animGroup, centerPoint=[0, 0], radius=R, offset=position, lineStyle=self.constructionLine)

            # draw planetary wheel
            wheelGroup = self.createGroup(animGroup, 'Anim')
            circle_r = inkDraw.circle.centerRadius(wheelGroup, centerPoint=CentersFinal[0], radius=r, offset=position, lineStyle=self.lineStyleDisk)
            arms1 = inkDraw.line.absCoords(wheelGroup, coordsList=[CentersFinal[0], PointsFinal[0]], offset=position, lineStyle=self.lineStyleARM)
            arms2 = inkDraw.line.absCoords(wheelGroup, coordsList=[CentersFinal2[0], PointsFinal2[0]], offset=position, lineStyle=self.lineStyleARM)
            arms3 = inkDraw.line.absCoords(wheelGroup, coordsList=[CentersFinal3[0], PointsFinal3[0]], offset=position, lineStyle=self.lineStyleARM)

            arc1 = inkDraw.arc.centerAngStartAngEnd(wheelGroup, centerPoint=CentersFinal[0], radius=r * 0.6, angStart=40, angEnd=80, offset=position,
                                                    lineStyle=self.lineStyleArrow)
            arc2 = inkDraw.arc.centerAngStartAngEnd(wheelGroup, centerPoint=CentersFinal[0], radius=r * 0.6, angStart=160, angEnd=200,
                                                    offset=position, lineStyle=self.lineStyleArrow)
            arc3 = inkDraw.arc.centerAngStartAngEnd(wheelGroup, centerPoint=CentersFinal[0], radius=r * 0.6, angStart=280, angEnd=320,
                                                    offset=position, lineStyle=self.lineStyleArrow)

            self.exportSVG(animGroup, os.path.join(so.directory,'outSVG_%1.5d.svg' % 0))

            for i in range(1, len(thetasFinal)):

                self.moveElement(wheelGroup, [CentersFinal[i][0] - CentersFinal[i - 1][0], CentersFinal[i][1] - CentersFinal[i - 1][1]])
                if typeCurve == 'hypo':
                    self.rotateElement(wheelGroup, [position[0] + CentersFinal[i][0], position[1] + CentersFinal[i][1]],
                                       (thetasFinal[i] - thetasFinal[i - 1]) * (R - r) / r * 180 / np.pi)
                else:
                    self.rotateElement(wheelGroup, [position[0] + CentersFinal[i][0], position[1] + CentersFinal[i][1]],
                                       - (thetasFinal[i] - thetasFinal[i - 1]) * (R + r) / r * 180 / np.pi)

                curve1 = inkDraw.line.absCoords(parent=animGroup, coordsList=PointsFinal[:i + 1], offset=position, lineStyle=self.lineStyleCurve,
                                               closePath=False)
                curve2 = inkDraw.line.absCoords(parent=animGroup, coordsList=PointsFinal2[:i + 1], offset=position, lineStyle=self.lineStyleCurve2,
                                                closePath=False)
                curve3 = inkDraw.line.absCoords(parent=animGroup, coordsList=PointsFinal3[:i + 1], offset=position, lineStyle=self.lineStyleCurve3,
                                                closePath=False)

                self.exportSVG(animGroup, os.path.join(so.directory , 'outSVG_%1.5d.svg' % i))

                self.removeElement(curve1)
                self.removeElement(curve2)
                self.removeElement(curve3)
            self.removeElement(animGroup)
        else:
            if so.drawBaseCircles:
                inkDraw.circle.centerRadius(parent=group, centerPoint=position, radius=R, offset=[0, 0], lineStyle=self.constructionLine)

                if typeCurve == 'hypo':
                    inkDraw.circle.centerRadius(parent=group, centerPoint=position, radius=r, offset=[R - r, 0], lineStyle=self.constructionLine)
                if typeCurve == 'epi':
                    inkDraw.circle.centerRadius(parent=group, centerPoint=position, radius=r, offset=[R + r, 0], lineStyle=self.constructionLine)

            inkDraw.line.absCoords(group, PointsFinal, position, 'spiro', self.lineStyleCurve, closePath=True)

            # plot curvatures
            if False:
                inkPlot.plot.polar(self, group, curvatureFinal, thetasFinal * 180 / np.pi, [position[0] + 3 * R, position[1]], rTicks=False,
                                   tTicks=False, rTickStep=0.2, tTickStep=45.0, rScale=20, rGrid=True, tGrid=True, lineStylePlot=self.lineStyleCurve,
                                   forceRlim=[0.0, 1.0])

        return

    # typeCurve: 'hypo', 'epi'
    def calcCurve__trochoid(self, typeCurve, R, r, d, thetas):
        j = complex(0, 1)
        if typeCurve.lower() == 'hypo':
            # https://www.mathcurve.com/courbes2d.gb/hypotrochoid/hypotrochoid.shtml
            P_complex = (R - r) * np.exp(j * thetas) + d * np.exp(-j * thetas * (R - r) / r)
            dP_complex = (R - r) * j * np.exp(j * thetas) + d * (-j) * (R - r) / r * np.exp(-j * thetas * (R - r) / r)
            ddP_complex = (R - r) * (-1) * np.exp(j * thetas) + d * (-1) * ((R - r) / r) ** 2 * np.exp(-j * thetas * (R - r) / r)
            centerGear = (R - r) * np.exp(j * thetas)
        if typeCurve.lower() == 'epi':
            # https://www.mathcurve.com/courbes2d.gb/epitrochoid/epitrochoid.shtml
            P_complex = (R + r) * np.exp(j * thetas) - d * np.exp(j * thetas * (R + r) / r)
            dP_complex = (R + r) * j * np.exp(j * thetas) - d * j * (R + r) / r * np.exp(j * thetas * (R + r) / r)
            ddP_complex = (R + r) * (-1) * np.exp(j * thetas) - d * (-1) * ((R + r) / r) ** 2 * np.exp(j * thetas * (R + r) / r)
            centerGear = (R + r) * np.exp(j * thetas)

        with np.errstate(divide='ignore', invalid='ignore'):
            curvature = np.divide(abs(dP_complex.real * ddP_complex.imag - dP_complex.imag * ddP_complex.real),
                                  (dP_complex.real ** 2 + dP_complex.imag ** 2) ** (2 / 3))

        # remove Nan=0/0
        np.nan_to_num(curvature, copy=False)

        # remove values too large
        curvature[curvature > 10 * np.mean(curvature)] = 0.0

        # self.Dump(curvature, '/home/fernando/lixo.txt', 'w')
        # normalize curvature
        curvature = self._normalizeCurvatures(curvature, 0.0, 1.0)

        Points = np.column_stack((P_complex.real, P_complex.imag))
        Centers = np.column_stack((centerGear.real, centerGear.imag))

        return [Points, Centers, curvature]

    def _normalizeCurvatures(self, curvatures, normMin=0.0, normMax=1.0):
        y1 = normMin
        y2 = normMax
        x1 = np.min(curvatures)
        x2 = np.max(curvatures)
        alpha = (y2 - y1) / (x2 - x1)
        return alpha * (curvatures - x1) + y1


if __name__ == '__main__':
    sp = Spirograph()
    sp.run()
