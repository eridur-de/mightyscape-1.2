#!/usr/bin/env python3

"""
Copyright (C) 2017 Corentin Brulé

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Special thanks and orignal copyrigths : Aaron Spike (2005) and Timo Kähkönen (2012)
"""

import inkex
import re
from lxml import etree
from inkex.transforms import Transform
from inkex.paths import Path, CubicSuperPath

__version__ = '0.1'

debug=False

def distort_path(path_str,source,destination):
    path_arr = path_string_to_array(path_str)

    subpath_type=""
    is_num =""
    xy_counter =""
    xy=""
    path_arr2=[]
    subpath_type_upper=""
    point=""
    i=0
    for i in range(len(path_arr)):
        patt1 = r"[mzlhvcsqta]"

        curr = path_arr[i]
        if re.match(patt1,curr,flags=re.I):
            xy_counter = -1
            subpath_type = curr
            subpath_type_upper = subpath_type.upper()
            is_num = False
            path_arr2.append(curr)
        else :
            is_num = True
            curr = float(curr)

        if xy_counter%2 == 0:
            xy="x"
        else:
             xy="y"

        if is_num :
            if xy=="y" :
                point = transferPoint(float(path_arr[i-1]),curr,source,destination)
                path_arr2.append(point["x"])
                path_arr2.append(point["y"])

        xy_counter+=1

    path_str = path_array_to_string(path_arr2)
    return path_str


def path_array_to_string(path_arr):

    path_str=str(path_arr)

    path_str=path_str.replace(r"([0-9]),([-0-9])", "$1 $2")
    path_str=path_str.replace(r"([0-9]),([-0-9])", "$1 $2")
    path_str=path_str.replace(",", "")
    path_str=path_str.replace("[", "").replace("]","")
    path_str=path_str.replace("'", "")

    return path_str

def path_string_to_array(path_str):

    patt1=r"[mzlhvcsqta]|-?[0-9.]+" #gi
    #path_arr=path_str.match(patt1) #array de résultats
    path_arr = re.findall(patt1,path_str,flags=re.I)

    patt1=r"[mzlhvcsqta]" #i
    i = 0
    for i in range(len(path_arr)):
        if re.match(path_arr[i],patt1,flags=re.I) == -1:
            path_arr[i] = float(path_arr[i])

    return path_arr

'''
def isPermissible(p):
    p0 = {x:c0.attr("cx"),y:c0.attr("cy")}
    p1 = {x:c1.attr("cx"),y:c1.attr("cy")}
    p2 = {x:c2.attr("cx"),y:c2.attr("cy")}
    p3 = {x:c3.attr("cx"),y:c3.attr("cy")}
    a0 = angle(p3, p0, p1)
    a1 = angle(p0, p1, p2)
    a2 = angle(p1, p2, p3)
    a3 = angle(p2, p3, p0)
    if not (a0 > 0 and a0 < 180) or not (a1 > 0 and a1 < 180) or not(a2 > 0 and a2 < 180) or not(a3 > 0 and a3 < 180) :
        return False
    else :
        return True
}

def angle(c, b, a):
  ab = {x: b.x - a.x, y: b.y - a.y }
  cb = {x: b.x - c.x, y: b.y - c.y }
  dot = (ab.x * cb.x + ab.y * cb.y)
  cross = (ab.x * cb.y - ab.y * cb.x)
  alpha = Math.atan2(cross, dot)
  return alpha * 180 / PI
}
'''

def transferPoint (xI, yI, source, destination):

    ADDING = 0.001 # to avoid dividing by zero

    xA = source[0]["x"]
    yA = source[0]["y"]

    xC = source[2]["x"]
    yC = source[2]["y"]

    xAu = destination[0]["x"]
    yAu = destination[0]["y"]

    xBu = destination[1]["x"]
    yBu = destination[1]["y"]

    xCu = destination[2]["x"]
    yCu = destination[2]["y"]

    xDu = destination[3]["x"]
    yDu = destination[3]["y"]

    # Calcultations
    if xBu==xCu :
        xCu+=ADDING
    if xAu==xDu :
        xDu+=ADDING
    if xAu==xBu :
        xBu+=ADDING
    if xDu==xCu :
        xCu+=ADDING
    kBC = float(yBu-yCu)/float(xBu-xCu)
    kAD = float(yAu-yDu)/float(xAu-xDu)
    kAB = float(yAu-yBu)/float(xAu-xBu)
    kDC = float(yDu-yCu)/float(xDu-xCu)

    if kBC==kAD :
        kAD += ADDING
    xE = float(kBC*xBu - kAD*xAu + yAu - yBu) / float(kBC-kAD)
    yE = kBC*(xE - xBu) + yBu

    if kAB==kDC :
        kDC += ADDING
    xF = float(kAB*xBu - kDC*xCu + yCu - yBu) / float(kAB-kDC)
    yF = kAB*(xF - xBu) + yBu

    if xE==xF :
        xF += ADDING
    kEF = float(yE-yF) / float(xE-xF)

    if kEF==kAB:
        kAB += ADDING
    xG = float(kEF*xDu - kAB*xAu + yAu - yDu) / float(kEF-kAB)
    yG = kEF*(xG - xDu) + yDu

    if kEF==kBC :
        kBC+=ADDING
    xH = float(kEF*xDu - kBC*xBu + yBu - yDu) / float(kEF-kBC)
    yH = kEF*(xH - xDu) + yDu

    rG = float(yC-yI)/float(yC-yA)
    rH = float(xI-xA)/float(xC-xA)

    xJ = (xG-xDu)*rG + xDu
    yJ = (yG-yDu)*rG + yDu

    xK = (xH-xDu)*rH + xDu
    yK = (yH-yDu)*rH + yDu

    if xF==xJ:
        xJ+=ADDING
    if xE==xK:
        xK+=ADDING
    kJF = float(yF-yJ) / float(xF-xJ)
    kKE = float(yE-yK) / float(xE-xK)

    xKE = ""
    if kJF==kKE:
        kKE += ADDING
    xIu = float(kJF*xF - kKE*xE + yE - yF) / float(kJF-kKE)
    yIu = kJF * (xIu - xJ) + yJ

    b = {"x":xIu,"y":yIu}
    b["x"] = round(b["x"])
    b["y"] = round(b["y"])
    return b


def projection(path_object,coords):

    pp_object = Path(path_object).to_arrays()

    bounds = Path(path_object).bounding_box()

    # Make array of coordinates, every array member represent corner of text path
    source = [
    {"x":bounds.left,"y":bounds.top},
    {"x":bounds.right,"y":bounds.top},
    {"x":bounds.right,"y":bounds.bottom},
    {"x":bounds.left,"y":bounds.bottom}
    ]

    destination=[
    {"x":coords[0][0],"y":coords[0][1]},
    {"x":coords[1][0],"y":coords[1][1]},
    {"x":coords[2][0],"y":coords[2][1]},
    {"x":coords[3][0],"y":coords[3][1]}
    ]

    path_destination = distort_path(path_object,source,destination)

    return path_destination
'''
def complex2tulpe(complexNb):
    return (complexNb.real,complexNb.imag)
'''
class AnotherPerspective(inkex.EffectExtension):

    def envelope2coords(self, path_envelope):
        pp_envelope = CubicSuperPath(path_envelope)
        if len(pp_envelope[0]) < 4:
            inkex.errormsg("The selected envelope (your second path) does not contain enough nodes. Check to have at least 4 nodes.")
            exit()

        c0 = pp_envelope[0][0][0]
        c1 = pp_envelope[0][1][0]
        c2 = pp_envelope[0][2][0]
        c3 = pp_envelope[0][3][0]
        # inkex.debug(str(c0)+" "+str(c1)+" "+str(c2)+" "+str(c3))
        return [c0, c1, c2, c3]

    def effect(self):
        if len(self.options.ids) < 2:
            inkex.errormsg("This extension requires two selected paths.")
            exit()

        obj = self.svg.selected[self.options.ids[0]]
        envelope = self.svg.selected[self.options.ids[1]]

        if obj.get(inkex.addNS('type','sodipodi')):
            inkex.errormsg("The first selected object is of type '%s'.\nTry using the procedure Path->Object to Path." % obj.get(inkex.addNS('type','sodipodi')))
            exit()

        if obj.tag == inkex.addNS('path','svg') or obj.tag == inkex.addNS('g','svg'):
            if envelope.tag == inkex.addNS('path','svg'):
                mat = envelope.transform @ Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                path = CubicSuperPath(envelope.get('d'))
                Path(path).transform(mat)
                absolute_envelope_path = envelope.get('d')
                # inkex.debug(absolute_envelope_path)
                coords_to_project = self.envelope2coords(absolute_envelope_path)

                if obj.tag == inkex.addNS('path','svg'):
                    mat = obj.transform @ Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                    absolute_d = str(Path(obj.get('d')))
                    path = CubicSuperPath(absolute_d)
                    Path(path).transform(mat)
                    absolute_object_path = str(path)
                    # inkex.debug(absolute_object_path)

                elif obj.tag == inkex.addNS('g','svg'):
                    absolute_object_path=""
                    for p in obj.iterfind(".//{http://www.w3.org/2000/svg}path"):

                        absolute_d = str(Path(p.get('d')))
                        mat = p.transform * Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
                        path = CubicSuperPath(absolute_d)
                        Path(path).transform(mat)
                        absolute_object_path += str(Path(path))
                        # inkex.debug(absolute_object_path)

                new_path = projection(absolute_object_path,coords_to_project)
                attributes = {'d':new_path, 'style':str(obj.style)}
                new_element = etree.SubElement(self.svg.get_current_layer(),inkex.addNS('path','svg'),attributes)

            else:
                if envelope.tag == inkex.addNS('g','svg'):
                    inkex.errormsg("The second selected object is a group, not a path.\nTry using the procedure Object->Ungroup.")
                else:
                    inkex.errormsg("The second selected object is not a path.\nTry using the procedure Path->Object to Path.")
                exit()
        else:
            inkex.errormsg("The first selected object is not a path.\nTry using the procedure Path->Object to Path.")
            exit()

if __name__ == '__main__':
   AnotherPerspective().run()