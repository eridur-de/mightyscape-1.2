#!/usr/bin/env python3
#
# Copyright (C) 2020 Ellen Wasboe, ellen@wasbo.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
Duplicate subpaths of all selected paths, reverse and join end nodes.
"""

import inkex

class DuplicateReverseJoin(inkex.EffectExtension):
		
	def effect(self):
		for elem in self.svg.selection:
			
			pp=elem.path.to_absolute()
			dList=str(pp).split(' M')
			dFinal=''
			l=0
			for sub in dList:
				if l>0:
					origSub='M'+dList[l]
				else:
					origSub=dList[l]
				
				elem.path=origSub
				reSub=elem.path.reverse()
				
				if l>0:
					origSub=' '+origSub
					
				if origSub.find('Z') > -1:
					dRev=str(reSub).split(' ')
					strRev=''
					if dRev[3]=='L' and dRev[1]==dRev[4] and dRev[2]==dRev[5]:
						strRev=' '.join(dRev[0:3])+' '+' '.join(dRev[6:]) #avoid that reverse path duplicate first node
					else:
						strRev=' '.join(dRev)
					dFinal=dFinal+origSub+' '+strRev #keep original and reverse as separate closed paths
					if dRev[-1]!='Z':
						dFinal=dFinal+' Z'#avoid that reverse of closed path is open
				else:
					dRev=str(reSub).split(' ')
					dFinal=dFinal+origSub+' '+' '.join(dRev[3:])+' Z' #pop off M element of reverse path and add Z to close
				l+=1
			elem.path=dFinal
		
				
if __name__ == '__main__':
    DuplicateReverseJoin().run()