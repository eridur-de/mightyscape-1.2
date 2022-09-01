#!/usr/bin/env python3
# Distributed under the terms of the GNU Lesser General Public License v3.0
### Author: Neon22 - github 2016

### fret scale calculation code

from math import log, floor

def fret_calc_ratio(length, howmany, ratio):
	" given the ratio between notes, calc distance between frets "
	# typically 18, 17.817, 17.835 for equal temperment scales
	distances = []
	prev = 0
	for i in range(howmany):
		distance = length / ratio
		distances.append(prev+distance)
		length -= distance
		prev += distance
		# print "%02d  %6.4f  %s" %(i, prev, distance)
	return distances

def fret_calc_root2(length, howmany, numtones=12):
	" using Nroot2 method, calc distance between frets "
	distances = []
	for i in range(howmany):
		# Calculating Fret Spacing for a Single Fret
		# d = s-(s/ (2^ (n/12)))
		distance = length - (length / (pow(2, (i+1)/(float(numtones))) ))
		distances.append(distance)
		# print "%02d  %6.4f" %(i, distance)
	return distances

def fret_calc_scala(length, howmany, scala_notes):
	" use ratios from scala file, calc distance between frets "
	distances = []
	for i in range(howmany):
		if i < len(scala_notes):
			r = scala_notes[i]
		else:
			end = pow(scala_notes[-1], int(i / float(len(scala_notes))))
			r = end * scala_notes[i%len(scala_notes)]
		distance = length - (length / r)
		distances.append(distance)
	return distances

def cents_to_ratio(cents):
	" given a value in cents, calculate the ratio "
	return pow(2, cents / 1200.0)

def parse_scala(scala, filename, verbose=True):
	""" Parse the readlines() from scala file into:
		- description, numnotes, 
		- lists of pretty ratios, numeric ratios
	"""
	description = ""
	numnotes = 0
	notes = []
	ratios = []
	error = False
	# print scala
	for line in scala:
		try:
			# take out leading and trailing spaces - get everything up to first space if exists
			line = line.strip() # hold onto this for when we need the description
			first = line.split()[0] # first element in the line
			# print line
			if first and first[0] != "!": # ignore all blank and comment lines
				if not description:
					# expecting description line first
					# may contain unprintable characters - force into unicode
					description = unicode(line, errors='ignore')
				elif numnotes == 0:
					# expecting notes count after description
					numnotes = int(first)
				else: # expecting sequences of notes
					notes.append(first) # for later ref
					# remove comments at end of line if exist
					if first.count("!") > 0:
						first = first[:first.find("!")]
					if first.find('.') > -1: # cents
						ratios.append(cents_to_ratio(float(first)))
					elif first.find("/") > -1: # ratio
						num, denom = first.split('/')
						ratios.append(int(num)/float(denom))
					else:
						ratios.append(int(first))
		except:
			error = "ERROR: Failed to load "+filename
	#
	if verbose:
		print ("Found:", description)
		print ("",numnotes, "notes found.")
		for n,r in zip(notes,ratios):
			print (" %4.4f : %s"%(r, n))
		print (" check: indicated=found : %d=%d"%(numnotes,len(notes)))
	if error:
		return [error, numnotes, notes, ratios]
	else:
		return [description, numnotes, notes, ratios]

def read_scala(filename, verbose=False):
	" read and parse scala file into interval ratios "
	try:
		inf = open(filename, 'rB')
		content = inf.readlines()
		inf.close()
		flag = verbose
		# if filename.find("dyadic") > -1: flag = True
		return parse_scala(content, filename, flag)
	except:
		return ["ERROR: Failed to load "+filename, 2, [1], [1.01]]

		
### frequency to note
def log_note(freq):
	" find the octave the note is in "
	octave = (log(freq) - log(261.626)) / log (2) + 4.0
	return octave

def freq_to_note(freq):
	lnote = log_note(freq)
	octave = floor(lnote)
	cents = 1200 * (lnote - octave)
	notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
	offset = 50.0
	x = 1
	if cents < 50:
		note = "C"
	elif cents >= 1150:
		note = "C"
		cents -= 1200
		octave += 1
	else:
		for j in range(1,12):
			if offset <= cents < (offset + 100):
				note = notes[x]
				cents -= (j * 100)
				break
			offset += 100
			x += 1
	return "%s%d"%(note, int(octave)), "%4.2f"%(cents)


def int_or_float(value):
	" true if value is an int or a float "
	return type(value) == type(1) or type(value) == type(1.0)


### class to hold info about instrument necks
class Neck(object):
	def __init__(self, length, strings=['G','C','E','A'], units='in', spacing=0.4, fret_width=1.5):
		" "
		# coerce single spacing value into a list of nut/bridge spacing
		self.set_spacing(spacing)
		# same for fret_width
		self.set_width(fret_width)
		#
		self.length = length
		self.strings = strings
		self.units = units
		self.frets = [] # Treble side frets if fanned
		self.bass_frets =[]
		self.fanned = False
		self.bass_scale = 0
		self.fanned_vertical = False
		self.method = '12root2'
		self.notes_in_scale = False
		# Scala
		self.scala = False
		self.description = False
		self.scala_notes = False
		self.scala_ratios = False
	def __repr__(self):
		extra = ""
		if len(self.frets)>0:
			extra += "%d frets"%(len(self.frets))
		if self.method == 'scala':
			extra += "(%s)" %(self.scala.split('/')[-1]) # filename
		return "<Neck: %s -%4.2f(%s) %s %d strings>"%(self.method, self.length, self.units, extra, len(self.strings))

	def set_width(self, fret_width):
		" get both values from this "
		if int_or_float(fret_width):
			fret_width = [fret_width,fret_width]
		elif type(fret_width) != type([]):
			fret_width = [1,1]
		self.nut_width = fret_width[0]
		self.bridge_width = fret_width[1]

	def set_spacing(self, spacing):
		" get both values from this "
		if int_or_float(spacing):
			spacing = [spacing,spacing]
		elif type(spacing) != type([]):
			spacing = [1,1]
		self.nut_spacing = spacing[0]
		self.bridge_spacing = spacing[1]

	def set_fanned(self, bass_scale, vertical_fret):
		""" keep existing treble calc and create Bass calc
			- must have called calc_fret_offsets() before
			  (so notes_in_scale is set)
		"""
		# adjust the position of the treble side if required.
		# calc fret_offset and if treble or bass side needs to be moved
		# if treble - move self.frets
		# if bass, add offset as calculated
		treble = self.frets
		# print treble
		if self.method == 'scala':
			bass = self.calc_fret_offsets(bass_scale, len(self.frets), method=self.method, scala_filename=self.scala)
		else:
			bass = self.calc_fret_offsets(bass_scale, len(self.frets), method=self.method, numtones=self.notes_in_scale)
		offset = 0 if vertical_fret ==0 else bass[vertical_fret - 1] - treble[vertical_fret - 1]
		# print "offset", offset, "bass",bass
		if offset > 0:
			# shift treble
			for i in range(len(treble)):
				treble[i] += offset
		else: # shift bass
			for i in range(len(bass)):
				bass[i] -= offset
		self.frets = treble
		self.bass_frets = bass
		self.bass_scale = bass_scale
		self.fanned_vertical = vertical_fret
		self.fan_offset = offset
		self.fanned = True
		return offset

	def find_mid_point(self, fret_index, width_offset):
		""" find midpoint of fret, fret-1 along neck
			and ///y width where width_offset=0 means center of neck
		"""
		y_factor = (width_offset + self.nut_width/2) / float(self.nut_width)
		# assume fanned
		tpos_f1 = self.frets[fret_index]
		bpos_f1 = tpos_f1 if not self.fanned else self.bass_frets[fret_index]
		if self.fanned:
			if self.fan_offset >= 0:
				tpos_f0 = self.fan_offset if fret_index<=1 else self.frets[fret_index-1]
				bpos_f0 = 0 if fret_index<=1 else self.bass_frets[fret_index-1]
			else:
				bpos_f0 = -self.fan_offset if fret_index<=1 else self.bass_frets[fret_index-1]
				tpos_f0 = 0 if fret_index<=1 else self.frets[fret_index-1]
		else:
			tpos_f0 = 0 if fret_index<=1 else self.frets[fret_index-1]
			bpos_f0 = 0 if fret_index<=1 else tpos_f0
		#
		mid_tpos = tpos_f0 + (tpos_f1 - tpos_f0)/2
		mid_bpos = bpos_f0 + (bpos_f1 - bpos_f0)/2
		# print fret_index, y_factor
		# print " %4.2f %4.2f %4.2f"% (tpos_f0, tpos_f1, mid_tpos)
		# print " %4.2f %4.2f %4.2f"% (bpos_f0, bpos_f1, mid_bpos)
		# the mid_xx positions are self.nut_width apart
		return [mid_tpos + (mid_bpos-mid_tpos)*y_factor, width_offset/self.nut_width*1.5]

	def calc_fret_offsets(self, length, howmany, method='12root2', numtones=12, scala_filename=False):
		" calc fret positions from Nut for all methods "
		frets = False # store them in here
		if scala_filename:
			scala_notes = read_scala(scala_filename)
			self.method = 'scala'
			self.scala = scala_filename
			self.description = scala_notes[0]
			self.scala_notes = scala_notes[2]
			self.scala_ratios = scala_notes[3] # [-1]
			frets = fret_calc_scala(length, howmany, self.scala_ratios)
			self.notes_in_scale = len(self.scala_ratios)
		elif method.find('root2') > -1:
			self.method = method
			frets = fret_calc_root2(length, howmany, numtones)
			self.notes_in_scale = numtones
		elif method == '18':
			self.method = method
			ratio = 18
			frets = fret_calc_ratio(length, howmany, ratio)
			self.notes_in_scale = 12
		elif method == '17.817':
			self.method = method
			ratio = 17.81715374510580
			frets = fret_calc_ratio(length, howmany, ratio)
			self.notes_in_scale = 12
		elif method == '17.835':
			self.method = method
			ratio = 17.835
			frets = fret_calc_ratio(length, howmany, ratio)
			self.notes_in_scale = 12
		# update the iv
		self.frets = frets
		return frets

	def show_frets(self):
		" pretty print "
		for i,d in enumerate(self.frets):
			print ("%2d: %4.4f" %(i+1,d))
		if self.bass_frets:
			for i,d in enumerate(self.bass_frets):
				print ("%2d: %4.4f" %(i+1,d))

	def compare_methods(self, howmany, verbose=True):
		" show differences in length for the main methods (not scala) "
		distances = []
		differences = []
		methods = ['12root2', '18', '17.817', '17.835']
		n = Neck(30) # long one to maximise errors
		for method in methods:
			distances.append(n.calc_fret_offsets(n.length, howmany, method))
			# print distances[-1]
		for i in range(1, len(methods)):
			differences.append( [a-b for (a,b) in zip(distances[0], distances[i])] )
		if verbose:
			print("Differences from 12root2")
			for i,m in enumerate(methods[1:]):
				print ("\nMethod = %s\n  " %(m))
				for d in differences[i]:
					print ("%2.3f " %(d))
			print("")
		# package
		combined = []
		for i,m in enumerate(methods[1:]):
			combined.append([m, max(differences[i]), differences[i]])
		return combined

# Gibson "rule of 18" base scale is in sys 18. 
# Martin 24.9 (24.84), 25.4 (act 25.34) rough approx and round up. not actually the scale length
# The difference between 17.817 and 17.835 came from rounding early and carrying the roundoff error through the rest of the work.
# where r = twelfth root of two and put the first fret where it would make the sounding length of the string 1/r of its original length 


### tests
if __name__ == "__main__":
	n = Neck(24)
	f = n.calc_fret_offsets(n.length, 12, '12root2')
	n.show_frets()
	print (n)
	errors = n.compare_methods(22, False)
	for m,e,d in errors:
		print ("for method '%s': max difference from 12Root2 = %4.3f%s (on highest fret)"%(m,e, n.units))
	#
	n = Neck(24)
	f = n.calc_fret_offsets(n.length, 22, 'scala', scala_filename='scales/diat_chrom.scl')
	n.show_frets()
	print ("Fanning")
	# n.set_fanned(25,0)
	# n.show_frets()
	# print n
	# print n.description
	# print n.scala
	# print n.scala_notes
	# print n.scala_ratios

	# similar to scale=10 to scale = 9.94 but slightly diff neaer the nut.

	# scala_notes = read_scala("scales/alembert2.scl")#, True)
	# print "Notes=",len(scala_notes[-1]), scala_notes[1]
	# for d in fret_calc_scala(24, scala_notes[-1]): print d

	# test load all scala files
	# import os
	# probable_dir = "scales/"
	# files = os.listdir(probable_dir)
	# for f in files:
		# fname = probable_dir+f
		# # print f
		# data = read_scala(fname)
		# # print "     ",data[0]
		# if data[0][:5] == "ERROR":
			# print "!!!!    ERROR",fname

	## freq conversion
	print("")
	for f in [440,443,456,457, 500,777, 1086]:
		print (f, freq_to_note(f))

	## fanned frets
	# print
	# for f in [1,11]:
		# print n.find_mid_point(f,-0.75) 

	# get to this eventually
	string_compensation = [
		0.0086, 0.0119,  0.0107, 0.0124, 0.0151, 0.0175, 0.020, 0.0222, 0.0244, 0.0263,
		0.0282, 0.030, 0.0371, 0.4235
		]

### Optionally:
# how many strings, 
# (associated sequence of intervals)


### refs:
#http://fretfocus.anastigmatix.net/
#http://windworld.com/features/tools-resources/exmis-fret-placement-calculator/
#http://www.huygens-fokker.org/scala/

# superstart:
# notes on the fretboard
#  https://www.youtube.com/watch?v=-jW1Xx0t3ZI