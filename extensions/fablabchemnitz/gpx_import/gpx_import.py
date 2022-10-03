#!/usr/bin/env python3

#   Copyright (c) 2012-2018 Tobias Leupold <tobias.leupold@gmx.de>
#
#   gpx2svg - Convert GPX formatted geodata to Scalable Vector Graphics (SVG)
#
#   This program is free software; you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by the Free
#   Software Foundation in version 2 of the License.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#   or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#   for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
#   modified by monomono@disroot.org at 2019-08-05 for use on inkscape extension,
#    3to2 python converter and adjust parser_options for inkscape compatibility.

from __future__ import division
from __future__ import absolute_import
from io import open
__version__ = u'@VERSION@'

import argparse
import sys
import math
from xml.dom.minidom import parse as parseXml
from os.path import abspath

def parseGpx(gpxFile):
    u"""Get the latitude and longitude data of all track segments in a GPX file"""

    if gpxFile == u'/dev/stdin':
        gpxFile = sys.stdin

    # Get the XML information
    try:
        gpx = parseXml(gpxFile)
    except IOError as error:
        print (sys.stderr, u'Error while reading file: {}. Terminating.'.format(error))
        sys.exit(1)
    except:
        print (sys.stderr, u'Error while parsing XML data:')
        print (sys.stderr, sys.exc_info())
        print (sys.stderr, u'Terminating.')
        sys.exit(1)

    # Iterate over all tracks, track segments and points
    gpsData = []
    for track in gpx.getElementsByTagName(u'trk'):
        for trackseg in track.getElementsByTagName(u'trkseg'):
            trackSegData = []
            for point in trackseg.getElementsByTagName(u'trkpt'):
                trackSegData.append(
                    (float(point.attributes[u'lon'].value), float(point.attributes[u'lat'].value))
                )
            # Leave out empty segments
            if(trackSegData != []):
                gpsData.append(trackSegData)

    return gpsData

def calcProjection(gpsData):
    u"""Calculate a plane projection for a GPS dataset"""

    projectedData = []
    for segment in gpsData:
        projectedSegment = []
        for coord in segment:
            # At the moment, we only have the Mercator projection
            projectedSegment.append(mercatorProjection(coord))
        projectedData.append(projectedSegment)

    return projectedData

def mercatorProjection(coord):
    u"""Calculate the Mercator projection of a coordinate pair"""

    # Assuming we're on earth, we have (according to GRS 80):
    r = 6378137.0

    # As long as meridian = 0 and can't be changed, we don't need:
    #    meridian = meridian * math.pi / 180.0
    #    x = r * ((coord[0] * math.pi / 180.0) - meridian)

    # Instead, we use this simplified version:
    x = r * coord[0] * math.pi / 180.0
    y = r * math.log(math.tan((math.pi / 4.0) + ((coord[1] * math.pi / 180.0) / 2.0)))
    return x, y

def moveProjectedData(gpsData):
    u"""Move a dataset to 0,0 and return it with the resulting width and height"""

    # Find the minimum and maximum x and y coordinates
    minX = maxX = gpsData[0][0][0]
    minY = maxY = gpsData[0][0][1]
    for segment in gpsData:
        for coord in segment:
            if coord[0] < minX:
                minX = coord[0]
            if coord[0] > maxX:
                maxX = coord[0]
            if coord[1] < minY:
                minY = coord[1]
            if coord[1] > maxY:
                maxY = coord[1]

    # Move the GPS data to 0,0
    movedGpsData = []
    for segment in gpsData:
        movedSegment = []
        for coord in segment:
            movedSegment.append((coord[0] - minX, coord[1] - minY))
        movedGpsData.append(movedSegment)

    # Return the moved data and it's width and height
    return movedGpsData, maxX - minX, maxY - minY

def searchCircularSegments(gpsData):
    u"""Splits a GPS dataset to tracks that are circular and other tracks"""

    circularSegments = []
    straightSegments = []

    for segment in gpsData:
        if segment[0] == segment[len(segment) - 1]:
            circularSegments.append(segment)
        else:
            straightSegments.append(segment)

    return circularSegments, straightSegments

def combineSegmentPairs(gpsData):
    u"""Combine segment pairs to one bigger segment"""

    combinedData = []

    # Walk through the GPS data and search for segment pairs
    # that end with the starting point of another track
    while len(gpsData) > 0:
        # Get one segment from the source GPS data
        firstTrackData = gpsData.pop()
        foundMatch = False

        # Try to find a matching segment
        for i in xrange(len(gpsData)):
            if firstTrackData[len(firstTrackData) - 1] == gpsData[i][0]:
                # There is a matching segment, so break here
                foundMatch = True
                break

        if foundMatch == True:
            # We found a pair of segments with one shared point, so pop the data of the second
            # segment from the source GPS data and create a new segment containing all data, but
            # without the overlapping point
            firstTrackData.pop()
            combinedData.append(firstTrackData + gpsData[i])
            gpsData.pop(i)
        else:
            # No segment with a shared point was found, so just append the data to the output
            combinedData.append(firstTrackData)

    return searchCircularSegments(combinedData)

def combineSegments(gpsData):
    u"""Combine all segments of a GPS dataset that can be combined"""

    # Search for circular segments. We can't combine them with any other segment.
    circularSegments, remainingSegments = searchCircularSegments(gpsData)

    # Search for segments that can be combined
    while True:
        # Look how many tracks we have now
        segmentsBefore = len(remainingSegments)

        # Search for segments that can be combined
        newCircularSegments, remainingSegments = combineSegmentPairs(remainingSegments)

        # Add newly found circular segments to processedSegments -- they can't be used anymore
        circularSegments = circularSegments + newCircularSegments

        if segmentsBefore == len(remainingSegments):
            # combineSegmentPairs() did not reduce the number of tracks anymore,
            # so we can't combine more tracks and can stop here
            break

    return circularSegments + remainingSegments

def chronologyJoinSegments(gpsData):
    u"""Join all segments to a big one in the order defined by the GPX file."""
    joinedSegment = []
    for segment in gpsData:
        joinedSegment += segment
    return [joinedSegment]

def scaleCoords(coord, height, scale):
    u"""Return a scaled pair of coordinates"""
    return coord[0] * scale, (coord[1] * -1 + height) * scale

def generateScaledSegment(segment, height, scale):
    u"""Create the coordinate part of an SVG path string from a GPS data segment"""
    for coord in segment:
        yield scaleCoords(coord, height, scale)

def writeSvgData(gpsData, width, height, maxPixels, dropSinglePoints, outfile):
    u"""Output the SVG data -- quick 'n' dirty, without messing around with dom stuff ;-)"""

    # Calculate the scale factor we need to fit the requested maximal output size
    if width <= maxPixels and height <= maxPixels:
        scale = 1
    elif width > height:
        scale = maxPixels / width
    else:
        scale = maxPixels / height

    # Open the requested output file or map to /dev/stdout
    if outfile != u'/dev/stdout':
        try:
            fp = open(outfile, u'w')
        except IOError as error:
            print (sys.stderr, u"Can't open output file: {}. Terminating.".format(error))
            sys.exit(1)
    else:
        fp = sys.stdout

    # Header data
    fp.write( u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    fp.write((u'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
              u'"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'))
    fp.write( u'<!-- Created with gpx2svg {} -->\n'.format(__version__))
    fp.write((u'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
              u'width="{}px" height="{}px">\n').format(width * scale, height * scale))

    # Process all track segments and generate ids and path drawing commands for them

    # First, we split the data to circular and straight segments
    circularSegments, straightSegments = searchCircularSegments(gpsData)
    realCircularSegments = []
    singlePoints = []
    for segment in circularSegments:
        # We can leave out the last point, because it's equal to the first one
        segment.pop()
        if len(segment) == 1:
            # It's a single point
            if dropSinglePoints == False:
                # We want to keep single points, so add it to singlePoints
                singlePoints.append(segment)
        else:
            realCircularSegments.append(segment)

    circularSegments = realCircularSegments

    # Draw single points if requested
    if len(singlePoints) > 0:
        fp.write(u'<g>\n')
        for segment in singlePoints:
            x, y = scaleCoords(segment[0], height, scale)
            fp.write(
                u'<circle cx="{}" cy="{}" r="0.5" style="stroke:none;fill:black"/>\n'.format(x, y)
            )
        fp.write(u'</g>\n')

    # Draw all circular segments
    if len(circularSegments) > 0:
        fp.write(u'<g>\n')
        for segment in circularSegments:
            fp.write(u'<path d="M')
            for x, y in generateScaledSegment(segment, height, scale):
                fp.write(u' {} {}'.format(x, y))
            fp.write(u' Z" style="fill:none;stroke:black"/>\n')
        fp.write(u'</g>\n')

    # Draw all un-closed paths
    if len(straightSegments) > 0:
        fp.write(u'<g>\n')
        for segment in straightSegments:
            fp.write(u'<path d="M')
            for x, y in generateScaledSegment(segment, height, scale):
                fp.write(u' {} {}'.format(x, y))
            fp.write(u'" style="fill:none;stroke:black"/>\n')
        fp.write(u'</g>\n')

    # Close the XML
    fp.write(u'</svg>\n')

    # Close the file if necessary
    if fp != sys.stdout:
        fp.close()

def main():
    # Setup the command line argument parser
    cmdArgParser = argparse.ArgumentParser(
        description = u'Convert GPX formatted geodata to Scalable Vector Graphics (SVG)',
        epilog = u'gpx2svg {} - http://nasauber.de/opensource/gpx2svg/'.format(__version__)
    )
    cmdArgParser.add_argument(
        u'i', metavar = u'FILE', nargs = u'?', default = u'/dev/stdin',
        help = u'GPX input file (default: read from STDIN)'
    )
    cmdArgParser.add_argument(
        u'--o', metavar = u'FILE', nargs = u'?', default = u'/dev/stdout',
        help = u'SVG output file (default: write to STDOUT)'
    )
    cmdArgParser.add_argument(
        u'--m', metavar = u'PIXELS', nargs = u'?', type = int, default = 3000,
        help = u'Maximum width or height of the SVG output in pixels (default: 3000)'
    )
    cmdArgParser.add_argument(
        u'--d',
        help = u'Drop single points (default: draw a circle with 1px diameter)'
    )
    cmdArgParser.add_argument(
        u'--r',
        help = (u'"Raw" conversion: Create one SVG path per track segment, don\'t try to combine '
                u'paths that end with the starting point of another path')
    )
    cmdArgParser.add_argument(
        u'--j',
        help = (u'Join all segments to a big one in the order of the GPX file. This can create an '
                u'un-scattered path if the default combining algorithm does not work because there '
                u'are no matching points across segments (implies -r)')
    )
    cmdArgParser.add_argument(
        u'--tab',
        help = (u'inkscape option')
    )
    

    # Get the given arguments
    cmdArgs = cmdArgParser.parse_args()

    # Map "-" to STDIN or STDOUT
    if cmdArgs.i == u'-':
        cmdArgs.i = u'/dev/stdin'
    if cmdArgs.o == u'-':
        cmdArgs.o = u'/dev/stdout'

    # Check if a given input or output file name is a relative representation of STDIN or STDOUT
    if cmdArgs.i != u'/dev/stdin':
        if abspath(cmdArgs.i) == u'/dev/stdin':
            cmdArgs.i = u'/dev/stdin'
    if cmdArgs.o != u'/dev/stdout':
        if abspath(cmdArgs.o) == u'/dev/stdout':
            cmdArgs.o = u'/dev/stdout'

    # Get the latitude and longitude data from the given GPX file or STDIN
    gpsData = parseGpx(cmdArgs.i)

    # Check if we actually _have_ data
    if gpsData == []:
        print (sys.stderr, u'No data to convert. Terminating.')
        sys.exit(1)

    # Join all segments if requested by "-j"
    if bool(cmdArgs.j):
        gpsData = chronologyJoinSegments(gpsData)

    # Try to combine all track segments that can be combined if not requested otherwise
    # Don't execute if all segments are already joined with "-j"
    if not bool(cmdArgs.r) and not bool(cmdArgs.j):
        gpsData = combineSegments(gpsData)

    # Calculate a plane projection for a GPS dataset
    # At the moment, we only have the Mercator projection
    gpsData = calcProjection(gpsData)

    # Move the projected data to the 0,0 origin of a cartesial coordinate system
    # and get the raw width and height of the resulting vector data
    gpsData, width, height = moveProjectedData(gpsData)

    # Write the resulting SVG data to the requested output file or STDOUT
    writeSvgData(gpsData, width, height, cmdArgs.m, bool(cmdArgs.d), cmdArgs.o)

if __name__ == u'__main__':
    main()
