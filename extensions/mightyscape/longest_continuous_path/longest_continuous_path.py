#!/usr/bin/env python3
'''
Copyright (C) 2017 Romain Testuz

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St Fifth Floor, Boston, MA 02139
'''
import inkex
import sys
import math
import random
import colorsys
import os
import numpy
import timeit

import networkx as nx

MAX_CONSECUTIVE_OVERWRITE_EDGE = 3
STOP_SHORTEST_PATH_IF_SMALLER_OR_EQUAL_TO = 1
OVERWRITE_ALLOW = 0
OVERWRITE_ALLOW_SOME = 1
OVERWRITE_ALLOW_NONE = 2

"""
class Graph:
    def __init__(self):
        self.__adj = {}
        self.__data = {}

    def __str__(self):
        return str(self.__adj)

    def nodes(self):
        nodes = []
        for n in self.__adj:
            nodes.append(n)
        return nodes

    def edges(self):
        edges = []
        for n1 in self.__adj:
            for n2 in self.neighbours(n1):
                if((n2, n1) not in edges):
                    edges.append((n1, n2))
        return edges

    def node(self, n):
        if n in self.__adj:
            return self.__data[n]
        else:
            raise ValueError('Inexistant node')

    def neighbours(self, n):
        if n in self.__adj:
            return self.__adj[n]
        else:
            raise ValueError('Inexistant node')

    def outEdges(self, n):
        edges = []
        for n2 in self.neighbours(n):
            edges.append((n, n2))
        return edges

    def degree(self, n):
        if n in self.__adj:
            return len(self.__adj[n])
        else:
            raise ValueError('Inexistant node')

    def addNode(self, n, data):
        if n not in self.__adj:
            self.__adj[n] = []
            self.__data[n] = data
        else:
            raise ValueError('Node already exists')

    def removeNode(self, n):
        if n in self.__adj:
            #Remove all edges pointing to node
            for n2 in self.__adj:
                neighbours = self.__adj[n2]
                if n in neighbours:
                    neighbours.remove(n)
            del self.__adj[n]
            del self.__data[n]
        else:
            raise ValueError('Removing inexistant node')

    def addEdge(self, n1, n2):
        if(n1 in self.__adj and n2 in self.__adj):
            self.__adj[n1].append(n2)
            self.__adj[n2].append(n1)
        else:
            raise ValueError('Adding edge to inexistant node')

    def removeEdge(self, n1, n2):
        if(n1 in self.__adj and n2 in self.__adj and
        n2 in self.__adj[n1] and n1 in self.__adj[n2]):
            self.__adj[n1].remove(n2)
            self.__adj[n2].remove(n1)
        else:
            raise ValueError('Removing inexistant edge')

    def __sortedEdgesByAngle(self, previousEdge, edges):
        previousEdgeVectNormalized = numpy.array(self.node(previousEdge[1])) - numpy.array(self.node(previousEdge[0]))
        previousEdgeVectNormalized = previousEdgeVectNormalized/numpy.linalg.norm(previousEdgeVectNormalized)
        #previousEdgeVectNormalized = numpy.array((0,1))
        def angleKey(outEdge):
            edgeVectNormalized = numpy.array(self.node(outEdge[1])) - numpy.array(self.node(outEdge[0]))
            edgeVectNormalized = edgeVectNormalized/numpy.linalg.norm(edgeVectNormalized)
            return -numpy.dot(previousEdgeVectNormalized, edgeVectNormalized)

        return sorted(edges, key=angleKey)

    def dfsEdges(self):
        nodes = self.nodes()
        visitedEdges = set()
        visitedNodes = set()
        edges = {}
        dfsEdges = []

        for startNode in nodes:
            #if self.degree(startNode) != 1:
                #continue#Makes sure we don't start in the middle of a path
            stack = [startNode]
            prevEdge = None
            while stack:
                currentNode = stack[-1]
                if currentNode not in visitedNodes:
                    edges[currentNode] = self.outEdges(currentNode)
                    visitedNodes.add(currentNode)

                if edges[currentNode]:
                    if(prevEdge):
                        edges[currentNode] = self.__sortedEdgesByAngle(prevEdge, edges[currentNode])
                    edge = edges[currentNode][0]
                    if edge not in visitedEdges and (edge[1], edge[0]) not in visitedEdges:
                        visitedEdges.add(edge)
                        # Mark the traversed "to" node as to-be-explored.
                        stack.append(edge[1])
                        dfsEdges.append(edge)
                        prevEdge = edge
                    edges[currentNode].pop(0)
                else:
                    # No more edges from the current node.
                    stack.pop()
                    prevEdge = None

        return dfsEdges
"""

class LongestContinuousPath(inkex.GenerateExtension):

    def add_arguments(self, pars):
        pars.add_argument("-t", "--tolerance", type=float, default=0.1, help="the distance below which 2 nodes will be merged")
        pars.add_argument("-l", "--enableLog", type=inkex.Boolean, default=False, help="Enable logging")
        pars.add_argument("-o", "--overwriteRule", type=int, default=1, help="Options to control edge overwrite rules")
        pars.add_argument("-k", "--keepSelected", type=inkex.Boolean, default=False, help="Keep selected elements")

    def parseSVG(self):
        vertices = []
        edges = []

        objects = self.svg.selection.filter(inkex.PathElement).values()

        for node in objects:
            if node.tag == inkex.addNS('path', 'svg'):
                node.apply_transform()
                superpath = node.path.to_absolute().to_superpath()
                for subpath in superpath:
                    subpathList = list(subpath)

                    # We only work with lines, not curves, so we ignore the a and c in [a, b, c]
                    newVertices = list(map(lambda x: x[1], subpathList))
                    # self.log(newVertices)

                    newEdges = range(len(vertices), len(vertices) + len(newVertices) - 1)
                    newEdges = list(map(lambda x: (x, x + 1), newEdges))
                    # self.log(newEdges)

                    edges.extend(newEdges)
                    vertices.extend(newVertices)
            else:
                self.log("This extension only works with paths and currently doesn't support groups")

            if self.options.keepSelected is False:
                for object in objects:
                    if object.getparent() is not None:
                        #inkex.utils.debug(object.get('id'))
                        object.getparent().remove(object)

        return (vertices, edges)

    # Also computes edge weight
    def buildGraph(self, vertices, edges):
        G = nx.Graph()
        for i, v in enumerate(vertices):
            G.add_node(i, x=v[0], y=v[1])
            # self.log("N "+ str(i) + " (" + str(v[0]) + "," + str(v[1]) + ")")
        for e in edges:
            dist = self.dist(G.nodes[e[0]], G.nodes[e[1]])
            G.add_edge(e[0], e[1], weight=dist)
            # self.log("E "+str(e[0]) + " " + str(e[1]))
        return G

    @staticmethod
    def dist(a, b):
        return math.sqrt((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2)

    def log(self, message):
        if self.options.enableLog:
            inkex.utils.debug(message)

    def mergeWithTolerance(self, G, tolerance):
        mergeTo = {}
        for ni in G.nodes():
            for nj in G.nodes():
                if nj <= ni:
                    continue
                # self.log("Test " + str(ni) + " with " + str(nj))
                dist_ij = self.dist(G.nodes[ni], G.nodes[nj])
                if (dist_ij < tolerance) and (nj not in mergeTo) and (ni not in mergeTo):
                    # self.log("Merge " + str(nj) + " with " + str(ni) + " (dist=" + str(dist_ij) + ")")
                    mergeTo[nj] = ni

        for n in mergeTo:
            newEdges = []
            for neigh_n in G[n]:
                newEdge = None
                if neigh_n in mergeTo:
                    newEdge = (mergeTo[n], mergeTo[neigh_n])
                else:
                    newEdge = (mergeTo[n], neigh_n)

                if newEdge[0] != newEdge[1]:  # Don't add self-loops
                    newEdges.append(newEdge)

            for e in newEdges:
                G.add_edge(*e)
                # self.log("Added edge: "+str(e[0]) + " " + str(e[1]))
            G.remove_node(n)
            # self.log("Removed node: " + str(n))

    @staticmethod
    def rgbToHex(rgb):
        return '#%02x%02x%02x' % rgb

    # Color should be in hex format ("#RRGGBB"), if not specified a random color will be generated
    def addPathToInkscape(self, path, parent, color):
        elem = parent.add(inkex.PathElement())
        elem.style = {'stroke': color, 'stroke-width': 2, 'fill': 'none'}
        elem.path = inkex.Path(path)

    def removeSomeEdges(self, G, edges):
        visitedEdges = set()

        # Contains a list of [start, end] where start is the start index of a duplicate path
        # and end is the end index of the duplicate path
        edgeRangeToRemove = []
        isPrevEdgeDuplicate = False
        duplicatePathStartIndex = -1
        for i, e in enumerate(edges):
            isEdgeDuplicate = e in visitedEdges or (e[1], e[0]) in visitedEdges

            if isEdgeDuplicate:
                if duplicatePathStartIndex == -1:
                    duplicatePathStartIndex = i
            else:
                if duplicatePathStartIndex >= 0:
                    edgeRangeToRemove.append((duplicatePathStartIndex, i - 1))
                    duplicatePathStartIndex = -1

                visitedEdges.add(e)

            if isEdgeDuplicate and i == len(edges) - 1:
                edgeRangeToRemove.append((duplicatePathStartIndex, i))

        if self.options.overwriteRule == OVERWRITE_ALLOW:
            # The last duplicate path can always be removed
            edgeRangeToRemove = [edgeRangeToRemove[-1]] if edgeRangeToRemove else []
        elif self.options.overwriteRule == OVERWRITE_ALLOW_SOME:  # Allow overwrite except for long paths
            edgeRangeToRemove = [x for x in edgeRangeToRemove if x[1] - x[0] > MAX_CONSECUTIVE_OVERWRITE_EDGE]

        indicesToRemove = set()
        for start, end in edgeRangeToRemove:
            indicesToRemove.update(range(start, end + 1))

        cleanedEdges = [e for i, e in enumerate(edges) if i not in indicesToRemove]

        return cleanedEdges

    # Find the first break and rotate the edges to align to this break
    # this allows to avoid an extra path
    # Return the rotated edges
    def shiftEdgesToBreak(self, edges):
        if not edges:
            return edges
        # Only useful if the last edge connects to the first
        if edges[0][0] != edges[-1][1]:
            return edges

        for i, e in enumerate(edges):
            if i == 0:
                continue
            if edges[i - 1][1] != e[0]:
                return edges[i:] + edges[:i]

        return edges

    def edgesToPaths(self, edges):
        paths = []
        path = []

        for i, e in enumerate(edges):
            if e[0] == -1:  # Start with extra node, ignore it
                assert not path
            elif e[1] == -1:  # End with extra node, ignore it
                if path:
                    paths.append(path)
                path = []

            else:
                # Path ends either at the last edge or when the next edge starts somewhere else
                endPath = (i == len(edges) - 1 or e[1] != edges[i + 1][0])

                if not path:
                    path.append(e[0])
                    path.append(e[1])
                else:
                    path.append(e[1])

                if endPath:
                    paths.append(path)
                    path = []

        if self.options.overwriteRule == OVERWRITE_ALLOW:
            assert len(paths) == 1

        # paths.sort(key=len, reverse=True)
        return paths

    def pathsToSVG(self, G, paths):
        svgPaths = []
        for path in paths:
            svgPath = []
            for nodeIndex, n in enumerate(path):
                command = None
                if nodeIndex == 0:
                    command = 'M'
                else:
                    command = 'L'
                svgPath.append([command, (G.nodes[n]['x'], G.nodes[n]['y'])])
            svgPaths.append(svgPath)

        # Create a group
        group = inkex.Group.new("OptimizedPaths")

        for pathIndex, svgPath in enumerate(svgPaths):
            # Generate a different color for every path
            color = colorsys.hsv_to_rgb(pathIndex / float(len(svgPaths)), 1.0, 1.0)
            color = tuple(int(x * 255) for x in color)
            color = self.rgbToHex(color)
            self.addPathToInkscape(svgPath, group, color)
        return group

    # Computes the physical path length (it ignores the edge weight)
    def pathLength(self, G, path):
        length = 0.0
        for i, n in enumerate(path):
            if i > 0:
                length += self.dist(G.nodes[path[i - 1]], G.nodes[path[i]])
        return length

    # Eulerization algorithm:
    # 1. Find all vertices with odd valence.
    # 2. Pair them up with their nearest neighbor.
    # 3. Find the shortest path between each pair.
    # 4. Duplicate these edges.
    # Doesn't modify input graph
    def makeEulerianGraph(self, G):
        oddNodes = []
        for n in G.nodes:
            if G.degree(n) % 2 != 0:
                oddNodes.append(n)
        # self.log("Number of nodes with odd degree: " + str(len(oddNodes)))

        if len(oddNodes) == 0:
            return G

        # self.computeEdgeWeights(G)

        pathsToDuplicate = []

        while (oddNodes):
            n1 = oddNodes[0]

            shortestPaths = []
            # For every other node, find the shortest path to the closest node
            for n2 in oddNodes:
                if n2 != n1:
                    # self.log(str(n1) + " " + str(n2))
                    shortestPath = nx.astar_path(G, n1, n2,
                                                 lambda n1, n2: self.dist(G.nodes[n1], G.nodes[n2]), 'weight')
                    # self.log(str(len(shortestPath)))
                    shortestPaths.append(shortestPath)
                    if len(shortestPath) <= STOP_SHORTEST_PATH_IF_SMALLER_OR_EQUAL_TO:
                        # If we find a path of length <= STOP_SHORTEST_PATH_IF_SMALLER_OR_EQUAL_TO,
                        # we assume it's good enough (to speed up calculation)
                        break
            # For all the shortest paths from n1, we take the shortest one and therefore get the closest odd node
            shortestShortestPath = min(shortestPaths, key=lambda x: self.pathLength(G, x))
            closestNode = shortestShortestPath[-1]
            pathsToDuplicate.append(shortestShortestPath)
            oddNodes.pop(0)
            oddNodes.remove(closestNode)

        numberOfDuplicatedEdges = 0
        lenghtOfDuplicatedEdges = 0.0

        for path in pathsToDuplicate:
            numberOfDuplicatedEdges += len(path) - 1
            pathLength = self.pathLength(G, path)
            # self.log("Path length: " + str(pathLength))
            lenghtOfDuplicatedEdges += pathLength
        # self.log("Number of duplicated edges: " + str(numberOfDuplicatedEdges))
        # self.log("Length of duplicated edges: " + str(lenghtOfDuplicatedEdges))

        # Convert the graph to a MultiGraph to allow parallel edges
        G2 = nx.MultiGraph(G)
        for path in pathsToDuplicate:
            nx.add_path(G2, path)

        return G2

    # Doesn't modify input graph
    # faster than makeEulerianGraph but creates an extra node
    def makeEulerianGraphExtraNode(self, G):
        oddNodes = []
        for n in G.nodes:
            if G.degree(n) % 2 != 0:
                oddNodes.append(n)
        if len(oddNodes) == 0:
            return G

        G2 = nx.Graph(G)
        G2.add_node(-1, x=0, y=0)
        for n in oddNodes:
            G2.add_edge(n, -1)

        return G2

    """def computeEdgeWeights(self, G):
        for n1, n2 in G.edges():
            dist = self.dist(G.nodes[n1], G.nodes[n2])
            G.add_edge(n1, n2, weight=dist)"""

    def _getNodePosition(self, G, n):
        return (G.nodes[n]['x'], G.nodes[n]['y'])

    def _getBestEdge(self, G, previousEdge, edges):
        previousEdgeVectNormalized = numpy.array(self._getNodePosition(G, previousEdge[1])) - numpy.array(
            self._getNodePosition(G, previousEdge[0]))
        # self.log(str(numpy.linalg.norm(previousEdgeVectNormalized)) + " " + str(previousEdge[1]) + " " + str(previousEdge[0]))
        previousEdgeVectNormalized = previousEdgeVectNormalized / numpy.linalg.norm(previousEdgeVectNormalized)

        # previousEdgeVectNormalized = numpy.array((0,1))
        def angleKey(outEdge):
            edgeVectNormalized = numpy.array(self._getNodePosition(G, outEdge[1])) - numpy.array(
                self._getNodePosition(G, outEdge[0]))
            edgeVectNormalized = edgeVectNormalized / numpy.linalg.norm(edgeVectNormalized)
            return numpy.dot(previousEdgeVectNormalized, edgeVectNormalized)

        return max(edges, key=angleKey)

    """def eulerian_circuit(self, G):
        g = G.__class__(G)#G.copy()
        v = next(g.nodes())

        degree = g.degree
        edges = g.edges

        circuit = []
        vertex_stack = [v]
        last_vertex = None
        while vertex_stack:
            current_vertex = vertex_stack[-1]
            if degree(current_vertex) == 0:
                if last_vertex is not None:
                    circuit.append((last_vertex, current_vertex))
                    self.log(str(last_vertex) + " " + str(current_vertex))
                last_vertex = current_vertex
                vertex_stack.pop()
            else:
                if circuit:
                    arbitrary_edge = self._getBestEdge(g, circuit[-1], edges(current_vertex))
                else:#For the first iteration we arbitrarily take the first edge
                    arbitrary_edge = next(edges(current_vertex))
                #self.log(str(arbitrary_edge) + "::" + str(edges[current_vertex]))

                #self.log(str(edges[current_vertex]))
                #self.log(" ")

                vertex_stack.append(arbitrary_edge[1])
                g.remove_edge(*arbitrary_edge)

        return circuit"""

    # Walk as straight as possible from node until stuck
    def walk(self, node, G):
        n = node
        e = None
        path = [n]

        while G.degree[n]:  # Continue until there no unvisited edges from n
            if e:
                e = self._getBestEdge(G, e, G.edges(n))
            else:  # For the first iteration we arbitrarily take the first edge
                e = (n, next(iter(G[n])))
            n = e[1]
            G.remove_edge(*e)
            path.append(n)

        return path

    def eulerian_circuit_hierholzer(self, G):
        g = G.copy()
        v = next(iter(g.nodes))  # First vertex, arbitrary

        cycle = self.walk(v, g)
        assert cycle[0] == cycle[-1]
        notvisited = set(cycle)

        while len(notvisited) != 0:
            v = notvisited.pop()
            if g.degree(v) != 0:
                i = cycle.index(v)
                sub = self.walk(v, g)
                assert sub[0] == sub[-1]
                cycle = cycle[:i] + sub[:-1] + cycle[i:]
                notvisited.update(sub)

        cycleEdges = []
        prevNode = None
        for n in cycle:
            if prevNode != None:
                cycleEdges.append((prevNode, n))
            prevNode = n
        return cycleEdges

    def generate(self):
        self.log("NetworkX version: " + nx.__version__)
        if int(nx.__version__[0]) < 2:
            inkex.utils.debug("NetworkX version is: {} but should be >= 2.0.".format(nx.__version__))
            return
        self.log("Python version: " + sys.version)

        totalTimerStart = timeit.default_timer()
        (vertices, edges) = self.parseSVG()
        G = self.buildGraph(vertices, edges)

        timerStart = timeit.default_timer()
        self.mergeWithTolerance(G, self.options.tolerance)
        timerStop = timeit.default_timer()
        mergeDuration = timerStop - timerStart
        initialEdgeCount = nx.number_of_edges(G)
        finalEdgeCount = 0

        """for e in G.edges():
            self.log("E "+str(e[0]) + " " + str(e[1]))
        for n in G.nodes():
            self.log("Degree of "+str(n) + ": " + str(G.degree(n)))"""
        # Split disjoint graphs
        connectedGraphs = [G.subgraph(c).copy() for c in nx.connected_components(G)]
        self.log("Number of disconnected graphs: " + str(len(connectedGraphs)))

        paths = []
        makeEulerianDuration = 0
        for connectedGraph in connectedGraphs:
            timerStart = timeit.default_timer()
            if self.options.overwriteRule == OVERWRITE_ALLOW_NONE:
                connectedGraph = self.makeEulerianGraphExtraNode(connectedGraph)
                #connectedGraph = nx.eulerize(connectedGraph)
            else:
                connectedGraph = self.makeEulerianGraph(connectedGraph)
                #connectedGraph = nx.eulerize(connectedGraph)
            timerStop = timeit.default_timer()
            makeEulerianDuration += timerStop - timerStart
            # connectedGraph is now likely a multigraph

            finalEdgeCount = finalEdgeCount + nx.number_of_edges(connectedGraph)
            #pathEdges = list(nx.eulerian_path(connectedGraph))
            pathEdges = self.eulerian_circuit_hierholzer(connectedGraph)
            pathEdges = self.removeSomeEdges(connectedGraph, pathEdges)
            pathEdges = self.shiftEdgesToBreak(pathEdges)

            paths.extend(self.edgesToPaths(pathEdges))

        self.log("Path number: " + str(len(paths)))
        self.log("Total path length: {:.2f}".format(sum(self.pathLength(G, x) for x in paths)))
        self.log("Number of duplicated edges: {:d}".format(finalEdgeCount-initialEdgeCount))

        group = self.pathsToSVG(G, paths)
        totalTimerStop = timeit.default_timer()
        totalDuration = totalTimerStop - totalTimerStart
        self.log("Merge duration: {:.0f} sec ({:.1f} min)".format(mergeDuration, mergeDuration / 60))
        self.log("Make Eulerian duration: {:.0f} sec ({:.1f} min)".format(makeEulerianDuration, makeEulerianDuration / 60))
        self.log("Total duration: {:.0f} sec ({:.1f} min)".format(totalDuration, totalDuration / 60))
        return group

if __name__ == '__main__':
    LongestContinuousPath().run()