#!/usr/bin/env python3

import math
import os
import inkex
from inkex.paths import Path
from geometry.Circle import Circle
from geometry.Vertex import Vertex
from geometry.Triangle import Triangle
from geometry.Plus import Plus
from geometry.Minus import Minus
from lxml import etree

ALL=".//"

def fixTo360(radian):
    if radian < 0:
        return math.pi * 2.0 + radian
    return radian
    
def widenDir(start, end):
    d21x = end.x - start.x;
    d21y = end.y - start.y;
    return fixTo360(-math.atan2(d21x, d21y));
    
def lineDir(start, end):
    d21x = end.x - start.x;
    d21y = end.y - start.y;
    #inkex.errormsg("d21y "+str(d21y)+" d21x "+str(d21x)+" d21y/d21x"+str(d21y/d21x))
    rad=math.atan2(d21y, d21x);
    #inkex.errormsg(u"Line direction"+str(math.degrees(rad)))
    return fixTo360(rad)

#radian<The assumption is that 0 will not come
def invert(radian):
    return radian - math.pi
    
def fixWithin90(radian):
    if math.fabs(radian) > math.pi / 2.0: #I want you to be +-90 (forward direction)
        return invert(radian)
    return radian
    
def fixOver90(radian):
    if math.fabs(radian) < math.pi / 2.0:
        return invert(radian)
    return radian
    
def fixWithinAb180(radian):
    if math.fabs(radian) < math.pi:
        return radian
        
    if radian < 0:
        return math.pi * 2.0 + radian
    return radian - math.pi * 2.0

def printRadian(fp, message, radian):
    fp.write(message+":"+str(math.degrees(radian))+"\n")
    
def stripline(bone, line_width, log_directory, log_filename):
    try:
        with open(os.path.join(log_directory, log_filename),'w', encoding = 'utf-8') as fp:
            i = 0;
            segmentNum = len(bone) - 1;
            elementNum = (segmentNum * 2 + 2) * 5
            outVertexArray = []
            #4 vertices per line segment+Extra amount added to the end point
            vertexIdx = 0
            #First apex
            start = bone[0]
            end = bone[1]
            lastRad = 0
            lastUsedRad = 0
            radY = widenDir(start, end)
            lineRad=lineDir(start, end)
            fp.write(u"0th vertex")
            printRadian(fp, u"lineRad", lineRad)
        
            originalRad = radY
        
            #Indicates the direction of bending
            cornerDir = radY - lastRad
            printRadian(fp, u"radY", radY)
            diffRad = 0
            printRadian(fp, u"diffRad:", diffRad)
            printRadian(fp, u"radY-lineRad:", radY - lineRad)
            printRadian(fp, u"sin(radY-lineRad:)", math.sin(radY - lineRad))
        
            adjustedRad = radY
            printRadian(fp, u"The first drawing angle", adjustedRad)
            fp.write("\n")
            direction=True
            lastRad=radY
        
            lastUsedRad = adjustedRad
            LEFT = Vertex(line_width, 0)
            RIGHT = Vertex(-line_width, 0)
            #variable
            v = Vertex(0,0)
            v.set(LEFT)
            v.rotate(adjustedRad)
            flag = False #if radY < 0 else False
            outVertexArray.append([start + v, flag])
        
            v.set(RIGHT)
            v.rotate(adjustedRad)
            flag = True# if radY< 0 else False
            outVertexArray.append([start + v, flag])
        
            for i in range(1, segmentNum, 1):
                start = bone[i]
                end = bone[i + 1]
                originalRad = widenDir(start,end)
                radY = (originalRad + lastRad) * 0.5 #Values ​​from 0 to 360 degrees
                fp.write(str(i) + u"Th vertex")
                diffRad = (originalRad - lastRad)
                if math.fabs(math.fabs(diffRad) - math.pi) <= (45.0 * math.pi / 180.0):#To erase the pointed triangle when making a U-turn
                    printRadian(fp, u"Correction of U-turn point:diffRad", diffRad)
                    fp.write(u"Difference" + str(math.fabs(math.fabs(diffRad) - math.pi)))
                    radY = originalRad
        
                printRadian(fp, u"radY:", radY)
                printRadian(fp, u"diffRad:", diffRad)
                printRadian(fp, u"radY - lineRad:", radY - lineRad)
                printRadian(fp, u"sin(radY - lineRad:)", math.sin(radY - lineRad))
                #Twist prevention
                if math.sin(radY - lineRad) > 0:
                    radY = invert(radY)
        
                lineRad = lineDir(start, end)
        
                printRadian(fp, u"lineRad:", lineRad)
                adjustedRad = radY
                printRadian(fp, u"diffRad:", diffRad)
                squareRad = lineDir(start, end)
                #printRadian(u"squareRad",squareRad)
                printRadian(fp, u"Drawing angle after conversion:", radY)
                v.set(LEFT)
                #1〜√2 I want you to be in the range
                coef = (1 + 0.41421356237 * math.fabs(math.sin(diffRad * 0.5)))
                fp.write("coef=" + str(coef))
                v.x *= coef
                v.rotate(adjustedRad)
                flag = False
                outVertexArray.append([start + v, flag])
                v.set(RIGHT)
                v.x *= coef
                v.rotate(adjustedRad)
                flag = True
                outVertexArray.append([start + v , flag])
                lastRad = originalRad
                lastUsedRad = adjustedRad
                fp.write("\n")
                #The last round
                fp.write(str(i) + u"Th vertex")
                adjustedRad = originalRad
                printRadian(fp, u"Last drawing angle:",originalRad)
                v.set(LEFT)
                v.rotate(adjustedRad)
                flag = False # if originalRad< 0 else False
                outVertexArray.append([end + v, flag])
                v.set(RIGHT)
                v.rotate(adjustedRad)
                flag = True # if originalRad< 0 else False
                outVertexArray.append([end + v, flag])
            fp.close()
            return outVertexArray
    except IOError as error: # parent of IOError, OSError *and* WindowsError where available
        inkex.utils.debug(str("Directory error. Please select another one and try again!"))
        exit()

class StripLine(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--line_width", type = int, default = "10", help = "Line thickness")
        pars.add_argument("--unit", default = "mm", help = "Width unit")
        pars.add_argument("--log_directory", default = "~/", help = "Log directory")
        pars.add_argument("--log_filename", default = "stripline.log", help = "Log file name")
        
    def effect(self):
        line_width = self.svg.unittouu(str(self.options.line_width) + self.options.unit)
        # Get the main root element SVG
        svg = self.document.getroot()
        pathlist = svg.findall(ALL + "{" + inkex.NSS['svg'] + "}path")

        for path in pathlist:
            if path == None:
                inkex.errormsg("Please write the path! !")
            #Get vertex coordinates of path
            vals = path.path.to_arrays()
            bone = []
            for cmd, vert in vals:
                #Sometimes there is an empty, so countermeasures against it
                #inkex.utils.debug("{},{}".format(cmd, vert))
                if len(vert) != 0:
                    bone.append(Vertex(vert[0], vert[1]))
                        
            if len(bone) != 0:
                outVertexArray = stripline(bone, line_width, self.options.log_directory, self.options.log_filename)
            pointer = 0
            for t in range(len(outVertexArray) - 2):
                tri = Triangle(outVertexArray[pointer][0], outVertexArray[pointer+1][0], outVertexArray[pointer+2][0])

                stripstr = tri.toSVG()
                color2 = "blue"
                if outVertexArray[pointer][1]:
                    color = "blue"
                else:
                    color = "red"
                pointer += 1
                attributes = {"points": stripstr,
                "style":"fill:" + color2 + ";stroke:" + color2 + ";stroke-width:" + str(line_width / 3), "fill-opacity": "0.5"}
                pth = etree.Element("polygon", attributes)
                svg.append(pth)
            pointer = 0
            #Draw a point indicating +-
            for t in range(len(outVertexArray)):

                if outVertexArray[pointer][1]:
                    point = Plus(outVertexArray[pointer][0].x, outVertexArray[pointer][0].y, line_width / 3)
                    color = "blue"
                else:
                    point = Minus(outVertexArray[pointer][0].x, outVertexArray[pointer][0].y, line_width / 3)
                    color = "red"
                if pointer == 0:
                    color = "#6f0018"#Dark red
                point.appendToSVG(color, svg)
                #svg.append(Circle.toSVG(outVertexArray[pointer][0].x,outVertexArray[pointer][0].y,line_width/3,color,0))
                pointer += 1
            pointer = 0
            pathstr = "M "
            for t in range(len(outVertexArray)):
                pathstr += str(outVertexArray[pointer][0].x) + " "+str(outVertexArray[pointer][0].y) + " "
                pointer += 1

            att3 = {"d":pathstr,"r":"1","fill":"none","stroke-width":"1","stroke":"white"}
            pt = etree.Element("path", att3)

if __name__ == '__main__':
    StripLine().run()