#!/usr/bin/env python3
import math
import inkex
from inkex import Transform, TextElement, Tspan, Color, Circle, PathElement, CubicSuperPath
import os
import random
import numpy as np
import openmesh as om
import networkx as nx
from lxml import etree
import copy

"""
Extension for InkScape 1.0

Paperfold is another flattener for triangle mesh files, heavily based on paperfoldmodels by Felix Scholz aka felixfeliz.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.09.2020
Last patch: 10.05.2021
License: GNU GPL v3

To run this you need to install OpenMesh with python pip. 

The algorithm of paperfoldmodels consists of three steps:
  - Find a minimum spanning tree of the dual graph of the mesh.
  - Unfold the dual graph.
  - Remove self-intersections by adding additional cuts along edges.
  
Reference: The code is mostly based on the algorithm presented in a by Straub and Prautzsch (https://geom.ivd.kit.edu/downloads/proj-paper-models_cut_out_sheets.pdf).

Module licenses
- paperfoldmodels (https://github.com/felixfeliz/paperfoldmodels) - MIT License

possible import file types -> https://www.graphics.rwth-aachen.de/media/openmesh_static/Documentations/OpenMesh-8.0-Documentation/a04096.html

todo:
- option to render all triangles in a detached way (overlapping lines/independent) + merge coplanar adjacent triangles to polygons
- write tab and slot generator (like joinery/polyhedra extension)
- fstl preview
- fix line: dualGraph.add_edge(face1.idx(), face2.idx(), idx=edge.idx(), weight=edgeweight) # #might fail without throwing any error (silent aborts) ...
- option to set fill color per face
- add some way to merge coplanar triangles (tri-faces) to polygons and keep those polygons (facets) intact. At the moment facets are getting destroyed. Not good for some papercrafts
"""

class Paperfold(inkex.EffectExtension):

    angleRangeCalculated = False #set to true after first calculation iteration (needed globally)
    minAngle = 0
    minAngle = 0
    angleRange = 0

    def getElementChildren(self, element, elements = None):
        if elements == None:
            elements = []
        if element.tag != inkex.addNS('g','svg'):
                elements.append(element)
        for child in element.getchildren():
            self.getElementChildren(child, elements)
        return elements

    # Compute the third point of a triangle when two points and all edge lengths are given
    def getThirdPoint(self, v0, v1, l01, l12, l20):
        v2rotx = (l01 ** 2 + l20 ** 2 - l12 ** 2) / (2 * l01)
        val = (l01 + l20 + l12) * (l01 + l20 - l12) * (l01 - l20 + l12) * (-l01 + l20 + l12)
        v2roty0 = np.sqrt(abs(val)) / (2 * l01)
    
        v2roty1 = - v2roty0
    
        theta = np.arctan2(v1[1] - v0[1], v1[0] - v0[0])
    
        v2trans0 = np.array(
            [v2rotx * np.cos(theta) - v2roty0 * np.sin(theta), v2rotx * np.sin(theta) + v2roty0 * np.cos(theta), 0])
        v2trans1 = np.array(
            [v2rotx * np.cos(theta) - v2roty1 * np.sin(theta), v2rotx * np.sin(theta) + v2roty1 * np.cos(theta), 0])
        return [v2trans0 + v0, v2trans1 + v0]
    
    
    # Check if two lines intersect


    def lineIntersection(self, v1, v2, v3, v4, epsilon):
        d = (v4[1] - v3[1]) * (v2[0] - v1[0]) - (v4[0] - v3[0]) * (v2[1] - v1[1])
        u = (v4[0] - v3[0]) * (v1[1] - v3[1]) - (v4[1] - v3[1]) * (v1[0] - v3[0])
        v = (v2[0] - v1[0]) * (v1[1] - v3[1]) - (v2[1] - v1[1]) * (v1[0] - v3[0])
        if d < 0:
            u, v, d = -u, -v, -d
        return ((0 + epsilon) <= u <= (d - epsilon)) and ((0 + epsilon) <= v <= (d - epsilon))
    
    # Check if a point lies inside a triangle


    def pointInTriangle(self, A, B, C, P, epsilon):
        v0 = [C[0] - A[0], C[1] - A[1]]
        v1 = [B[0] - A[0], B[1] - A[1]]
        v2 = [P[0] - A[0], P[1] - A[1]]
        cross = lambda u, v: u[0] * v[1] - u[1] * v[0]
        u = cross(v2, v0)
        v = cross(v1, v2)
        d = cross(v1, v0)
        if d < 0:
            u, v, d = -u, -v, -d
        return u >= (0 + epsilon) and v >= (0 + epsilon) and (u + v) <= (d - epsilon)
    
    
    # Check if two triangles intersect


    def triangleIntersection(self, t1, t2, epsilon):
        if self.lineIntersection(t1[0], t1[1], t2[0], t2[1], epsilon): return True
        if self.lineIntersection(t1[0], t1[1], t2[0], t2[2], epsilon): return True
        if self.lineIntersection(t1[0], t1[1], t2[1], t2[2], epsilon): return True
        if self.lineIntersection(t1[0], t1[2], t2[0], t2[1], epsilon): return True
        if self.lineIntersection(t1[0], t1[2], t2[0], t2[2], epsilon): return True
        if self.lineIntersection(t1[0], t1[2], t2[1], t2[2], epsilon): return True
        if self.lineIntersection(t1[1], t1[2], t2[0], t2[1], epsilon): return True
        if self.lineIntersection(t1[1], t1[2], t2[0], t2[2], epsilon): return True
        if self.lineIntersection(t1[1], t1[2], t2[1], t2[2], epsilon): return True
        inTri = True
        inTri = inTri and self.pointInTriangle(t1[0], t1[1], t1[2], t2[0], epsilon)
        inTri = inTri and self.pointInTriangle(t1[0], t1[1], t1[2], t2[1], epsilon)
        inTri = inTri and self.pointInTriangle(t1[0], t1[1], t1[2], t2[2], epsilon)
        if inTri == True: return True
        inTri = True
        inTri = inTri and self.pointInTriangle(t2[0], t2[1], t2[2], t1[0], epsilon)
        inTri = inTri and self.pointInTriangle(t2[0], t2[1], t2[2], t1[1], epsilon)
        inTri = inTri and self.pointInTriangle(t2[0], t2[1], t2[2], t1[2], epsilon)
        if inTri == True: return True
        return False
    
    
    # Functions for visualisation and output


    def addVisualisationData(self, mesh, unfoldedMesh, originalHalfedges, unfoldedHalfedges, glueNumber, dihedralAngles):
        for i in range(3):
            dihedralAngles[unfoldedMesh.edge_handle(unfoldedHalfedges[i]).idx()] = round(math.degrees(mesh.calc_dihedral_angle(originalHalfedges[i])), self.options.roundingDigits)
            # Information, which edges belong together
            glueNumber[unfoldedMesh.edge_handle(unfoldedHalfedges[i]).idx()] = mesh.edge_handle(originalHalfedges[i]).idx()
    
     # Function that unwinds a spanning tree
    def unfoldSpanningTree(self, mesh, spanningTree): 
        try:
            unfoldedMesh = om.TriMesh()  # the unfolded mesh

            numFaces = mesh.n_faces()
            sizeTree = spanningTree.number_of_edges()
            numUnfoldedEdges = 3 * numFaces - sizeTree
 
            isFoldingEdge = np.zeros(numUnfoldedEdges, dtype=bool)  # Indicates whether an edge is folded or cut
            glueNumber = np.empty(numUnfoldedEdges, dtype=int)  # Saves with which edge is glued together
            dihedralAngles = np.empty(numUnfoldedEdges, dtype=float)  # Valley folding or mountain folding
            connections = np.empty(numFaces, dtype=int)  # Saves which original triangle belongs to the unrolled one

            numFaces = mesh.n_faces()
            sizeTree = spanningTree.number_of_edges()
            numUnfoldedEdges = 3 * numFaces - sizeTree
    
            # Select the first triangle as desired
            startingNode = list(spanningTree.nodes())[0]
            startingTriangle = mesh.face_handle(startingNode)
        
            # We unwind the first triangle
        
            # All half edges of the first triangle
            firstHalfEdge = mesh.halfedge_handle(startingTriangle)
            secondHalfEdge = mesh.next_halfedge_handle(firstHalfEdge)
            thirdHalfEdge = mesh.next_halfedge_handle(secondHalfEdge)
            originalHalfEdges = [firstHalfEdge, secondHalfEdge, thirdHalfEdge]
        
            # Calculate the lengths of the edges, this will determine the shape of the triangle (congruence)
            edgelengths = [mesh.calc_edge_length(firstHalfEdge), mesh.calc_edge_length(secondHalfEdge),
                           mesh.calc_edge_length(thirdHalfEdge)]
        
            # The first two points
            firstUnfoldedPoint = np.array([0, 0, 0])
            secondUnfoldedPoint = np.array([edgelengths[0], 0, 0])
        
            # We calculate the third point of the triangle from the first two. There are two possibilities
            [thirdUnfolded0, thirdUnfolded1] = self.getThirdPoint(firstUnfoldedPoint, secondUnfoldedPoint, edgelengths[0],
                                                             edgelengths[1],
                                                             edgelengths[2])
            if thirdUnfolded0[1] > 0:
                thirdUnfoldedPoint = thirdUnfolded0
            else:
                thirdUnfoldePoint = thirdUnfolded1
        
            # Add the new corners to the unwound net
            firstUnfoldedVertex = unfoldedMesh.add_vertex(secondUnfoldedPoint)
            secondUnfoldedVertex = unfoldedMesh.add_vertex(thirdUnfoldedPoint)
            thirdUnfoldedVertex = unfoldedMesh.add_vertex(firstUnfoldedPoint)
        
            #firstUnfoldedVertex = unfoldedMesh.add_vertex(firstUnfoldedPoint)
            #secondUnfoldedVertex = unfoldedMesh.add_vertex(secondUnfoldedPoint)
            #thirdUnfoldedVertex = unfoldedMesh.add_vertex(thirdUnfoldedPoint)
        
            # Create the page
            unfoldedFace = unfoldedMesh.add_face(firstUnfoldedVertex, secondUnfoldedVertex, thirdUnfoldedVertex)
        
            # Memory properties of the surface and edges
            # The half edges in unrolled mesh
            firstUnfoldedHalfEdge = unfoldedMesh.opposite_halfedge_handle(unfoldedMesh.halfedge_handle(firstUnfoldedVertex))
            secondUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(firstUnfoldedHalfEdge)
            thirdUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(secondUnfoldedHalfEdge)
        
            unfoldedHalfEdges = [firstUnfoldedHalfEdge, secondUnfoldedHalfEdge, thirdUnfoldedHalfEdge]
        
            # Associated triangle in 3D mesh
            connections[unfoldedFace.idx()] = startingTriangle.idx()
            # Folding direction and adhesive number
            self.addVisualisationData(mesh, unfoldedMesh, originalHalfEdges, unfoldedHalfEdges, glueNumber, dihedralAngles)
        
            if self.angleRangeCalculated is False:
                self.minAngle = min(dihedralAngles)
                self.maxAngle = max(dihedralAngles)
                #sometimes weird large value are returned, like -34345645435464565453356788761029782
                if self.minAngle < -180.0:
                    self.minAngle = -180.0
                if self.maxAngle > 180.0:
                    self.maxAngle = 180.0
                self.angleRange = self.maxAngle - self.minAngle
                #self.msg(minAngle)
                #self.msg(maxAngle)
                #self.msg(angleRange)
                self.angleRangeCalculated = True
        
            halfEdgeConnections = {firstHalfEdge.idx(): firstUnfoldedHalfEdge.idx(),
                                   secondHalfEdge.idx(): secondUnfoldedHalfEdge.idx(),
                                   thirdHalfEdge.idx(): thirdUnfoldedHalfEdge.idx()}
        
            # We walk through the tree
            for dualEdge in nx.dfs_edges(spanningTree, source=startingNode):
                try:  
                    foldingEdge = mesh.edge_handle(spanningTree[dualEdge[0]][dualEdge[1]]['idx'])
                    # Find the corresponding half edge in the output triangle
                    foldingHalfEdge = mesh.halfedge_handle(foldingEdge, 0)
                    if not (mesh.face_handle(foldingHalfEdge).idx() == dualEdge[0]):
                        foldingHalfEdge = mesh.halfedge_handle(foldingEdge, 1)
            
                    # Find the corresponding unwound half edge
                    unfoldedLastHalfEdge = unfoldedMesh.halfedge_handle(halfEdgeConnections[foldingHalfEdge.idx()])
            
                    # Find the point in the unrolled triangle that is not on the folding edge
                    oppositeUnfoldedVertex = unfoldedMesh.to_vertex_handle(unfoldedMesh.next_halfedge_handle(unfoldedLastHalfEdge))
            
                    # We turn the half edges over to lie in the new triangle
                    foldingHalfEdge = mesh.opposite_halfedge_handle(foldingHalfEdge)
                    unfoldedLastHalfEdge = unfoldedMesh.opposite_halfedge_handle(unfoldedLastHalfEdge)
            
                    # The two corners of the folding edge
                    unfoldedFromVertex = unfoldedMesh.from_vertex_handle(unfoldedLastHalfEdge)
                    unfoldedToVertex = unfoldedMesh.to_vertex_handle(unfoldedLastHalfEdge)
            
                    # Calculate the edge lengths in the new triangle
                    secondHalfEdgeInFace = mesh.next_halfedge_handle(foldingHalfEdge)
                    thirdHalfEdgeInFace = mesh.next_halfedge_handle(secondHalfEdgeInFace)
            
                    originalHalfEdges = [foldingHalfEdge, secondHalfEdgeInFace, thirdHalfEdgeInFace]
            
                    edgelengths = [mesh.calc_edge_length(foldingHalfEdge), mesh.calc_edge_length(secondHalfEdgeInFace),
                                   mesh.calc_edge_length(thirdHalfEdgeInFace)]
            
                    # We calculate the two possibilities for the third point in the triangle
                    [newUnfoldedVertex0, newUnfoldedVertex1] = self.getThirdPoint(unfoldedMesh.point(unfoldedFromVertex),
                                                                             unfoldedMesh.point(unfoldedToVertex), edgelengths[0],
                                                                             edgelengths[1], edgelengths[2])
            
            
                    newUnfoldedVertex = unfoldedMesh.add_vertex(newUnfoldedVertex0)
            
                    # Make the face
                    newface = unfoldedMesh.add_face(unfoldedFromVertex, unfoldedToVertex, newUnfoldedVertex)
            
                    secondUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(unfoldedLastHalfEdge)
                    thirdUnfoldedHalfEdge = unfoldedMesh.next_halfedge_handle(secondUnfoldedHalfEdge)
                    unfoldedHalfEdges = [unfoldedLastHalfEdge, secondUnfoldedHalfEdge, thirdUnfoldedHalfEdge]
            
                    # Saving the information about edges and page
                    # Dotted one's in the output
                    unfoldedLastEdge = unfoldedMesh.edge_handle(unfoldedLastHalfEdge)
                    isFoldingEdge[unfoldedLastEdge.idx()] = True
            
                    # Gluing number and folding direction
                    self.addVisualisationData(mesh, unfoldedMesh, originalHalfEdges, unfoldedHalfEdges, glueNumber, dihedralAngles)
            
                    # Related page
                    connections[newface.idx()] = dualEdge[1]
            
                    # Identify the half edges
                    for i in range(3):
                        halfEdgeConnections[originalHalfEdges[i].idx()] = unfoldedHalfEdges[i].idx()
                except Exception as e:
                    inkex.utils.debug("Error walking the dual tree at dualEdge {}".format(e))
                    exit(1)
            return [unfoldedMesh, isFoldingEdge, connections, glueNumber, dihedralAngles]
        except Exception as e:
            inkex.utils.debug("Error: model could not be unfolded. Check for:")
            inkex.utils.debug(" - watertight model / intact hull")
            inkex.utils.debug(" - duplicated edges or faces")
            inkex.utils.debug(" - detached faces or holes")
            inkex.utils.debug(" - missing units")
            inkex.utils.debug(" - missing coordinate system")
            inkex.utils.debug(" - multiple bodies in one file")
            exit(1)
 
    
    def unfold(self, mesh):
        # Calculate the number of surfaces, edges and corners, as well as the length of the longest shortest edge
        numEdges = mesh.n_edges()
        numVertices = mesh.n_vertices()
        numFaces = mesh.n_faces()
    
        if numFaces > self.options.maxNumFaces:
            inkex.utils.debug("Aborted. Target STL file has " + str(numFaces) + " faces, but only " + str( self.options.maxNumFaces) + " are allowed.")
            exit(1)
    
        if self.options.printStats is True:
            inkex.utils.debug("Input STL mesh stats:")
            inkex.utils.debug("* Number of edges: " + str(numEdges))
            inkex.utils.debug("* Number of vertices: " + str(numVertices))
            inkex.utils.debug("* Number of faces: " + str(numFaces))
            inkex.utils.debug("-----------------------------------------------------------")
    
        # Generate the dual graph of the mesh and calculate the weights
        dualGraph = nx.Graph()
    
        # For the weights: calculate the longest and shortest edge of the triangle
        minLength = 1000
        maxLength = 0
        for edge in mesh.edges():
            edgelength = mesh.calc_edge_length(edge)
            if edgelength < minLength:
                minLength = edgelength
            if edgelength > maxLength:
                maxLength = edgelength
    
        # All edges in the net
        for edge in mesh.edges():
            #inkex.utils.debug("edge.idx = " + str(edge.idx()))
            
            # The two sides adjacent to the edge
            face1 = mesh.face_handle(mesh.halfedge_handle(edge, 0))
            face2 = mesh.face_handle(mesh.halfedge_handle(edge, 1))
        
            # The weight
            edgeweight = 1.0 - (mesh.calc_edge_length(edge) - minLength) / (maxLength - minLength)
            
            if self.options.experimentalWeights is True:
                if round(math.degrees(mesh.calc_dihedral_angle(edge)), self.options.roundingDigits) > 0:
                    edgeweight = 1.0 - (mesh.calc_edge_length(edge) - minLength) / (maxLength - minLength)
                if round(math.degrees(mesh.calc_dihedral_angle(edge)), self.options.roundingDigits) < 0:
                    edgeweight = -(1.0 - (mesh.calc_edge_length(edge) - minLength) / (maxLength - minLength))
                if round(math.degrees(mesh.calc_dihedral_angle(edge)), self.options.roundingDigits) == 0:
                    edgeweight = 0.0
                
            #inkex.utils.debug("edgeweight = " + str(edgeweight))
            # Calculate the centres of the pages (only necessary for visualisation)
            center1 = (0, 0)
            for vertex in mesh.fv(face1):
                center1 = center1 + 0.3333333333333333 * np.array([mesh.point(vertex)[0], mesh.point(vertex)[2]])
            center2 = (0, 0)
            for vertex in mesh.fv(face2):
                center2 = center2 + 0.3333333333333333 * np.array([mesh.point(vertex)[0], mesh.point(vertex)[2]])
    
            # Add the new nodes and edge to the dual graph
            dualGraph.add_node(face1.idx(), pos=center1)
            dualGraph.add_node(face2.idx(), pos=center2)
            dualGraph.add_edge(face1.idx(), face2.idx(), idx=edge.idx(), weight=edgeweight) # #might fail without throwing any error ...
           
        # Calculate the minimum spanning tree
        spanningTree = nx.minimum_spanning_tree(dualGraph)
    
        # Unfold the tree
        fullUnfolding = self.unfoldSpanningTree(mesh, spanningTree)
        [unfoldedMesh, isFoldingEdge, connections, glueNumber, dihedralAngles] = fullUnfolding
    
    
        # Resolve the intersections
        # Find all intersections
        epsilon = 1E-12  # Accuracy
        faceIntersections = []
        for face1 in unfoldedMesh.faces():
            for face2 in unfoldedMesh.faces():
                if face2.idx() < face1.idx():  # so that we do not double check the couples
                    # Get the triangle faces
                    triangle1 = []
                    triangle2 = []
                    for halfedge in unfoldedMesh.fh(face1):
                        triangle1.append(unfoldedMesh.point(unfoldedMesh.from_vertex_handle(halfedge)))
                    for halfedge in unfoldedMesh.fh(face2):
                        triangle2.append(unfoldedMesh.point(unfoldedMesh.from_vertex_handle(halfedge)))
                    if self.triangleIntersection(triangle1, triangle2, epsilon):
                        faceIntersections.append([connections[face1.idx()], connections[face2.idx()]])
    
        # Find the paths
        # We find the minimum number of cuts to resolve any self-intersection
    
        # Search all paths between overlapping triangles
        paths = []
        for intersection in faceIntersections:
            paths.append(
                nx.algorithms.shortest_paths.shortest_path(spanningTree, source=intersection[0], target=intersection[1]))
    
        # Find all edges in all threads
        edgepaths = []
        for path in paths:
            edgepath = []
            for i in range(len(path) - 1):
                edgepath.append((path[i], path[i + 1]))
            edgepaths.append(edgepath)
    
        # List of all edges in all paths
        allEdgesInPaths = list(set().union(*edgepaths))
    
        # Count how often each edge occurs
        numEdgesInPaths = []
        for edge in allEdgesInPaths:
            num = 0
            for path in edgepaths:
                if edge in path:
                    num = num + 1
            numEdgesInPaths.append(num)
    
        S = []
        C = []
    
        while len(C) != len(paths):
            # Calculate the weights to decide which edge to cut
            cutWeights = np.empty(len(allEdgesInPaths))
            for i in range(len(allEdgesInPaths)):
                currentEdge = allEdgesInPaths[i]
    
                # Count how many of the paths in which the edge occurs have already been cut
                numInC = 0
                for path in C:
                    if currentEdge in path:
                        numInC = numInC + 1
    
                # Determine the weight
                if (numEdgesInPaths[i] - numInC) > 0:
                    cutWeights[i] = 1 / (numEdgesInPaths[i] - numInC)
                else:
                    cutWeights[i] = 1000  # 1000 = infinite
            # Find the edge with the least weight
            minimalIndex = np.argmin(cutWeights)
            S.append(allEdgesInPaths[minimalIndex])
            # Find all paths where the edge occurs and add them to C
            for path in edgepaths:
                if allEdgesInPaths[minimalIndex] in path and not path in C:
                    C.append(path)
    
        # Now we remove the cut edges from the minimum spanning tree
        spanningTree.remove_edges_from(S)
    
        # Find the cohesive components
        connectedComponents = nx.algorithms.components.connected_components(spanningTree)
        connectedComponentList = list(connectedComponents)
    
        # Unfolding of the components
        unfoldings = []
        for component in connectedComponentList:
            unfoldings.append(self.unfoldSpanningTree(mesh, spanningTree.subgraph(component)))
    
    
        return fullUnfolding, unfoldings
    
    
    def findBoundingBox(self, mesh):
        firstpoint = mesh.point(mesh.vertex_handle(0))
        xmin = firstpoint[0]
        xmax = firstpoint[0]
        ymin = firstpoint[1]
        ymax = firstpoint[1]
        for vertex in mesh.vertices():
            coordinates = mesh.point(vertex)
            if (coordinates[0] < xmin):
                xmin = coordinates[0]
            if (coordinates[0] > xmax):
                xmax = coordinates[0]
            if (coordinates[1] < ymin):
                ymin = coordinates[1]
            if (coordinates[1] > ymax):
                ymax = coordinates[1]
        boxSize = np.maximum(np.abs(xmax - xmin), np.abs(ymax - ymin))
    
        return [xmin, ymin, boxSize]
    
    
    def writeSVG(self, unfolding, size, randomColorSet):
        mesh = unfolding[0]
        isFoldingEdge = unfolding[1]
        glueNumber = unfolding[3]
        dihedralAngles = unfolding[4]
    
        #statistic values
        gluePairs = 0
        cuts = 0
        coplanarEdges = 0
        mountainFolds = 0
        valleyFolds = 0
        
        # Calculate the bounding box
        [xmin, ymin, boxSize] = self.findBoundingBox(unfolding[0])
    
        if size > 0:
            boxSize = size
    
        strokewidth = boxSize * self.options.fontSize / 8000
        dashLength = boxSize * self.options.fontSize / 2000
        spaceLength = boxSize * self.options.fontSize / 800
        textDistance = boxSize * self.options.fontSize / 800
        textStrokeWidth = boxSize * self.options.fontSize / 3000
        fontsize = boxSize * self.options.fontSize / 1000
        
        # Grouping
        uniqueMainId = self.svg.get_unique_id("")
        
        paperfoldPageGroup = self.document.getroot().add(inkex.Group(id=uniqueMainId + "-paperfold-page"))
        
        textGroup = inkex.Group(id=uniqueMainId + "-text")   
        edgesGroup = inkex.Group(id=uniqueMainId + "-edges")
        paperfoldPageGroup.add(textGroup)
        paperfoldPageGroup.add(edgesGroup) 
        
        textFacesGroup = inkex.Group(id=uniqueMainId + "-textFaces")
        textEdgesGroup = inkex.Group(id=uniqueMainId + "-textEdges")
        textGroup.add(textFacesGroup)
        textGroup.add(textEdgesGroup)
      
        #we could write the unfolded mesh as a 2D stl file to disk if we like:
        if self.options.writeTwoDSTL is True:
            if not os.path.exists(self.options.TwoDSTLdir):
                inkex.utils.debug("Export location for 2D STL unfoldings does not exist. Please select a another dir and try again.")
                exit(1)
            else:
                om.write_mesh(os.path.join(self.options.TwoDSTLdir, uniqueMainId + "-paperfold-page.stl"), mesh)
    
        
        #########################################################
        # Nmbering triangle faces with circle around
        #########################################################
        if self.options.printTriangleNumbers is True:
            for face in mesh.faces():
                faceNr = str(face.idx() + 1)
                centroid = mesh.calc_face_centroid(face) 
                textFaceGroup = inkex.Group(id=uniqueMainId + "-textFace-" + faceNr)
                
                circle = textFaceGroup.add(Circle(cx="{:0.6f}".format(centroid[0]), cy="{:0.6f}".format(centroid[1]), r="{:0.6f}".format(fontsize)))
                circle.set('id', uniqueMainId + "-textFaceCircle-" + faceNr)
                circle.set("style", "stroke:#000000;stroke-width:{:0.6f}".format(strokewidth/2) + ";fill:none")
                
                text = textFaceGroup.add(TextElement(id=uniqueMainId + "-textFaceNumber-" + faceNr))
                text.set("x", "{:0.6f}".format(centroid[0]))
                text.set("y", "{:0.6f}".format(centroid[1] + fontsize / 3))
                text.set("font-size", "{:0.6f}".format(fontsize))
                text.set("style", "stroke-width {:0.6f}".format(textStrokeWidth) + ";text-anchor:middle;text-align:center")
                
                tspan = text.add(Tspan(id=uniqueMainId + "-textFaceNumberTspan-" + faceNr))
                tspan.set("x", "{:0.6f}".format(centroid[0]))
                tspan.set("y", "{:0.6f}".format(centroid[1] + fontsize / 3))
                tspan.set("style", "stroke-width {:0.6f}".format(textStrokeWidth) + ";text-anchor:middle;text-align:center")
                tspan.text = faceNr
                textFacesGroup.append(textFaceGroup)
      
        #########################################################
        # Nmbering triangle edges and style them according to their type
        #########################################################        
        # Go over all edges of the grid
        for edge in mesh.edges():
            # The two endpoints
            he = mesh.halfedge_handle(edge, 0)
            vertex0 = mesh.point(mesh.from_vertex_handle(he))
            vertex1 = mesh.point(mesh.to_vertex_handle(he))
    
            # Write a straight line between the two corners
            line = edgesGroup.add(PathElement())
            line.set('d', "M {:0.6f},{:0.6f} {:0.6f},{:0.6f}".format(vertex0[0], vertex0[1], vertex1[0], vertex1[1]))
            # Colour depending on folding direction
            lineStyle = {"fill": "none"}
    
            lineStyle.update({"stroke": self.options.colorCutEdges})
            line.set("id", uniqueMainId + "-cut-edge-" + str(edge.idx())) 
                        
            lineStyle.update({"stroke-width": "{:0.6f}".format(strokewidth)})
            lineStyle.update({"stroke-linecap":"butt"})
            lineStyle.update({"stroke-linejoin":"miter"})
            lineStyle.update({"stroke-miterlimit":"4"})  
         
            dihedralAngle = dihedralAngles[edge.idx()]
                
            # Dotted lines for folding edges    
            if isFoldingEdge[edge.idx()]:
                if self.options.dashes is True:
                    lineStyle.update({"stroke-dasharray":"{:0.6f}, {:0.6f}".format(dashLength, spaceLength)})
                if dihedralAngle > 0:
                    lineStyle.update({"stroke": self.options.colorMountainFolds})
                    line.set("id", uniqueMainId + "-mountain-fold-" + str(edge.idx()))
                    mountainFolds += 1
                if dihedralAngle < 0:
                    lineStyle.update({"stroke": self.options.colorValleyFolds})
                    line.set("id", uniqueMainId + "-valley-fold-" + str(edge.idx()))
                    valleyFolds += 1
                if dihedralAngle == 0:
                    lineStyle.update({"stroke": self.options.colorCoplanarEdges})
                    line.set("id", uniqueMainId + "-coplanar-edge-" + str(edge.idx()))
                    if self.options.importCoplanarEdges is False:
                        line.delete()
                    coplanarEdges += 1
            else:
                lineStyle.update({"stroke-dasharray":"none"})
    
            # The number of the edge to be glued  
            if not isFoldingEdge[edge.idx()]:
                if self.options.separateGluePairsByColor is True:
                    lineStyle.update({"stroke": randomColorSet[glueNumber[edge.idx()]]})
                gluePairs += 1
                
            lineStyle.update({"stroke-dashoffset":"0.0"})
            lineStyle.update({"stroke-opacity":"1.0"})       
    
            if self.options.edgeStyle == "saturationsForAngles":
                if dihedralAngle != 0: #we dont want to apply HSL adjustments for zero angle lines because they would be invisible then
                    hslColor = inkex.Color(lineStyle.get('stroke')).to_hsl()
                    newSaturation = abs(dihedralAngle / self.angleRange) * 100 #percentage values
                    hslColor.saturation = newSaturation
                    lineStyle.update({"stroke":hslColor.to_rgb()})
    
            elif self.options.edgeStyle == "opacitiesForAngles":
                if dihedralAngle != 0: #we dont want to apply opacity adjustments for zero angle lines because they would be invisible then
                    opacity = abs(dihedralAngle / 180)
                    lineStyle.update({"stroke-opacity": "{:0.6f}".format(opacity)})
    
            line.style = lineStyle
           
            #########################################################
            # Textual things
            #########################################################
            halfEdge = mesh.halfedge_handle(edge, 0) # Find halfedge in the face
            if mesh.face_handle(halfEdge).idx() == -1:
                halfEdge = mesh.opposite_halfedge_handle(halfEdge)
            vector = mesh.calc_edge_vector(halfEdge)
            vector = vector / np.linalg.norm(vector) # normalize
            midPoint = 0.5 * (
                    mesh.point(mesh.from_vertex_handle(halfEdge)) + mesh.point(mesh.to_vertex_handle(halfEdge)))
            rotatedVector = np.array([-vector[1], vector[0], 0])
            angle = np.arctan2(vector[1], vector[0])
            position = midPoint + textDistance * rotatedVector
            if self.options.flipLabels is True:
                position = midPoint - textDistance * rotatedVector
            rotation = 180 / np.pi * angle
            if self.options.flipLabels is True:
                rotation += 180
    
            edgeNr = str(edge.idx() + 1)
            text = textEdgesGroup.add(TextElement(id=uniqueMainId + "-edgeNumber-" + edgeNr))
            text.set("x", "{:0.6f}".format(position[0]))
            text.set("y", "{:0.6f}".format(position[1]))
            text.set("font-size", "{:0.6f}".format(fontsize))
            text.set("style", "stroke-width {:0.6f}".format(textStrokeWidth) + ";text-anchor:middle;text-align:center")
            text.set("transform", "rotate({:0.6f} {:0.6f} {:0.6f})".format(rotation, position[0], position[1]))
            
            tspan = text.add(Tspan())
            tspan.set("x", "{:0.6f}".format(position[0]))
            tspan.set("y", "{:0.6f}".format(position[1]))
            tspan.set("style", "stroke-width {:0.6f}".format(textStrokeWidth) + ";text-anchor:middle;text-align:center")
            tspanText = []
            if self.options.printGluePairNumbers is True and not isFoldingEdge[edge.idx()]:
                tspanText.append(str(glueNumber[edge.idx()] + 1))
            if self.options.printAngles is True and dihedralAngle != 0.0:
                tspanText.append("{:0.2f}°".format(dihedralAngle))
            if self.options.printLengths is True:
                printUnit = True
                if printUnit is False:
                    unitToPrint = self.svg.unit
                else:
                    unitToPrint = ""
                tspanText.append("{:0.2f} {}".format(self.options.scalefactor * math.hypot(vertex1[0] - vertex0[0], vertex1[1] - vertex0[1]), unitToPrint))
            tspan.text = " | ".join(tspanText)
    
            if tspan.text == "": #if no text we remove again to clean up
                text.delete()
                tspan.delete()
 
        '''
        merge cutting edges to single contour. code ripped off from "join path" extension
        '''
        if self.options.merge_cut_lines is True:
            cutEdges = []
            
            #find all cutting edges - they have to be sorted to build up a clean continuous line
            for edge in edgesGroup:
                edge_id = edge.get('id')
                if "cut-edge-" in edge_id:
                    cutEdges.append(edge)

            #find the cutting edge which starts at the previous cutting edge end point
            paths = {p.get('id'): self.getPartsFromCubicSuper(CubicSuperPath(p.get('d'))) for p in  cutEdges }
            pathIds = [p.get('id') for p in cutEdges]

            startPathId = pathIds[0]
            pathIds = self.getArrangedIds(paths, startPathId)
                
            newParts = []
            firstElem = None
            for key in pathIds:
                parts = paths[key]
                # ~ parts = getPartsFromCubicSuper(cspath)
                start = parts[0][0][0]
                elem = self.svg.getElementById(key)
        
                if(len(newParts) == 0):
                    newParts += parts[:]
                    firstElem = elem
                else:
                    if(self.vectCmpWithMargin(start, newParts[-1][-1][-1], margin = .01)):
                        newParts[-1] += parts[0]
                    else:
                        newSeg = [newParts[-1][-1][-1], newParts[-1][-1][-1], start, start]
                        newParts[-1].append(newSeg)                    
                        newParts[-1] += parts[0]
                    
                    if(len(parts) > 1):
                        newParts += parts[1:]
                
                parent = elem.getparent()
                parent.remove(elem)
        
            newElem = copy.copy(firstElem)
            oldId = firstElem.get('id')
            newElem.set('d', CubicSuperPath(self.getCubicSuperFromParts(newParts)))
            newElem.set('id', oldId + '_joined')
            parent.append(newElem) #insert at the end
 
        if len(textFacesGroup) == 0:
            textFacesGroup.delete() #delete if empty set
            
        if len(textEdgesGroup) == 0:
            textEdgesGroup.delete() #delete if empty set
            
        if len(textGroup) == 0:
            textGroup.delete() #delete if empty set
              
        if self.options.printStats is True:
            inkex.utils.debug(" * Number of cuts: " + str(cuts))
            inkex.utils.debug(" * Number of coplanar edges: " + str(coplanarEdges))
            inkex.utils.debug(" * Number of mountain folds: " + str(mountainFolds))
            inkex.utils.debug(" * Number of valley folds: " + str(valleyFolds))
            inkex.utils.debug(" * Number of glue pairs: {:0.0f}".format(gluePairs / 2))
            inkex.utils.debug(" * min angle: {:0.2f}".format(self.minAngle))
            inkex.utils.debug(" * max angle: {:0.2f}".format(self.maxAngle))
            inkex.utils.debug(" * Edge angle range: {:0.2f}".format(self.angleRange))
                        
        return paperfoldPageGroup


    def floatCmpWithMargin(self, float1, float2, margin):
        return abs(float1 - float2) < margin 
  
        
    def vectCmpWithMargin(self, vect1, vect2, margin):
        return all(self.floatCmpWithMargin(vect2[i], vect1[i], margin) for i in range(0, len(vect1)))
  
    
    def getPartsFromCubicSuper(self, cspath):
        parts = []
        for subpath in cspath:
            part = []
            prevBezPt = None            
            for i, bezierPt in enumerate(subpath):
                if(prevBezPt != None):
                    seg = [prevBezPt[1], prevBezPt[2], bezierPt[0], bezierPt[1]]
                    part.append(seg)
                prevBezPt = bezierPt
            parts.append(part)
        return parts
  
            
    def getCubicSuperFromParts(self, parts):
        cbsuper = []
        for part in parts:
            subpath = []
            lastPt = None
            pt = None
            for seg in part:
                if(pt == None):
                    ptLeft = seg[0]
                    pt = seg[0]
                ptRight = seg[1]
                subpath.append([ptLeft, pt, ptRight])
                ptLeft = seg[2]
                pt = seg[3]
            subpath.append([ptLeft, pt, pt])
            cbsuper.append(subpath)
        return cbsuper
   
        
    def getArrangedIds(self, pathMap, startPathId):
        nextPathId = startPathId
        orderPathIds = [nextPathId]
        
        #Arrange in order
        while(len(orderPathIds) < len(pathMap)):
            minDist = 9e+100 #A large float
            closestId = None        
            np = pathMap[nextPathId]
            npPts = [np[-1][-1][-1]]
            if(len(orderPathIds) == 1):#compare both the ends for the first path
                npPts.append(np[0][0][0])
            
            for key in pathMap:
                if(key in orderPathIds):
                    continue
                parts = pathMap[key] 
                start = parts[0][0][0]
                end = parts[-1][-1][-1]
                
                for i, npPt in enumerate(npPts):
                    dist = abs(start[0] - npPt[0]) + abs(start[1] - npPt[1])
                    if(dist < minDist):
                        minDist = dist
                        closestId = key
                    dist = abs(end[0] - npPt[0]) + abs(end[1] - npPt[1])
                    if(dist < minDist):
                        minDist = dist
                        pathMap[key] = [[[pts for pts in reversed(seg)] for seg in \
                            reversed(part)] for part in reversed(parts)]
                        closestId = key
                        
                    #If start point of the first path is closer reverse its direction    
                    if(i > 0 and closestId == key):
                        pathMap[nextPathId] = [[[pts for pts in reversed(seg)] for seg in \
                            reversed(part)] for part in reversed(np)]
                        
            orderPathIds.append(closestId)
            nextPathId = closestId
        return orderPathIds
 
                
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        
        #Input
        pars.add_argument("--inputfile")
        pars.add_argument("--maxNumFaces", type=int, default=200, help="If the STL file has too much detail it contains a large number of faces. This will make unfolding extremely slow. So we can limit it.")
        pars.add_argument("--scalefactor", type=float, default=1.0, help="Manual scale factor")
        pars.add_argument("--roundingDigits", type=int, default=3, help="Digits for rounding")

        #Output
        pars.add_argument("--printGluePairNumbers", type=inkex.Boolean, default=False, help="Print glue pair numbers on cut edges")
        pars.add_argument("--printAngles", type=inkex.Boolean, default=False, help="Print folding angles on edges")
        pars.add_argument("--printLengths", type=inkex.Boolean, default=False, help="Print lengths on edges")
        pars.add_argument("--printTriangleNumbers", type=inkex.Boolean, default=False, help="Print triangle numbers on faces")
        pars.add_argument("--importCoplanarEdges", type=inkex.Boolean, default=False, help="Import coplanar edges")
        pars.add_argument("--experimentalWeights", type=inkex.Boolean, default=False, help="Mess around with algorithm")
        pars.add_argument("--printStats", type=inkex.Boolean, default=False, help="Show some unfold statistics")
        pars.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        pars.add_argument("--extraborder", type=float, default=0.0)
        pars.add_argument("--extraborderUnits")
        pars.add_argument("--writeTwoDSTL", type=inkex.Boolean, default=False, help="Write 2D STL unfoldings")
        pars.add_argument("--TwoDSTLdir", default="./inkscape_export/", help="Location to save exported 2D STL")

        #Style 
        pars.add_argument("--fontSize", type=int, default=15, help="Label font size (%)")
        pars.add_argument("--flipLabels", type=inkex.Boolean, default=False, help="Flip labels")
        pars.add_argument("--dashes", type=inkex.Boolean, default=True, help="Dashes for cut/coplanar edges")
        pars.add_argument("--merge_cut_lines", type=inkex.Boolean, default=True, help="Merge cut lines")
        pars.add_argument("--edgeStyle", help="Adjust color saturation or opacity for folding edges. The larger the angle the darker the color")
        pars.add_argument("--separateGluePairsByColor", type=inkex.Boolean, default=False, help="Separate glue pairs by color")
        pars.add_argument("--colorCutEdges", type=Color, default='255', help="Cut edges")
        pars.add_argument("--colorCoplanarEdges", type=Color, default='1943148287', help="Coplanar edges")
        pars.add_argument("--colorValleyFolds", type=Color, default='3422552319', help="Valley fold edges")
        pars.add_argument("--colorMountainFolds", type=Color, default='879076607', help="Mountain fold edges")
        
        #Post Processing
        pars.add_argument("--joineryMode", type=inkex.Boolean, default=False, help="Enable joinery mode")
        pars.add_argument("--origamiSimulatorMode", type=inkex.Boolean, default=False, help="Enable origami simulator mode")
   
               
    def effect(self):
        if not os.path.exists(self.options.inputfile):
            inkex.utils.debug("The input file does not exist. Please select a proper file and try again.")
            exit(1)
        mesh = om.read_trimesh(self.options.inputfile)
        #mesh = om.read_polymesh(self.options.inputfile) #we must work with triangles instead of polygons because the algorithm works with that ONLY

        fullUnfolded, unfoldedComponents = self.unfold(mesh)
        unfoldComponentCount = len(unfoldedComponents)
 
        #if len(unfoldedComponents) == 0:
        #    inkex.utils.debug("Error: no components were unfolded.")
        #    exit(1)
 
        if self.options.printStats is True:
            inkex.utils.debug("Unfolding components: {:0.0f}".format(unfoldComponentCount))
        
        # Compute maxSize of the components
        # All components must be scaled to the same size as the largest component
        maxSize = 0
        for unfolding in unfoldedComponents:
            [xmin, ymin, boxSize] = self.findBoundingBox(unfolding[0])
            if boxSize > maxSize:
                maxSize = boxSize
                   
        xSpacing = maxSize / unfoldComponentCount * 0.1 # 10% spacing between each component; calculated by max box size
                     
        #########################################################
        # mode config for joinery:
        #########################################################
        if self.options.joineryMode is True:
            self.options.separateGluePairsByColor = True #we need random colors in this mode
             
             
        #########################################################
        # mode config for origami simulator:
        #########################################################
            '''
            required style for Origami Simulator:
            colors:
             - #ff0000 (red)     - mountain folds
             - #0000ff (blue)    - valley folds
             - #000000 (black)   - boundary cuts (for both the outline of the pattern and any internal holes)
             - #ffff00 (yellow)  - coplonar triangle edges ("facet creases") (no support for polygons > 3 edges)
             - #00ff00 (green)   - thin slits
             - #ff00ff (magenta) - undriven creases (swing freely)

            opacity:
             - final fold angle of a mountain or valley fold is set by its opacity. Any fold angle between 0° and 180° may be used. For example:
                  - 1.0 = 180° (fully folded)
                  - 0.5 = 90°
                  - 0 = 0° (flat)
            '''      
        if self.options.origamiSimulatorMode is True:
            self.options.joineryMode = True #we set to true even if false because we need the same flat structure for origami simulator
            self.options.separateGluePairsByColor = False #we need to have no weird random colors in this mode
            self.options.edgeStyle = "opacitiesForAngles" #highly important for simulation
            self.options.dashes = False
            self.options.printGluePairNumbers = False
            self.options.printAngles = False
            self.options.printLengths = False
            self.options.importCoplanarEdges = True
            self.options.colorCutEdges = "#000000" #black
            self.options.colorCoplanarEdges = "#ffff00" #yellow
            self.options.colorMountainFolds = "#ff0000" #red
            self.options.colorValleyFolds = "#0000ff" #blue
 
        #generate random colors; used to identify glue tab pairs
        randomColorSet = []
        if self.options.separateGluePairsByColor:
            while len(randomColorSet) < len(mesh.edges()):
                r = lambda: random.randint(0,255)
                newColor = '#%02X%02X%02X' % (r(),r(),r())
                if newColor not in randomColorSet:
                    randomColorSet.append(newColor)
                  
        # Create a new container group to attach all paperfolds
        paperfoldMainGroup = self.document.getroot().add(inkex.Group(id=self.svg.get_unique_id("paperfold-"))) #make a new group at root level
        for i in range(len(unfoldedComponents)):
            if self.options.printStats is True:
                inkex.utils.debug("-----------------------------------------------------------")
                inkex.utils.debug("Unfolding component nr.: {:0.0f}".format(i))
            paperfoldPageGroup = self.writeSVG(unfoldedComponents[i], maxSize, randomColorSet)
            #translate the groups next to each other to remove overlappings
            if i != 0:
                #previous_bbox = paperfoldMainGroup[i-1].bounding_box()
                #as TextElement, Tspan and Circle cause wrong BBox calculation, we have to make it more complex
                previous_bbox = inkex.BoundingBox()
                for child in self.getElementChildren(paperfoldMainGroup[i-1]):
                    if not isinstance (child, inkex.TextElement) and \
                       not isinstance (child, inkex.Tspan) and \
                       not isinstance (child, inkex.Circle):
                        transform = inkex.Transform()
                        parent = child.getparent()
                        if parent is not None and isinstance(parent, inkex.ShapeElement):
                            transform = parent.composed_transform()
                        previous_bbox += child.bounding_box(transform)
                          
                #this_bbox = paperfoldPageGroup.bounding_box()
                this_bbox = inkex.BoundingBox()
                for child in self.getElementChildren(paperfoldPageGroup):
                #as TextElement, Tspan and Circle cause wrong BBox calculation, we have to make it more complex
                    if not isinstance (child, inkex.TextElement) and \
                       not isinstance (child, inkex.Tspan) and \
                       not isinstance (child, inkex.Circle):
                        transform = inkex.Transform()
                        parent = child.getparent()
                        if parent is not None and isinstance(parent, inkex.ShapeElement):
                            transform = parent.composed_transform()
                        this_bbox += child.bounding_box(transform)   
                
                #self.msg(previous_bbox)
                #self.msg(this_bbox)
                paperfoldPageGroup.set("transform", "translate({:0.6f}, 0.0)".format(previous_bbox.left + previous_bbox.width - this_bbox.left + xSpacing))
            paperfoldMainGroup.append(paperfoldPageGroup) 

        #apply scale factor
        translation_matrix = [[self.options.scalefactor, 0.0, 0.0], [0.0, self.options.scalefactor, 0.0]]
        paperfoldMainGroup.transform = Transform(translation_matrix) @ paperfoldMainGroup.transform
        #paperfoldMainGroup.set('transform', 'scale(%f,%f)' % (self.options.scalefactor, self.options.scalefactor))

        #adjust canvas to the inserted unfolding
        if self.options.resizetoimport:
            bbox = paperfoldMainGroup.bounding_box()
            namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
            root = self.svg.getElement('//svg:svg');
            offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborderUnits)
            root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
            root.set('width', "{:0.6f}{}".format(bbox.width + 2 * offset, self.svg.unit))
            root.set('height', "{:0.6f}{}".format(bbox.height + 2 * offset, self.svg.unit))

        #if set, we move all edges (path elements) to the top level
        if self.options.joineryMode is True:
            for paperfoldPage in paperfoldMainGroup.getchildren():
                for child in paperfoldPage:
                    if "-edges" in child.get('id'):
                        for edge in child:
                            edgeTransform = edge.composed_transform()
                            self.document.getroot().append(edge)
                            edge.transform = edgeTransform


if __name__ == '__main__':
    Paperfold().run()