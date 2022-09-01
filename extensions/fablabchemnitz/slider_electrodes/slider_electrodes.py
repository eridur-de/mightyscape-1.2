#!/usr/bin/env python3
from io import StringIO
import inkex
from lxml import etree

class SliderElectrodes(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument("-c", "--count", type=int, default=5, help="Number of electrodes")
		pars.add_argument("-s", "--spikes", type=int, default=5, help="Number of spikes")

	def genPathString(self, bounds, spikeWidth, first=False, last=False):
		s = StringIO()
		cx = bounds[0]
		cy = bounds[1]
		stepx = spikeWidth
		stepy = (bounds[3] - bounds[1]) / (2.0 * self.options.spikes)
		s.write(" M %f, %f " % (bounds[0], bounds[1]))
		if first:
			s.write(" L %f, %f " % (bounds[0], bounds[3]))
		else:
			for i in range(self.options.spikes):
				s.write(" L %f, %f " % (bounds[0] + stepx, bounds[1] + (2 * i + 1) * stepy))
				s.write(" L %f, %f " % (bounds[0], bounds[1] + (2 * i + 2) * stepy))
		if last:
			s.write(" L %f, %f " % (bounds[2], bounds[3]))
			s.write(" L %f, %f " % (bounds[2], bounds[1]))
		else:
			s.write(" L %f, %f " % (bounds[2] - stepx, bounds[3]))
			for i in range(self.options.spikes):
				s.write(" L %f, %f " % (bounds[2], bounds[3] - (2 * i + 1) * stepy))
				s.write(" L %f, %f " % (bounds[2] - stepx, bounds[3] - (2 * i + 2) * stepy))
		s.write(" Z ")
		return s.getvalue()
		
	def effect(self):
		svg = self.document.getroot()
		width = self.svg.unittouu(self.document.getroot().get('width'))
		height = self.svg.unittouu(self.document.getroot().get('height'))
		
		group = etree.SubElement(self.svg.get_current_layer(), 'g', {inkex.addNS('label', 'inkscape') : 'Slider electrodes'})
		
		eWidth = width / self.options.count
		spikeWidth = 0.6 * eWidth
		
		for eid in range(self.options.count):
			if eid == 0:
				path = self.genPathString((eid * eWidth, 0, (eid + 1) * eWidth + 0.4 * spikeWidth, height), spikeWidth, first=True)
			elif eid == self.options.count - 1:
				path = self.genPathString((eid * eWidth - 0.4 * spikeWidth, 0, (eid + 1) * eWidth, height), spikeWidth, last=True)
			else:
				path = self.genPathString((eid * eWidth - 0.4 * spikeWidth, 0, (eid + 1) * eWidth + 0.4 * spikeWidth, height), spikeWidth)
			e = etree.SubElement(group, inkex.addNS('path', 'svg'), {'style':str(inkex.Style({'stroke':'none','fill'	:'#000000'})),'d' : path})
			
if __name__ == '__main__':
	effect = SliderElectrodes().run()