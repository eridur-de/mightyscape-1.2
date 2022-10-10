#!/usr/bin/env python3
'''
This script reads and writes Laser Draw (LaserDRW) LYZ files.

File history:
0.1 Initial code (2/5/2017)

Copyright (C) 2017 Scorch www.scorchworks.com

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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import struct
import sys
import os
from time import time
from shutil import copyfile

##############################################################################
def show(byte_in):
    print("%03d" %ord(byte_in))


def possible_values(loc,len,type,bf):
    cur= bf.tell()
    vals=""
    if type=='d' or type=='Q' or type=='>d' or type=='>Q':
        tl=8
    elif type=='i' or  type=='f' or type=='l' or type=='L'  or type=='I':
        tl=4
    elif type=='>i' or  type=='>f' or type=='>l' or type=='>L'  or type=='>I':
        tl=4
    elif type=='h' or  type=='H' or type=='>h' or type=='>H':
        tl=2
        
    for i in range(tl):
        for j in range(i,(len-tl+1),tl):
            bf.seek(loc+j)
            vals = vals + "\t"+ str( struct.unpack(type,bf.read(tl))[0] )
        vals = vals+"\n"
    bf.seek(cur)
    return vals
##############################################################################


class LYZ_CLASS:
    def __init__(self):        
        # DEFINE HEADER FIELDS
        self.header_fields = []
        
        self.header_data = []
        self.feature_list = []
        self.left_over    = ""
        self.EOF          = ""
        
        ##########################  Description ,location,length,type,default value
        self.header_fields.append(["EXTENSION"  ,     9999999,     4, 't', ".LYZ"    ]) #0
        self.header_fields.append(["LENGTH"     ,     9999999,     4, 'i', 221       ]) #1
        self.header_fields.append(["N FEATURES" ,     9999999,     4, 'i', 0         ]) #2
        self.header_fields.append(["?A(4)"      ,     9999999,     4, 'i', 0         ]) #3
        self.header_fields.append(["CREATOR"    ,     9999999,    50, 't',"Creater: LaserDraw.exe(Lihuiyu software Co., Ltd.)"]) #4
        self.header_fields.append(["?B(14)"     ,     9999999,    14, 'z',[0,0,0,0,0,0,0,0,0,2,0,0,0,128] ]) #5
        self.header_fields.append(["DESC"       ,     9999999,    37, 't',"Description: LaserDraw Graphics File."]) #6
        self.header_fields.append(["?C(1)"      ,     9999999,     1, 'z', [0]        ]) #7
        self.header_fields.append(["?D(1)"      ,     9999999,     1, 'z', [0]        ]) #8
        self.header_fields.append(["Time(8)"    ,     9999999,     8, 'z', [0,0,0,0,0,0,0,0] ]) #9
        self.header_fields.append(["TIME(8)"    ,     9999999,     8, 'z', [0,0,0,0,0,0,0,0] ]) #10
        self.header_fields.append(["?G(8)"      ,     9999999,     4, 'z', [0,0,0,0] ]) #11
        self.header_fields.append(["?H(8)"      ,     9999999,     4, 'z', [0,0,0,0] ]) #12
        self.header_fields.append(["?I(18)"     ,     9999999,    18, 'z', [176,8,210,125,0,65,206,0,0,19,17,126,0,36,35,23,0,2] ]) #13
        self.header_fields.append(["OFFSET"     ,     9999999,     8, 'd', 0.0       ]) #14 #was 84
        self.header_fields.append(["X SIZE"     ,     9999999,     8, 'd', 42.0      ]) #15
        self.header_fields.append(["Y SIZE"     ,     9999999,     8, 'd', 42.0      ]) #16
        self.header_fields.append(["BORDER1"    ,     9999999,     8, 'd', 1.0       ]) #17
        self.header_fields.append(["BORDER2"    ,     9999999,     8, 'd', 1.0       ]) #18
        self.header_fields.append(["BORDER3"    ,     9999999,     8, 'd', 1.0       ]) #19
        self.header_fields.append(["BORDER4"    ,     9999999,     8, 'd', 1.0       ]) #20
                
        # DEFINE FEATURE FIELDS
        self.feature_fields=[]
        ##########################  Description ,location,length,type,default value
        self.feature_fields.append(["?a(4)"     ,     9999999,     4, 'i', 0                 ]) #0
        self.feature_fields.append(["SHAPE TYPE",     9999999,     1, 'b', 10                ]) #1
        #SHAPE TYPE NUMBERS
        #0, circle
        #1 square
        #2 Square Rounded Corners
        #3 Square Bevel Corners
        #4 triangle
        #5 diamond
        #8 Star
        #10 line
        #12 PNG
        #22 line text
        self.feature_fields.append(["AC Density",     9999999,     4, 'z', [75,0,0,0]        ]) #2 [ACdensity,color 0 or 8, ?,?]
        self.feature_fields.append(["?b(1)"     ,     9999999,     1, 'z', [134]             ]) #3 #solid fill 134
        self.feature_fields.append(["AC cnt"    ,     9999999,     1, 'z', [2]               ]) #4 This needs to be 2 for lines
        self.feature_fields.append(["?c(1)"     ,     9999999,     1, 'z', [0]               ]) #5 
        self.feature_fields.append(["?d(1)"     ,     9999999,     1, 'z', [6]               ]) #6
        self.feature_fields.append(["?e(3)"     ,     9999999,     3, 'z', [0  ,0  ,0  ]     ]) #7
        self.feature_fields.append(["?f(4)"     ,     9999999,     4, 'i', 16                ]) #8
        self.feature_fields.append(["ZOOM"      ,     9999999,     8, 'd', 96                ]) #9
        self.feature_fields.append(["?g(8)"     ,     9999999,     8, 'd', 0                 ]) #10
        self.feature_fields.append(["?h(8)"     ,     9999999,     8, 'd', 0                 ]) #11
        self.feature_fields.append(["?i(8)"     ,     9999999,     8, 'd', 0                 ]) #12
        self.feature_fields.append(["?j(8)"     ,     9999999,     8, 'd', 0                 ]) #13
        self.feature_fields.append(["X cent Loc",     9999999,     8, 'd', 0                 ]) #14  To the Right of the center of the laser area
        self.feature_fields.append(["Y cent Loc",     9999999,     8, 'd', 0                 ]) #15 Down from the center of the laser area
        self.feature_fields.append(["Width"     ,     9999999,     8, 'd', 0                 ]) #16
        self.feature_fields.append(["Height"    ,     9999999,     8, 'd', 0                 ]) #17
        self.feature_fields.append(["Pen Width" ,     9999999,     8, 'd', 0.025             ]) #18
        self.feature_fields.append(["AC Line"   ,     9999999,     8, 'd', 0.127             ]) #19
        self.feature_fields.append(["Rot(deg)"  ,     9999999,     8, 'd', 0                 ]) #20
        self.feature_fields.append(["Corner Rad",     9999999,     8, 'd', 0                 ]) #21
        self.feature_fields.append(["?k(8)"     ,     9999999,     8, 'd', 0                 ]) #22
        self.feature_fields.append(["?l(8)"     ,     9999999,     8, 'd', 0                 ]) #23
        self.feature_fields.append(["?m(8)"     ,     9999999,     8, 'd', 0                 ]) #24
        self.feature_fields.append(["?n(4)"     ,     9999999,     4, 'i', 4                 ]) #25
        self.feature_fields.append(["?o(4)"     ,     9999999,     4, 'i', 0                 ]) #26
        self.feature_fields.append(["?p(4)"     ,     9999999,     4, 'z', [0  ,0  ,0  ,0  ] ]) #27
        self.feature_fields.append(["?q(4)"     ,     9999999,     4, 'z', [255,255,255,0  ] ]) #28
        self.feature_fields.append(["?r(4)"     ,     9999999,     4, 'z', [0  ,0  ,0  ,0  ] ]) #29
        self.feature_fields.append(["string_len",     9999999,     4, 'i', 0                 ]) #30
        self.feature_fields.append(["filename"  ,     9999999,     4, 'x', "\000"            ]) #31
        self.feature_fields.append(["?u(4)"     ,     9999999,     4, 'z', [0  ,0  ,0  ,0  ] ]) #32
        self.feature_fields.append(["ACtexture1",     9999999,     4, 'z', [255,255,255,255] ]) #33 [0  ,0  ,0  ,0  ]
        self.feature_fields.append(["ACtexture2",     9999999,     4, 'z', [0  ,0  ,0  ,0  ] ]) #34 
        self.feature_fields.append(["?v(4)"     ,     9999999,     4, 'z', [0  ,0  ,0  ,0  ] ]) #35
        self.feature_fields.append(["?w(4)"     ,     9999999,     4, 'z', [2  ,0  ,0  ,0  ] ]) #36
        self.feature_fields.append(["data length",    9999999,     4, 'i', 2                 ]) #37 needs to be 2 for line

        self.feature_appendix = []
        for i in range(13):
            self.feature_appendix.append([])
        ## Appendix values for Line
        self.feature_appendix[10].append(["line X1",  9999999,     4, 'i', -10000 ]) #position as 1000*value
        self.feature_appendix[10].append(["line Y1",  9999999,     4, 'i', -10000 ]) #position as 1000*value
        self.feature_appendix[10].append(["line X2",  9999999,     4, 'i',  10000 ]) #position as 1000*value
        self.feature_appendix[10].append(["line Y2",  9999999,     4, 'i',  10000 ]) #position as 1000*value
        self.feature_appendix[10].append(["lineEND",  9999999,     4, 'i', 0      ]) 
        ##Appendix values for PNG
        self.feature_appendix[12].append(["PNGdata",  9999999,     0, 't', ""     ])
        self.feature_appendix[12].append(["PNGend" ,  9999999,     8, 'z', [0,0,0,0,0,0,0,0]  ])
 
 
    def lyz_read(self,loc,len,type,bf):
        #try:
        if 1==1:
            #bf.seek(loc)
            if type=='t':
                data = bf.read(len)
            elif type == 'z':
                data = []
                for i in range(len):
                    data.append(ord(bf.read(1)))
            elif type == 'x':
                data = ""
                for i in range(0,len,4):
                    data_temp = bf.read(4)
                    data = data + data_temp[0]
            else:
                data = struct.unpack(type, bf.read(len))[0]
            return data
        #except:
        #    print("Error Reading data (lyz_read)")
        #    return []        
        
        
    def lyz_write(self,data,type,bf):
        #print("type,data: ",type,data)
        if type=='t':
            #print("data:",data)
            #bf.write(data)
            try:
                bf.write(data)
            except:
                bf.write(data.encode())
        elif type == 'z':
            for i in range(len(data)):
                #bf.write(chr(data[i]))
                bf.write(struct.pack('B',data[i]))
        elif type == 'x':
            for char in data:
                bf.write(char.encode())
                bf.write(struct.pack('B',0))
                bf.write(struct.pack('B',0))
                bf.write(struct.pack('B',0))
        else:
            bf.write(struct.pack(type,data))
            
    def read_header(self,f):
        self.header_data=[]
        for line in self.header_fields:
            #pos = line[1]
            len = line[2]
            typ = line[3]
            self.header_data.append(self.lyz_read(None,len,typ,f))
    
    
    def read_feature(self,f):
        feature_data=[]
        for i in range(len(self.feature_fields)):
            length  = self.feature_fields[i][2]
            typ     = self.feature_fields[i][3]
            
            if i==31 and feature_data[1]==12:
                string_length = feature_data[-1]*4
                feature_data.append(self.lyz_read(None,string_length,typ,f))
            else:  
                feature_data.append(self.lyz_read(None,length,typ,f))
            
            #if i==30 and feature_data[1]==12:
            #    self.feature_fields[i+1][2] = feature_data[-1]*4

        
        feat_type = feature_data[1]
        if feat_type==10 or feat_type==12:
            for i in range(len(self.feature_appendix[feat_type])):
                if feat_type==12 and i==0:
                    length = feature_data[-1]
                else:
                    length = self.feature_appendix[feat_type][i][2]   
                typ    = self.feature_appendix[feat_type][i][3]
                feature_data.append(self.lyz_read(None,length,typ,f))
        return feature_data
    
    
    def setup_new_header(self):
        self.header_data=[]
        for line in self.header_fields:
            data = line[4]
            self.header_data.append(data)
            
            
    def add_line(self,x1,y1,x2,y2,Pen_Width=.025):
        feature_data=[]
        for line in self.feature_fields:
            data = line[4]
            feature_data.append(data)
        feature_data.append(int(x1*1000.0))
        feature_data.append(int(y1*1000.0))
        feature_data.append(int(x2*1000.0))
        feature_data.append(int(y2*1000.0))
        feature_data.append(0)
        feature_data[1]=10   #set type to line
        feature_data[4]=[2]  #Not sure what this is for lines but it needs to be 2
        feature_data[18]=Pen_Width
        
        self.header_data[2]=self.header_data[2]+1
        self.feature_list.append(feature_data)
    
    def add_png(self,PNG_DATA,Xsixe,Ysize):
        filename="filename"
        feature_data=[]
        for line in self.feature_fields:
            data = line[4]
            feature_data.append(data)
        feature_data.append(PNG_DATA)
        feature_data.append([0,0,0,0,0,0,0,0])
        feature_data[1]  = 12            # set type to PNG
        feature_data[3]  = [150]
        feature_data[2]  = [75, 4, 0, 144]
        feature_data[4]  = [0]           # Number of Anti-Counterfeit lines 
        feature_data[6]  = [12]          # if this is not set to [12] the image does not get passed to the engrave window
        feature_data[16] = Xsixe         # set PNG width
        feature_data[17] = Ysize         # set PNG height
        feature_data[18] = 1.0
        feature_data[26] = 16777215
        feature_data[30]= len(filename)  # set filename length
        feature_data[31]= filename       # set filename
        feature_data[33]=[0  ,0  ,0  ,0  ]
        feature_data[34]=[255,255,255,255]
        feature_data[36]=[226, 29, 5, 175]
        feature_data[37]= len(PNG_DATA)  # set PNG data length
        
        self.header_data[2]=self.header_data[2]+1
        self.feature_list.append(feature_data)
    
    def set_size(self,Xsize,Ysize):
        self.header_data[15]=Xsize
        self.header_data[16]=Ysize
        
    def set_margin(self,margin):
        self.header_data[17]=margin/2
        self.header_data[18]=margin/2
        self.header_data[19]=margin/2
        self.header_data[20]=margin/2
        
    def find_PNG(self,f):
        self.PNGstart = -1
        self.PNGend   = -1
        f.seek(0)
        loc=0
        flag = True
        while flag:
            byte=f.read(1)
            if byte=="":
                flag=False
            if byte =="P":
                if byte =="N":
                    if byte =="G":
                        self.PNGstart = f.tell()-4
            if byte =="E":
                if byte =="N":
                    if byte =="D":
                        self.PNGend = f.tell()+4
                        flag = False
        f.seek(0)
            
    
    def read_file(self, file_name):
        with open(file_name, "rb") as f:
            self.find_PNG(f)
            PNGlen = self.PNGend-self.PNGstart
            self.png_message = "PNGlen: ",PNGlen
            self.read_header(f)
            for i in range(self.header_data[2]):
                data = self.read_feature(f)
                self.feature_list.append(data)

            self.left_over = f.read( self.header_data[1]-4-f.tell() )
            
            self.EOF = ""
            byte = f.read(1)
            while byte!="":
                self.EOF=self.EOF+byte
                byte = f.read(1)
            #print(possible_values(200+217,348-200,'d',f))

            
    def write_file(self, file_name):
        with open(file_name, "wb") as f:
            for i in range(len(self.header_fields)):
                typ  = self.header_fields[i][3]
                data =  self.header_data[i]
                self.lyz_write(data,typ,f)
             
            for j in range(len(self.feature_list)):
                for i in range(len(self.feature_fields)):
                    typ  = self.feature_fields[i][3]
                    data =  self.feature_list[j][i]
                    #print(j,i," typ,data: ",typ,data)
                    self.lyz_write(data,typ,f)
                    
                feat_type=self.feature_list[j][1]
                if feat_type==10 or feat_type==12:
                    appendix_data=[]
                    for i in range(len(self.feature_appendix[feat_type])):
                        typ  = self.feature_appendix[feat_type][i][3]
                        data =  self.feature_list[j][i+len(self.feature_fields)] #appendix_data
                        #print(j,i," typ,data: "typ,data)
                        self.lyz_write(data,typ,f)
                
            f.write("@EOF".encode())
            length=f.tell()            
            f.seek(4)
            f.write(struct.pack('i',length))


    def print_header(self):
        print("\nHEADER DATA:")
        print("--------------------")
        for i in range(len(self.header_data)):
            print("%11s : " %(self.header_fields[i][0]),self.header_data[i])
        
        
    def print_features(self):
        for i in range(len(self.feature_list)):
            print("\nFEATURE #%d:" %(i+1))
            print("--------------------")
            feature = self.feature_list[i]
            for j in range(len(self.feature_fields)): 
                try:
                    print("%11s : " %(self.feature_fields[j][0]),feature[j])
                except:
                    print("error")
            feat_type = feature[1]
            if feat_type==10 or feat_type==12:
                print("---LINE COORDS---")
                for j in range(len(self.feature_appendix[feat_type])):
                    jj = j+len(self.feature_fields)
                    if feat_type==12 and jj==38:
                        print("%11s : " %(self.feature_appendix[feat_type][j][0]),"....")
                    else:
                        print("%11s : " %(self.feature_appendix[feat_type][j][0]),feature[jj])
        print("--------------------")


    
if __name__ == "__main__":
    ###############################
    try:
        file_name = sys.argv[1]
        print("input:  ",file_name)
    except:
        file_name = ""
    ###############################
    try:
        file_out = sys.argv[2]
        print("output: ",file_name)
    except:
        file_out = ""
    ###############################

    if file_name=="test":
        LYZ=LYZ_CLASS()
        LYZ.setup_new_header()
        #image_file = "squigles.png"
        #image_file = "drawing_mod.png"
        image_file = "temp.png"
        with open(image_file, 'rb') as f:
            PNG_DATA = f.read()
        LYZ.add_png(PNG_DATA,20,20)
        
        LYZ.add_line(5,5,-10,-10,0.025)
        #LYZ.print_header()
        #LYZ.print_features()
        LYZ.write_file("test.lyz")
    else:
        if file_name!="":
            LYZ=LYZ_CLASS()
            LYZ.read_file(file_name)
            LYZ.print_header()
            LYZ.print_features()
            print("LEFTOVER    :", LYZ.left_over)
            print("EOF         :",LYZ.EOF)
        
        if file_out!="":
            LYZ.write_file(file_out)