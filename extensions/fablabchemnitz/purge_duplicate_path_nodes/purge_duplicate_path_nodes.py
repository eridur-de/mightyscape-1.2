#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2020 Ellen Wasboe, ellen@wasbo.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
"""
Remove duplicate nodes or interpolate nodes with distance less than specified.
Optionally:
    join start and end node of each subpath if distance < threshold
    join separate subpaths if end nodes closer than threshold
Joining subpaths can be done either by interpolating or straight line segment.
"""
import inkex
from inkex import bezier, CubicSuperPath
import numpy as np
from tkinter import messagebox


def join_search(xdiff, ydiff, limDist, idsIncluded):
    """Search for loose ends to join if within limDist."""
    joinFlag = False
    idJoin = -1
    dist = np.sqrt(np.add(np.power(xdiff, 2), np.power(ydiff, 2)))
    minDist = np.amin(dist)
    if minDist < limDist:
        joinFlag = True
        idMins = np.where(dist == minDist)
        idMin = idMins[0]
        idJoin = idsIncluded[idMin[0]]

    return [joinFlag, idJoin]


def reverse_sub(subPath):
    """Reverse sub path."""
    subPath = subPath[::-1]
    for i, s in enumerate(subPath):
        subPath[i] = s[::-1]

    return subPath


def join_sub(sub1, sub2, interpolate_or_line):
    """Join line segments by interpolation or straight line segment."""
    if interpolate_or_line == "1":
        # interpolate end nodes
        p1 = sub1[-1][-1]
        p2 = sub2[0][0]
        joinNode = [0.5 * (p1[0] + p2[0]), 0.5 * (p1[1] + p2[1])]
        # remove end/start + input join
        sub1[-1][1] = joinNode
        sub1[-1][2] = sub2[0][2]
        sub2.pop(0)

    newsub = sub1 + sub2

    return newsub


def remove_duplicate_nodes(
    elem, minlength, maxdist, maxdist2, allowReverse, optionJoin
):

    pp = elem.path.to_absolute()

    # register which subpaths are closed - to reset closing after
    # info are lost in to_superpath
    dList = str(pp).upper().split(" M")
    closed = []
    li = 0
    for sub in dList:
        if dList[li].find("Z") > -1:
            closed.append(" Z ")
        else:
            closed.append("")
        li += 1

    new = []
    nSub = len(closed)

    xStart = np.zeros(nSub)  # x start - prepare for joining subpaths
    yStart = np.copy(xStart)
    xEnd = np.copy(xStart)
    yEnd = np.copy(xStart)

    s = 0
    for sub in pp.to_superpath():
        new.append([sub[0]])
        if maxdist2 > -1:
            xStart[s] = sub[0][0][0]
            yStart[s] = sub[0][0][1]
            xEnd[s] = sub[-1][-1][0]
            yEnd[s] = sub[-1][-1][1]
        # remove segment if segment length is less than minimum set,
        # keep position
        i = 1
        lastCombined = False
        while i <= len(sub) - 1:
            length = bezier.cspseglength(new[-1][-1], sub[i])  # curve length
            if length >= minlength:
                new[-1].append(sub[i])  # add as is
                lastCombined = False
            else:
                # keep including segments until total length > minlength
                summedlength = length
                proceed = True
                e = 0  # extra segments
                finishedAdding = False
                while proceed and i + e + 1 <= len(sub) - 1:
                    nextlength = bezier.cspseglength(sub[i + e], sub[i + e + 1])
                    if nextlength >= minlength:  # not include the next segment
                        proceed = False
                        if lastCombined == False and i > 1:
                            # i.e.small group between long segments,
                            # average over the group, first node already added

                            # change position to average
                            new[-1][-1][1][0] = 0.5 * (
                                new[-1][-1][1][0] + sub[i + e][1][0]
                            )
                            new[-1][-1][1][1] = 0.5 * (
                                new[-1][-1][1][1] + sub[i + e][1][1]
                            )

                            # change last cp to that of the last node in group
                            new[-1][-1][2] = sub[i + e][2]
                            finishedAdding = True
                        else:
                            new[-1].append(sub[i])  # add as is
                            if e > 0:
                                # end of group with many segments - average over
                                # all but last node (which is added separately)

                                # change position to average first/last
                                new[-1][-1][1][0] = 0.5 * (
                                    new[-1][-1][1][0] + sub[i + e - 1][1][0]
                                )
                                new[-1][-1][1][1] = 0.5 * (
                                    new[-1][-1][1][1] + sub[i + e - 1][1][1]
                                )

                                # change last cp to that of the last node in group
                                new[-1][-1][2] = sub[i + e - 1][2]
                                new[-1].append(sub[i + e])  # add as is
                            finishedAdding = True
                        lastCombined = True
                    else:
                        summedlength = summedlength + nextlength
                        if summedlength >= minlength:
                            proceed = False
                        e = e + 1

                if finishedAdding == False:

                    if i == 1:
                        # if first segment keep position of first node,
                        # direction of last in group
                        new[-1][-1][2][0] = sub[i + e][2][0]
                        new[-1][-1][2][1] = sub[i + e][2][1]
                    elif i + e == len(sub) - 1:
                        # if last segment included keep position of last node,
                        # direction of previous
                        new[-1].append(sub[i])  # add first node in group
                        if e > 0:
                            new[-1].append(sub[i + e])  # add last node
                            # get first cp from i+1
                            new[-1][-1][0] = sub[i + 1][0]

                    else:
                        # average position over first/last in group and keep direction (controlpoint) of first/last node
                        # group within sequence of many close nodes - add new without averaging on previous
                        new[-1].append(sub[i])  # add first node in group

                        # change position to average
                        new[-1][-1][1][0] = 0.5 * (new[-1][-1][1][0] + sub[i + e][1][0])
                        new[-1][-1][1][1] = 0.5 * (new[-1][-1][1][1] + sub[i + e][1][1])

                        # change last cp to that of the last node in group
                        new[-1][-1][2] = sub[i + e][2]

                i = i + e

            i += 1

        if closed[s] == " Z ":
            # if new[-1][-1][1]==new[-1][-2][1]:#not always precise
            new[-1].pop(-1)
            # for some reason tosuperpath adds an extra node for closed paths

        # close each subpath where start/end node is closer than maxdist set
        # (if not already closed)
        if maxdist > -1:
            if closed[s] == "":  # ignore already closed paths
                # calculate distance between first and last node,
                # if <= maxdist set closed[i] to " Z "
                # last=new[-1][-1]
                length = bezier.cspseglength(new[-1][-1], sub[0])
                if length < maxdist:
                    newStartEnd = [
                        0.5 * (new[-1][-1][-1][0] + new[-1][0][0][0]),
                        0.5 * (new[-1][-1][-1][1] + new[-1][0][0][1]),
                    ]
                    new[-1][0][0] = newStartEnd
                    new[-1][0][1] = newStartEnd
                    new[-1][-1][1] = newStartEnd
                    new[-1][-1][2] = newStartEnd
                    closed[s] = " Z "

        s += 1

    # join different subpaths?
    closed = np.array(closed)
    openPaths = np.where(closed == "")
    closedPaths = np.where(closed == " Z ")
    if maxdist2 > -1 and openPaths[0].size > 1:
        # calculate distance between end nodes of the subpaths.
        # If distance < maxdist2 found - join
        joinStartToEnd = np.ones(nSub, dtype=bool)
        joinEndToStart = np.copy(joinStartToEnd)
        joinEndTo = np.full(nSub, -1)
        # set higher than maxdist2 to avoid join to closedPaths
        joinEndTo[closedPaths] = 2 * maxdist2
        joinStartTo = np.copy(joinEndTo)

        # join end node of current subpath to startnode of any other
        # or start node of current to end node of other (no reverse)
        s = 0
        while s < nSub:
            # end of current to start of other
            if joinEndTo[s] == -1:
                # find available start nodes
                idsTest = np.where(joinStartTo == -1)
                # avoid join to self
                id2Test = np.delete(idsTest[0], np.where(idsTest[0] == s))
                if id2Test.size > 0:
                    # calculate distances in x/y direction
                    diff_x = np.subtract(xStart[id2Test], xEnd[s])
                    diff_y = np.subtract(yStart[id2Test], yEnd[s])
                    # find shortest distance if less than minimum
                    res = join_search(diff_x, diff_y, maxdist2, id2Test)
                    if res[0] == True:
                        # if match found flag end of this with id of other and flag start of match to end of this
                        joinEndTo[s] = res[1]
                        joinStartTo[res[1]] = s

            # start of current to end of other
            if joinStartTo[s] == -1:
                idsTest = np.where(joinEndTo == -1)
                id2Test = np.delete(idsTest[0], np.where(idsTest[0] == s))
                if id2Test.size > 0:
                    diff_x = np.subtract(xEnd[id2Test], xStart[s])
                    diff_y = np.subtract(yEnd[id2Test], yStart[s])
                    res = join_search(diff_x, diff_y, maxdist2, id2Test)
                    if res[0] == True:
                        joinStartTo[s] = res[1]
                        joinEndTo[res[1]] = s

            if allowReverse == True:
                # start to start - if match reverse (reverseSub[s]=True)
                if joinStartTo[s] == -1:
                    idsTest = np.where(joinStartTo == -1)
                    id2Test = np.delete(idsTest[0], np.where(idsTest[0] == s))
                    if id2Test.size > 0:
                        diff_x = np.subtract(xStart[id2Test], xStart[s])
                        diff_y = np.subtract(yStart[id2Test], yStart[s])
                        res = join_search(diff_x, diff_y, maxdist2, id2Test)
                        if res[0] == True:
                            jID = res[1]
                            joinStartTo[s] = jID
                            joinStartTo[jID] = s
                            joinStartToEnd[s] = False  # false means reverse
                            joinStartToEnd[jID] = False

                # end to end
                if joinEndTo[s] == -1:
                    idsTest = np.where(joinEndTo == -1)
                    id2Test = np.delete(idsTest[0], np.where(idsTest[0] == s))
                    if id2Test.size > 0:
                        diff_x = np.subtract(xEnd[id2Test], xEnd[s])
                        diff_y = np.subtract(yEnd[id2Test], yEnd[s])
                        res = join_search(diff_x, diff_y, maxdist2, id2Test)
                        if res[0] == True:
                            jID = res[1]
                            joinEndTo[s] = jID
                            joinEndTo[jID] = s
                            joinEndToStart[s] = False
                            joinEndToStart[jID] = False

            s += 1

        old = new
        new = []
        s = 0
        movedTo = np.arange(nSub)
        newClosed = []
        # avoid joining to other paths if already closed
        joinEndTo[closedPaths] = -1
        joinStartTo[closedPaths] = -1

        for s in range(0, nSub):
            if movedTo[s] == s:  # not joined yet
                if joinEndTo[s] > -1 or joinStartTo[s] > -1:
                    # any join scheduled
                    thisSub = []
                    closedThis = ""
                    if joinEndTo[s] > -1:
                        # join one by one until -1 or back to s (closed)
                        jID = joinEndTo[s]
                        sub1 = old[s]
                        sub2 = old[jID]
                        rev = True if joinEndToStart[s] == False else False
                        sub2 = reverse_sub(sub2) if rev == True else sub2
                        thisSub = join_sub(sub1, sub2, optionJoin)
                        movedTo[jID] = s
                        prev = s
                        # continue if sub2 joined to more
                        if joinEndTo[jID] > -1 and joinStartTo[jID] > -1:
                            # already joined so both joined if continue
                            proceed = 1

                            while proceed == 1:
                                nID = (
                                    joinEndTo[jID]
                                    if joinEndTo[jID] != prev
                                    else joinStartTo[jID]
                                )
                                if movedTo[nID] == s:
                                    closedThis = " Z "
                                    proceed = 0
                                else:
                                    sub2 = old[nID]
                                    if (
                                        nID == joinEndTo[jID]
                                        and joinStartTo[nID] == jID
                                    ) or (
                                        nID == joinStartTo[jID]
                                        and joinEndTo[nID] == jID
                                    ):
                                        pass
                                    else:
                                        rev = not rev
                                    sub2 = reverse_sub(sub2) if rev == True else sub2
                                    thisSub = join_sub(thisSub, sub2, optionJoin)
                                    movedTo[nID] = s
                                    if joinEndTo[nID] > -1 and joinStartTo[nID] > -1:
                                        prev = jID
                                        jID = nID
                                    else:
                                        proceed = 0

                    if joinStartTo[s] > -1 and closedThis == "":
                        jID = joinStartTo[s]
                        sub1 = old[jID]
                        rev = True if joinStartToEnd[s] == False else False
                        sub1 = reverse_sub(sub1) if rev == True else sub1
                        sub2 = thisSub if len(thisSub) > 0 else old[s]
                        thisSub = join_sub(sub1, sub2, optionJoin)
                        movedTo[jID] = s
                        prev = s
                        # continue if sub1 joined to more
                        if joinEndTo[jID] > -1 and joinStartTo[jID] > -1:
                            proceed = 1

                            while proceed == 1:
                                nID = (
                                    joinStartTo[jID]
                                    if joinStartTo[jID] != prev
                                    else joinEndTo[jID]
                                )
                                if movedTo[nID] == s:
                                    closedThis = " Z "
                                    proceed = 0
                                else:
                                    sub1 = old[nID]
                                    if (
                                        nID == joinEndTo[jID]
                                        and joinStartTo[nID] == jID
                                    ) or (
                                        nID == joinStartTo[jID]
                                        and joinEndTo[nID] == jID
                                    ):
                                        pass
                                    else:
                                        rev = not rev
                                    sub1 = reverse_sub(sub1) if rev == True else sub1
                                    thisSub = join_sub(sub1, thisSub, optionJoin)
                                    movedTo[nID] = s
                                    if joinEndTo[nID] > -1 and joinStartTo[nID] > -1:
                                        prev = jID
                                        jID = nID
                                    else:
                                        proceed = 0

                    # close the new subpath if start/end node is closer than maxdist
                    # (should be handled above, but is not so this was a quick fix)
                    if closedThis == " Z " and optionJoin == "1":
                        newStartEnd = [
                            0.5 * (thisSub[-1][-1][0] + thisSub[0][0][0]),
                            0.5 * (thisSub[-1][-1][1] + thisSub[0][0][1]),
                        ]
                        thisSub[0][0] = newStartEnd
                        thisSub[0][1] = newStartEnd
                        thisSub[-1][1] = newStartEnd
                        thisSub[-1][2] = newStartEnd

                    new.append(thisSub)
                    newClosed.append(closedThis)

                else:
                    new.append(old[s])
                    newClosed.append(closed[s])

        closed = newClosed

    nEmpty = new.count([])
    if nEmpty > 0:
        for i in range(nEmpty):
            idx_empty = new.index([])
            new.pop(idx_empty)
            closed = np.delete(closed, idx_empty)

    return (new, closed)


class RemoveDuplicateNodes(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--tab", default="options")
        pars.add_argument("--minlength", default="0")
        pars.add_argument("--minUse", type=inkex.Boolean, default=False)
        pars.add_argument("--maxdist", default="0")
        pars.add_argument("--joinEnd", type=inkex.Boolean, default=False)
        pars.add_argument("--maxdist2", default="0")
        pars.add_argument("--joinEndSub", type=inkex.Boolean, default=False)
        pars.add_argument("--allowReverse", type=inkex.Boolean, default=True)
        pars.add_argument("--optionJoin", default="1")

    """Remove duplicate nodes"""

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")

        minlength = float(self.options.minlength)
        maxdist = float(self.options.maxdist)
        maxdist2 = float(self.options.maxdist2)
        if self.options.minUse is False:
            minlength = 0
        if self.options.joinEnd is False:
            maxdist = -1
        if self.options.joinEndSub is False:
            maxdist2 = -1

        nFailed = 0
        nInkEffect = 0

        for id, elem in self.svg.selection.id_dict().items():

            thisIsPath = True
            if elem.get("d") is None:
                thisIsPath = False
                nFailed += 1
            if elem.get("inkscape:path-effect") is not None:
                thisIsPath = False
                nInkEffect += 1

            if thisIsPath:

                new, closed = remove_duplicate_nodes(
                    elem,
                    minlength,
                    maxdist,
                    maxdist2,
                    self.options.allowReverse,
                    self.options.optionJoin,
                )

                elem.path = CubicSuperPath(new).to_path(curves_only=True)

                # reset z to the originally closed paths
                # (z lost in cubicsuperpath)
                temppath = str(elem.path.to_absolute()).split("M ")
                temppath.pop(0)
                newPath = ""
                li = 0
                for sub in temppath:
                    newPath = newPath + "M " + temppath[li] + closed[li]
                    li += 1
                elem.path = newPath

        if nFailed > 0:
            messagebox.showwarning(
                "Warning",
                f"""{nFailed} selected elements have no path specified.
                Groups have to be ungrouped first and paths have to be
                combined with Ctrl + K to be considered for joining.
                Shape-elements and text will be ignored.""",
            )

        if nInkEffect > 0:
            messagebox.showwarning(
                "Warning",
                f"""{nInkEffect} selected elements have an
                inkscape:path-effect applied. These elements will be
                ignored to avoid confusing results. Apply Paths->Object
                to path (Shift+Ctrl+C) and retry .""",
            )


if __name__ == "__main__":
    RemoveDuplicateNodes().run()
