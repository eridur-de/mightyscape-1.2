#!/usr/bin/env python3

import inkex
import copy

class bluePrintMakerData():
	def __init__(self,effect):
		self.effect=effect
		self.stroke_units=effect.options.stroke_units
		self.unit_factor=1.0
		self.set_units()
		self.stroke_width=effect.options.stroke_width*self.unit_factor
		self.palette=effect.options.palette
		self.background_color=None
		self.stroke_color=None
		self.set_colors()
		self.selected_nodes=[]
		if len(effect.options.ids)==0:
			self.selected_nodes=[effect.svg.getElementById(x) for x in effect.svg.get_ids()]
			self.selected_nodes=[node for node in self.selected_nodes if effect.is_geometry(node)]
		else:
			self.selected_nodes=[y for x,y in effect.svg.selected.items()]
			self.selected_nodes=[node for node in self.selected_nodes if effect.is_geometry(node,shapes=['path','g','rect','ellipse','perspective'])]
		self.allowed_ids=[]
		self.allowed_nodes=[]
		self.set_objects()
	
	def set_units(self):
		if self.stroke_units=='millimeters':
			self.unit_factor=3.543
		if self.stroke_units=='centimeters':
			self.unit_factor=35.433
		if self.stroke_units=='points':
			self.unit_factor=1.25
		if self.stroke_units=='pixels':
			self.unit_factor=1.0
	
	def set_colors(self):
		if self.palette=='blueprint':
			self.background_color='#006fde'
			self.stroke_color='#ffffff'
		if self.palette=='black':
			self.background_color='#000000'
			self.stroke_color='#ffffff'
		if self.palette=='white':
			self.background_color='#ffffff'
			self.stroke_color='#000000'
		if self.palette=='laser':
			self.background_color='#ffffff'
			self.stroke_color='#ff0000'
	
	def set_objects(self):
		for current_id in self.effect.svg.get_ids():
			node=self.effect.svg.getElementById(current_id)
			if self.effect.is_geometry(node):
				self.allowed_ids.append(current_id)
				self.allowed_nodes.append(node)

class BluePrintMaker(inkex.EffectExtension):
	
	def __init__(self):
		inkex.Effect.__init__(self)
		self.arg_parser.add_argument('-p', '--palette', help='Choose the colors...')
		self.arg_parser.add_argument('-s', '--stroke_width', type=float, help='Stroke size...')
		self.arg_parser.add_argument('-u', '--stroke_units', help='Choose the units...')
		self.data=None
	
	def is_a_group(self, node):
		data=False
		if node.tag==inkex.addNS('g','svg'):
			data=True
		return data
	
	def is_geometry(self, node, shapes=['path','rect','ellipse','perspective']):
		data=False
		for s in shapes:
			if node.tag==inkex.addNS(s,'svg'):
				data=True
		return data
	
	def change_page_settings(self):
		namedview=self.svg.namedview
		namedview.set('pagecolor',self.data.background_color)
		namedview.set(inkex.addNS('pageopacity', 'inkscape'),'1')
		namedview.set(inkex.addNS('pageshadow', 'inkscape'),'0')
		namedview.set('bordercolor',self.data.stroke_color)
		namedview.set('borderopacity','1')
		return None
	
	def change_this_object(self,node):
		styles=dict(inkex.Style.parse_str(node.get('style')))
		styles_copy=copy.deepcopy(styles)
		styles_copy['stroke']=self.data.stroke_color
		styles_copy['stroke-width']=self.data.stroke_width
		styles_copy['stroke-opacity']='1'
		styles_copy['fill']='none'
		styles_copy['fill-opacity']='1'
		styles_copy['opacity']='1'
		node.set('style',str(inkex.Style(styles_copy)))
		return None
	
	def iterate_on_objects(self,node=None):
		if self.is_geometry(node):
			self.change_this_object(node)
		if self.is_a_group(node):
			for current_node in list(node):
				self.iterate_on_objects(current_node)
	
	def effect(self):
		self.data=bluePrintMakerData(self)
		self.change_page_settings()
		for node in self.data.selected_nodes:
			self.iterate_on_objects(node)
		return None

if __name__ == '__main__':
	BluePrintMaker().run()