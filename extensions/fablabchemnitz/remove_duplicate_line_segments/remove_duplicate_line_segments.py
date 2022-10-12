#!/usr/bin/env python3
#
# Copyright (C) 2021 Ellen Wasboe, ellen@wasbo.net
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""s
Remove duplicate lines by comparing cubic bezier control points after converting to cubic super path.
Optionally include searching for overlaps within the same path (which might cause trouble if the tolerance is too high and small neighbour segments are regarded as a match.
Optionally add a tolerance for the comparison.
Optionally interpolate the four control points of the remaining and the removed segment. 
"""

import inkex
from inkex import bezier, PathElement, CubicSuperPath, Transform
import numpy as np
from tkinter import messagebox

class removeDuplicateLineSegments(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab", default="options")
        pars.add_argument("--tolerance", default="0")
        pars.add_argument("--minUse", type=inkex.Boolean, default=False)
        pars.add_argument("--selfPath", type=inkex.Boolean, default=False)
        pars.add_argument("--interp", type=inkex.Boolean, default=False)
        
    """Remove duplicate lines"""
    def effect(self):       
        tolerance=float(self.options.tolerance)
        if self.options.minUse == False:
            tolerance=0
        
        coords=[]#one segmentx8 subarray for each path and subpath (paths and subpaths treated equally)
        pathNo=[]
        subPathNo=[]
        cPathNo=[]#counting alle paths and subpaths equally
        removeSegmentPath=[]
        removeSegmentSubPath=[]
        removeSegment_cPath=[]
        removeSegment=[]
        matchSegmentPath=[]
        matchSegmentSubPath=[]
        matchSegment_cPath=[]
        matchSegment=[]
        matchSegmentRev=[]
        
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")
        nFailed=0
        nInkEffect=0
        p=0
        c=0
        idsNotPath=[]
        for id, elem in self.svg.selection.id_dict().items():
            thisIsPath=True
            if elem.get('d')==None:
                thisIsPath=False
                nFailed+=1
                idsNotPath.append(id)
            if elem.get('inkscape:path-effect') != None:
                thisIsPath=False
                nInkEffect+=1
                idsNotPath.append(id)

            if thisIsPath:
                #apply transformation matrix if present
                csp = CubicSuperPath(elem.get('d'))
                elem.path=elem.path.to_absolute()
                transformMat = Transform(elem.get('transform'))
                cpsTransf=csp.transform(transformMat)
                elem.path = cpsTransf.to_path(curves_only=True)
                pp=elem.path
                    
                s=0
                #create matrix with segment coordinates p1x p1y c1x c1y c2x c2y p2x p2y
                for sub in pp.to_superpath():                   
                    coordsThis=np.zeros((len(sub)-1,8))
                    
                    i=0
                    while i <= len(sub) - 2:
                        coordsThis[i][0]=sub[i][1][0]
                        coordsThis[i][1]=sub[i][1][1]
                        coordsThis[i][2]=sub[i][2][0]
                        coordsThis[i][3]=sub[i][2][1]
                        coordsThis[i][4]=sub[i+1][0][0]
                        coordsThis[i][5]=sub[i+1][0][1]
                        coordsThis[i][6]=sub[i+1][1][0]
                        coordsThis[i][7]=sub[i+1][1][1]                   
                                
                        i+=1
                    
                    coords.append(coordsThis)
                    pathNo.append(p)
                    subPathNo.append(s)
                    cPathNo.append(c)
                    c+=1
                    s+=1
                p+=1
        if nFailed > 0:
            messagebox.showwarning('Warning',str(nFailed)+' selected elements did not have a path. Groups, shapeelements and text will be ignored.')

        if nInkEffect > 0:
            messagebox.showwarning('Warning',str(nInkEffect)+' selected elements have an inkscape:path-effect applied. These elements will be ignored to avoid confusing results. Apply Paths->Object to path (Shift+Ctrl+C) and retry .')  
        
        origCoords=[]
        for item in coords: origCoords.append(np.copy(item))#make a real copy (not a reference that changes with the original
        #search for overlapping or close segments
        #for each segment find if difference of any x or y is less than tolerance - if so - calculate 2d-distance and find if all 4 less than tolerance
        #repeat with reversed segment
        #if match found set match coordinates to -1000 to mark this to be removed and being ignored later on
        i=0
        while i <= len(coords)-1:#each path or subpath
            j=0
            while j<=len(coords[i][:,0])-1:#each segment j of path i
                k=0
                while k<=len(coords)-1:#search all other subpaths
                    evalPath=True
                    if k == i and self.options.selfPath == False:#do not test path against itself
                        evalPath=False
                    if evalPath:
                        segmentCoords=np.array(coords[i][j,:])
                        if segmentCoords[0] != -1000 and segmentCoords[1] != -1000:
                            searchCoords=np.array(coords[k])
                            if k==i:
                                searchCoords[j,:]=-2000#avoid comparing segment with itself
                            subtr=np.abs(searchCoords-segmentCoords)
                            maxval=subtr.max(1)
                            lessTol=np.argwhere(maxval<tolerance)        
                            matchThis=False
                            matchThisRev=False
                            finalK=0
                            lesstolc=0
                            if len(lessTol) > 0:#proceed to calculate 2d distance where both x and y distance is less than tolerance
                                c=0
                                while c < len(lessTol):
                                    dists=np.zeros(4)
                                    dists[0]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][0],2),np.power(subtr[lessTol[c,0]][1],2)))
                                    dists[1]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][2],2),np.power(subtr[lessTol[c,0]][3],2)))
                                    dists[2]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][4],2),np.power(subtr[lessTol[c,0]][5],2)))
                                    dists[3]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][6],2),np.power(subtr[lessTol[c,0]][7],2)))
                                    if dists.max() < tolerance:
                                        matchThis=True
                                        finalK=k
                                        lesstolc=lessTol[c]
                                    c+=1
                            if matchThis == False:#try reversed
                                segmentCoordsRev=[segmentCoords[6], segmentCoords[7],segmentCoords[4],segmentCoords[5],segmentCoords[2],segmentCoords[3],segmentCoords[0],segmentCoords[1]]
                                subtr=np.abs(searchCoords-segmentCoordsRev)
                                maxval=subtr.max(1)
                                lessTol=np.argwhere(maxval<tolerance)   
                                if len(lessTol) > 0:#proceed to calculate 2d distance where both x and y distance is less than tolerance
                                    c=0
                                    while c < len(lessTol):
                                        dists=np.zeros(4)
                                        dists[0]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][0],2),np.power(subtr[lessTol[c,0]][1],2)))
                                        dists[1]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][2],2),np.power(subtr[lessTol[c,0]][3],2)))
                                        dists[2]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][4],2),np.power(subtr[lessTol[c,0]][5],2)))
                                        dists[3]=np.sqrt(np.add(np.power(subtr[lessTol[c,0]][6],2),np.power(subtr[lessTol[c,0]][7],2)))
                                        if dists.max() < tolerance:
                                            matchThis=True
                                            matchThisRev=True
                                            finalK=k
                                            lesstolc=lessTol[c]
                                        c+=1
                            
                            if matchThis:
                                coords[finalK][lesstolc,:]=-1000
                                removeSegmentPath.append(pathNo[finalK])
                                removeSegmentSubPath.append(subPathNo[finalK])
                                removeSegment_cPath.append(cPathNo[finalK])
                                removeSegment.append(lesstolc)
                                matchSegmentPath.append(pathNo[i])
                                matchSegmentSubPath.append(subPathNo[i])
                                matchSegment_cPath.append(cPathNo[i])
                                matchSegment.append(j)
                                matchSegmentRev.append(matchThisRev)        
                                        
                    k+=1
                j+=1
            i+=1
                
        #(interpolate remaining and) remove segments with a match
        if len(removeSegmentPath) > 0:          
            removeSegmentPath=np.array(removeSegmentPath)
            removeSegmentSubPath=np.array(removeSegmentSubPath)
            removeSegment_cPath=np.array(removeSegment_cPath)
            removeSegment=np.array(removeSegment)
            matchSegmentPath=np.array(matchSegmentPath)
            matchSegment_cPath=np.array(matchSegment_cPath)
            matchSegmentSubPath=np.array(matchSegmentSubPath)
            matchSegment=np.array(matchSegment)
            matchSegmentRev=np.array(matchSegmentRev)

            #first interpolate remaining segment
            if self.options.interp:
                idx=np.argsort(matchSegmentPath)
                matchSegmentPath=matchSegmentPath[idx]
                matchSegment_cPath=matchSegment_cPath[idx]
                matchSegmentSubPath=matchSegmentSubPath[idx]
                matchSegment=matchSegment[idx]
                matchSegmentRev=matchSegmentRev[idx]
                remSegmentPath=removeSegmentPath[idx]
                remSegment_cPath=removeSegment_cPath[idx]
                remSegment=removeSegment[idx]
                
                i=0
                for id, elem in self.svg.selection.id_dict().items():#each path         
                    if not id in idsNotPath:
                        if i in matchSegmentPath:           
                            idxi=np.argwhere(matchSegmentPath==i)
                            idxi=idxi.reshape(-1)
                            icMatch=matchSegment_cPath[idxi]
                            iSegMatch=matchSegment[idxi]
                            iSegMatchRev=matchSegmentRev[idxi]
                            iSubMatch=matchSegmentSubPath[idxi]
                            iSegRem=remSegment[idxi]
                            icRem=remSegment_cPath[idxi]
                            iPathRem=remSegmentPath[idxi]
                            new=[]
                            j=0
                            for sub in elem.path.to_superpath():#each subpath 
                                idxj=np.argwhere(iSubMatch==j)
                                idxj=idxj.reshape(-1)
                                this_cMatch=icMatch[idxj]
                                thisSegMatch=iSegMatch[idxj]
                                thisSegMatchRev=iSegMatchRev[idxj]                            
                                thisSegRem=iSegRem[idxj].reshape(-1)
                                this_cRem=icRem[idxj]
                                thisPathRem=iPathRem[idxj] 
                                k=0
                                while k<len(thisSegMatch):
                               
                                    if thisSegMatchRev[k]==False:
                                        x1interp=0.5*(sub[thisSegMatch[k]][1][0]+origCoords[this_cRem[k]][thisSegRem[k],0])
                                        y1interp=0.5*(sub[thisSegMatch[k]][1][1]+origCoords[this_cRem[k]][thisSegRem[k],1])
                                        cx1interp=0.5*(sub[thisSegMatch[k]][2][0]+origCoords[this_cRem[k]][thisSegRem[k],2])
                                        cy1interp=0.5*(sub[thisSegMatch[k]][2][1]+origCoords[this_cRem[k]][thisSegRem[k],3])
                                        x2interp=0.5*(sub[thisSegMatch[k]+1][1][0]+origCoords[this_cRem[k]][thisSegRem[k],6])
                                        y2interp=0.5*(sub[thisSegMatch[k]+1][1][1]+origCoords[this_cRem[k]][thisSegRem[k],7])
                                        cx2interp=0.5*(sub[thisSegMatch[k]+1][0][0]+origCoords[this_cRem[k]][thisSegRem[k],4])
                                        cy2interp=0.5*(sub[thisSegMatch[k]+1][0][1]+origCoords[this_cRem[k]][thisSegRem[k],5])
                                    else:
                                        x1interp=0.5*(sub[thisSegMatch[k]][1][0]+origCoords[this_cRem[k]][thisSegRem[k],6])
                                        y1interp=0.5*(sub[thisSegMatch[k]][1][1]+origCoords[this_cRem[k]][thisSegRem[k],7])
                                        cx1interp=0.5*(sub[thisSegMatch[k]][2][0]+origCoords[this_cRem[k]][thisSegRem[k],4])
                                        cy1interp=0.5*(sub[thisSegMatch[k]][2][1]+origCoords[this_cRem[k]][thisSegRem[k],5])
                                        x2interp=0.5*(sub[thisSegMatch[k]+1][1][0]+origCoords[this_cRem[k]][thisSegRem[k],0])
                                        y2interp=0.5*(sub[thisSegMatch[k]+1][1][1]+origCoords[this_cRem[k]][thisSegRem[k],1])
                                        cx2interp=0.5*(sub[thisSegMatch[k]+1][0][0]+origCoords[this_cRem[k]][thisSegRem[k],2])
                                        cy2interp=0.5*(sub[thisSegMatch[k]+1][0][1]+origCoords[this_cRem[k]][thisSegRem[k],3])
                                    
                                    sub[thisSegMatch[k]][1]=[x1interp,y1interp]
                                    sub[thisSegMatch[k]][2]=[cx1interp,cy1interp]
                                    sub[thisSegMatch[k]+1][1]=[x2interp,y2interp]
                                    sub[thisSegMatch[k]+1][0]=[cx2interp,cy2interp]
                                                                      
                                    if thisSegMatch[k]==0:
                                        sub[thisSegMatch[k]][0]=[x1interp,y1interp]
                                    if thisSegMatch[k]+1==len(sub)-1:
                                        sub[thisSegMatch[k]+1][2]=[x2interp,y2interp]
                                    k+=1

                                new.append(sub)
                                j+=1
                                
                            elem.path = CubicSuperPath(new).to_path(curves_only=True)
                            
                        i+=1
            
            #remove
            i=0
            for id, elem in self.svg.selection.id_dict().items():#each path 
                if not id in idsNotPath:
                    idx=np.argwhere(removeSegmentPath==i)              
                    if len(idx) > 0:
                        idx=idx.reshape(1,-1)
                        idx=idx[0]
                        new=[]
                        j=0
                        for sub in elem.path.to_superpath():#each subpath                       
                            thisSegRem=removeSegment[idx]
                            keepLast=False if len(sub)-2 in thisSegRem else True
                            keepNext2Last=False if len(sub)-3 in thisSegRem else True
                            thisSubPath=removeSegmentSubPath[idx]
                            idx2=np.argwhere(removeSegmentSubPath[idx]==j)                      
                            if len(idx2) > 0:
                                idx2=idx2.reshape(1,-1)
                                idx2=idx2[0]
                                thisSegRem=thisSegRem[idx2]
                                if len(thisSegRem) < len(sub)-1:#if any segment to be kept
                                    #find first segment
                                    k=0
                                    if 0 in thisSegRem:#remove first segment
                                        proceed=True
                                        while proceed:
                                            if k+1 in thisSegRem:
                                                k+=1
                                            else:
                                                proceed=False
                                        k+=1    
                                        new.append([sub[k]])
                                        if sub[k+1]!=new[-1][-1]:#avoid duplicated nodes
                                            new[-1].append(sub[k+1])
                                            new[-1][-1][0]=new[-1][-1][1]                                      
                                    else:
                                        new.append([sub[0]])
                                        if sub[1]!=new[-1][-1]:#avoid duplicated nodes
                                            new[-1].append(sub[1])
                                        k+=1
                                   
                                    #rest of segments
                                    while k<len(sub)-1:
                                        if k in thisSegRem:
                                            new[-1][-1][-1]=new[-1][-1][1]#stop subpath
                                            cut=True
                                            while cut:                                           
                                                if k+1 in thisSegRem:
                                                    k+=1
                                                else:
                                                    cut=False
                                            k+=1
                                            if k<len(sub)-1:
                                                #start new subpath, start by checking that last sub did contain more than one element
                                                if len(new[-1])==1: new.pop()
                                                new.append([sub[k]])#start new subpath
                                                new[-1][-1][0]=new[-1][-1][1]
                                                if sub[k+1]!=new[-1][-1]:#avoid duplicated nodes
                                                    new[-1].append(sub[k+1])
                                                k+=1
                                        else:
                                            if sub[k+1]!=new[-1][-1]:#avoid duplicated nodes
                                                new[-1].append(sub[k+1])
                                            k+=1
                                    if keepLast:
                                        if sub[-1]!=new[-1][-1]:#avoid duplicated nodes
                                            new[-1].append(sub[-1])

                                if len(new) > 0:
                                    if len(new[-1])==1: new.pop()   
                            else:
                                new.append(sub)#add as is
                             
                            j+=1
                                                                    
                        elem.path = CubicSuperPath(new).to_path(curves_only=True)
                    i+=1

if __name__ == '__main__':
    removeDuplicateLineSegments().run()