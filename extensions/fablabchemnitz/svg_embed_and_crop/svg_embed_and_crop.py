import inkex
import subprocess
import os
from lxml import etree
from inkex import command

class EmbedAndCrop(inkex.EffectExtension):

	'''
	This extension does not work for embedded images, but only for linked ones
	'''

	def effect(self):
		
		cp = os.path.dirname(os.path.abspath(__file__)) + "/svg_embed_and_crop/*"
		output_file = self.options.input_file + ".cropped"
		
		cmd = 'java -cp "' + cp + '" "edu.emory.cellbio.svg.EmbedAndCropInkscapeEntry" "' + self.options.input_file + '" -o "' + output_file + '"'
		with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
			proc.wait()
			stdout, stderr = proc.communicate()
			if stderr.decode('utf-8') != "":
				inkex.utils.debug(stderr.decode('utf-8'))
		#cli_output = command.call('java', '-cp', cp, 'edu.emory.cellbio.svg.EmbedAndCropInkscapeEntry', self.options.input_file, "-o", output_file)
		#if len(cli_output) > 0:
		#	self.debug(_("Inkscape extension returned the following output:"))
		#	self.debug(cli_output)

		if not os.path.exists(output_file):
			raise inkex.AbortExtension("Plugin cancelled")
		stream = open(output_file, 'r')
		p = etree.XMLParser(huge_tree=True)
		doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
		stream.close()
		root = self.document.getroot()
		kept = [] #required. if we delete them directly without adding new defs or namedview, inkscape will crash
		for node in self.document.xpath('//*', namespaces=inkex.NSS):
			if node.TAG not in ('svg', 'defs', 'namedview'):
				node.delete()
			elif node.TAG in ('defs', 'namedview'): #except 'svg'
				kept.append(node)
		
		children = doc.getroot().getchildren()
		for child in children:
		   root.append(child)
		for k in kept:
			k.delete()

if __name__ == '__main__':
	EmbedAndCrop().run()