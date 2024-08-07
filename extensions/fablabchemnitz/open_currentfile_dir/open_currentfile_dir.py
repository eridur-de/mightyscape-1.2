#!/usr/bin/env python3

import subprocess
import os
import sys
import warnings
import inkex

DETACHED_PROCESS = 0x00000008

class OpenCurrentFileDirectory(inkex.EffectExtension):

    def spawnIndependentProcess(self, args):
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"
        if os.name == 'nt':
            subprocess.Popen(args, close_fds=True, creationflags=DETACHED_PROCESS)
        else:
            subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        warnings.simplefilter("default", ResourceWarning)

    def effect(self):
        dir = os.path.dirname(self.document_path())
        if dir == '':
            inkex.utils.debug("Please save the document first!")
        if os.name == 'nt':
            explorer = "explorer"
        else:
            explorer = "xdg-open"
        
        args = [explorer, dir]
        try:
            self.spawnIndependentProcess(args)
        except FileNotFoundError as e:
            inkex.utils.debug(e)
            exit(1)

if __name__ == '__main__':
    OpenCurrentFileDirectory().run()