#!/usr/bin/env python3

"""
Extension for InkScape 1.0
Features
 - filters the current selection or the whole document for fill or stroke style. Each style will be put onto it's own layer. This way you can devide elements by their colors.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.08.2020
Last patch: 17.10.2021
License: GNU GPL v3
"""
import inkex
import re
import sys
from lxml import etree
import math
from operator import itemgetter
from inkex.colors import Color

sys.path.append("../remove_empty_groups")
sys.path.append("../apply_transformations")

class StylesToLayers(inkex.EffectExtension):

    def findLayer(self, layerName):
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        for layer in svg_layers:
            #self.msg(str(layer.get('inkscape:label')) + " == " + layerName)
            if layer.get('inkscape:label') == layerName:
                return layer
        return None

    def createLayer(self, layerNodeList, layerName):
        svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]
        for layer in layerNodeList:
            #self.msg(str(layer[0].get('inkscape:label')) + " == " + layerName)
            if layer[0].get('inkscape:label') == layerName:
                return layer[0] #already exists. Do not create duplicate
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), '%s' % layerName)
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return layer
        
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        pars.add_argument("--separateby", default = "stroke", help = "Separate by")
        pars.add_argument("--sortcolorby", default = "hexval", help = "Sort colors by")
        pars.add_argument("--subdividethreshold", type=int, default = 1, help = "Threshold for splitting into sub layers")
        pars.add_argument("--decimals", type=int, default = 1, help = "Decimal tolerance")
        pars.add_argument("--cleanup", type=inkex.Boolean, default = True, help = "Cleanup all unused groups/layers (requires separate extension)")
        pars.add_argument("--put_unfiltered", type=inkex.Boolean, default = False, help = "Put unfiltered elements to a separate layer")  
        pars.add_argument("--show_info", type=inkex.Boolean, default = False, help = "Show elements which have no style attributes to filter")

    def effect(self):
    
        def colorsort(stroke_value): #this function applies to stroke or fill (hex colors)
            if self.options.sortcolorby == "hexval":
                return float(int(stroke_value[1:], 16))
            elif self.options.sortcolorby == "hue":
                return float(Color(stroke_value).to_hsl()[0])
            elif self.options.sortcolorby == "saturation":
                return float(Color(stroke_value).to_hsl()[1])
            elif self.options.sortcolorby == "luminance":
                return float(Color(stroke_value).to_hsl()[2])
            return None
    
        applyTransformationsAvailable = False # at first we apply external extension
        try:
            import apply_transformations
            applyTransformationsAvailable = True
        except Exception as e:
            # self.msg(e)
            self.msg("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")
             
        layer_name = None
        layerNodeList = [] #list with layer, neutral_value, element and self.options.separateby type
        selected = [] #list of items to parse
        
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter("*"):
                selected.append(element)
        else:
            selected = self.svg.selected.values()

        for element in selected:
        
            # additional option to apply transformations. As we clear up some groups to form new layers, we might lose translations, rotations, etc.
            if self.options.apply_transformations is True and applyTransformationsAvailable is True:
                apply_transformations.ApplyTransformations().recursiveFuseTransform(element) 
        
            if isinstance(element, inkex.ShapeElement): # Elements which have a visible representation on the canvas (even without a style attribute but by their type); if we do not use that ifInstance Filter we provokate unkown InkScape fatal crashes
                           
                style = element.style
                if style is not None:
                    #if no style attributes or stroke/fill are set as extra attribute
                    stroke         = element.get('stroke')
                    stroke_width   = element.get('stroke-width')
                    stroke_opacity = element.get('stroke-opacity')
                    fill           = element.get('fill')
                    fill_opacity   = element.get('fill-opacity')
                    
                    # possible values for fill are #HEXCOLOR (like #000000), color name (like purple, black, red) or gradients (URLs)
        
                    neutral_value = None #we will use this value to slice the filter result into sub layers (threshold)
                   
                    if fill is not None:
                        style['fill'] = fill
                    if stroke is not None:    
                        style['stroke'] = stroke
                        
                    #we don't want to destroy elements with gradients (they contain svg:stop elements which have a style too) and we don't want to mess with tspans (text)
                    #the Styles to Layers extension still might brick the gradients (some tests failed)
                    if style and element.tag != inkex.addNS('stop','svg') and element.tag != inkex.addNS('tspan','svg'): 
                        
                        if self.options.separateby == "element_tag":
                            neutral_value = 1
                            layer_name = "element_tag-" + element.tag.replace("{http://www.w3.org/2000/svg}", "")
                                      
                        elif self.options.separateby == "stroke":
                            stroke = style.get('stroke')
                            if stroke is not None and stroke != "none":
                                    stroke_converted = str(Color(stroke).to_rgb()) #the color can be hex code or clear name. we handle both the same
                                    neutral_value = colorsort(stroke_converted)
                                    layer_name = "stroke-{}-{}".format(self.options.sortcolorby, stroke_converted)
                            else:
                                layer_name = "stroke-{}-none".format(self.options.sortcolorby)
                                
                        elif self.options.separateby == "stroke_width":        
                            stroke_width = style.get('stroke-width')
                            if stroke_width is not None:
                                neutral_value = self.svg.unittouu(stroke_width)
                                layer_name = "stroke-width-{}".format(neutral_value)
                            else:
                                layer_name = "stroke-width-none"
                                
                        elif self.options.separateby == "stroke_hairline":        
                            inkscape_stroke = style.get('-inkscape-stroke')
                            if inkscape_stroke is not None and inkscape_stroke == "hairline":
                                neutral_value = 1
                                layer_name = "stroke-hairline-yes"
                            else:
                                neutral_value = 0
                                layer_name = "stroke-hairline-no"
                                
                        elif self.options.separateby == "stroke_opacity":
                            stroke_opacity = style.get('stroke-opacity')
                            if stroke_opacity is not None:
                                neutral_value = float(stroke_opacity)
                                layer_name = "stroke-opacity-{}".format(neutral_value)
                            else:
                                layer_name = "stroke-opacity-none"
                                
                        elif self.options.separateby == "fill":
                            fill = style.get('fill')
                            if fill is not None:
                                #check if the fill color is a real color or a gradient. if it's a gradient we skip the element
                                if fill != "none" and "url" not in fill:
                                    fill_converted = str(Color(fill).to_rgb()) #the color can be hex code or clear name. we handle both the same
                                    neutral_value = colorsort(fill_converted)
                                    layer_name = "fill-{}-{}".format(self.options.sortcolorby,fill_converted)
                                elif "url" in fill: #okay we found a gradient. we put it to some group
                                    layer_name = "fill-{}-gradient".format(self.options.sortcolorby)
                                else: #none
                                    layer_name = "fill-" + self.options.sortcolorby + "-none" 
                            else:
                                layer_name = "fill-" + self.options.sortcolorby + "-none"
                                
                        elif self.options.separateby == "fill_opacity":
                            fill_opacity = style.get('fill-opacity')           
                            if fill_opacity is not None:
                                neutral_value = float(fill_opacity)
                                layer_name = "fill-opacity-{}".format(neutral_value)
                            else:
                                layer_name = "fill-opacity-none"
                                
                        else:
                            self.msg("No proper option selected.")
                            exit(1)
                                                       
                        if neutral_value is not None: #apply decimals filter
                            neutral_value = float(round(neutral_value, self.options.decimals))
                        if layer_name is not None:
                            layer_name = layer_name.split(";")[0] #cut off existing semicolons to avoid duplicated layers with/without semicolon
                            currentLayer = self.findLayer(layer_name)
                            if currentLayer is None: #layer does not exist, so create a new one
                                layerNodeList.append([self.createLayer(layerNodeList, layer_name), neutral_value, element, self.options.separateby])
                            else:
                                layerNodeList.append([currentLayer, neutral_value, element, self.options.separateby]) #layer is existent. append items to this later
                        elif layer_name is None and self.options.put_unfiltered:
                            layer_name = 'without-' + self.options.separateby + '-in-style-attribute'
                else: #if no style attribute in element and not a group
                    if isinstance(element, inkex.Group) is False:
                        if self.options.show_info:
                            self.msg(element.get('id') + ' has no style attribute')
                        if self.options.put_unfiltered:
                                layer_name = 'without-style-attribute'
                                currentLayer = self.findLayer(layer_name)

                                if currentLayer is None: #layer does not exist, so create a new one
                                    layerNodeList.append([self.createLayer(layerNodeList, layer_name), None, element, None])
                                else:
                                    layerNodeList.append([currentLayer, None, element, None]) #layer is existent. append items to this later

        contentlength = 0 #some counter to track if there are layers inside or if it is just a list with empty children
        for layerNode in layerNodeList:
            try: #some nasty workaround. Make better code
                layerNode[0].append(layerNode[2]) #append element to created layer           
                if layerNode[1] is not None: contentlength += 1 #for each found layer we increment +1
            except:
                continue
          
        # we do some cosmetics with layers. Sometimes it can happen that one layer includes another. We don't want that. We move all layers to the top level
        for newLayerNode in layerNodeList:
            self.document.getroot().append(newLayerNode[0])  
          
        # Additionally if threshold was defined re-arrange the previously created layers by putting them into sub layers        
        if self.options.subdividethreshold > 1 and contentlength > 0: #check if we need to subdivide and if there are items we could rearrange into sub layers
            
            #disabled sorting because it can return NoneType values which will kill the algorithm
            #layerNodeList.sort(key=itemgetter(1)) #sort by neutral values from min to max to put them with ease into parent layers
            
            topLevelLayerNodeList = [] #list with new layers and sub layers (mapping)
            minmax_range = []
            for layerNode in layerNodeList:
                if layerNode[1] is not None: 
                   if layerNode[1] not in minmax_range: 
                       minmax_range.append(layerNode[1]) #get neutral_value
      
            if len(minmax_range) >= 3: #if there are less than 3 distinct values a sub-layering will make no sense
                #adjust the subdividethreshold if there are less layers than division threshold value dictates
                if len(minmax_range) - 1 < self.options.subdividethreshold:
                    self.options.subdividethreshold = len(minmax_range)-1
                #calculate the sub layer slices (sub ranges)
                minval = min(minmax_range)
                maxval = max(minmax_range)
                sliceinterval = (maxval - minval) / self.options.subdividethreshold
        
                #self.msg("neutral values (sorted) = " + str(minmax_range))
                #self.msg("min neutral_value = " + str(minval))
                #self.msg("max neutral_value = " + str(maxval))
                #self.msg("slice value (divide step size) = " + str(sliceinterval))
                #self.msg("subdivides (parent layers) = " + str(self.options.subdividethreshold))
             
                for layerNode in layerNodeList:
                    for x in range(0, self.options.subdividethreshold): #loop through the sorted neutral_values and determine to which layer they should belong

                        if layerNode[1] is None:
                            layer_name = str(layerNode[3]) + "#parent:unfilterable"
                            currentLayer = self.findLayer(layer_name)
                            if currentLayer is None: #layer does not exist, so create a new one
                                topLevelLayerNodeList.append([self.createLayer(topLevelLayerNodeList, layer_name), layerNode[0]])
                            else:
                                topLevelLayerNodeList.append([currentLayer, layerNode[0]]) #layer is existent. append items to this later
                            break
                        else:
                            layer_name = str(layerNode[3]) + "#parent" + str(x+1)
                            currentLayer = self.findLayer(layer_name)    
                            #value example for arranging:
                            #min neutral_value = 0.07
                            #max neutral_value = 2.50
                            #slice value = 0.81
                            #subdivides = 3
                            #
                            #that finally should generate:
                            #    layer #1: (from 0.07) to (0.07 + 0.81 = 0.88)
                            #    layer #2: (from 0.88) to (0.88 + 0.81 = 1.69)
                            #    layer #3: (from 1.69) to (1.69 + 0.81 = 2.50)
                            #
                            #now check layerNode[1] (neutral_value) and sort it into the correct layer  
                            if (layerNode[1] >= minval + sliceinterval * x) and (layerNode[1] <= minval + sliceinterval + sliceinterval * x):
                                if currentLayer is None: #layer does not exist, so create a new one
                                    topLevelLayerNodeList.append([self.createLayer(topLevelLayerNodeList, layer_name), layerNode[0]])
                                else:
                                    topLevelLayerNodeList.append([currentLayer, layerNode[0]]) #layer is existent. append items to this later
                                break
                            
                #finally append the sublayers to the slices
                #for layer in topLevelLayerNodeList:
                    #self.msg(layer[0].get('inkscape:label'))
                    #self.msg(layer[1])
                for newLayerNode in topLevelLayerNodeList:            
                    newLayerNode[0].append(newLayerNode[1]) #append newlayer to layer     
        
        #clean all empty layers from node list. Please note that the following remove_empty_groups 
        #call does not apply for this so we need to do it as PREVIOUS step before!
        for i in range(0, len(layerNodeList)):
            deletes = []
            for j in range(0, len(layerNodeList[i][0])):
                if len(layerNodeList[i][0][j]) == 0 and isinstance(layerNodeList[i][0][j], inkex.Group):
                    deletes.append(layerNodeList[i][0][j])
            for delete in deletes:
                    delete.getparent().remove(delete)
            if len(layerNodeList[i][0]) == 0:
                if layerNodeList[i][0].getparent() is not None:
                    layerNodeList[i][0].getparent().remove(layerNodeList[i][0])
        
        if self.options.cleanup == True:
            try:
                import remove_empty_groups
                remove_empty_groups.RemoveEmptyGroups.effect(self)
            except:
                self.msg("Calling 'Remove Empty Groups' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping ...")
                
if __name__ == '__main__':
    StylesToLayers().run()