#! /usr/bin/env python3

import random
import inkex

class RandomDelete(inkex.Effect):

    def add_arguments(self, pars):
        pars.add_argument("--prob", type=float, default=50, help="Probability of deletion")

    def effect(self):
        if len(self.svg.selected) > 0:
            for element in self.svg.selection.values():
                if random.random() < self.options.prob/100:
                    element.delete()
        else:
            self.msg('Please select some paths first.')
            return 
 
if __name__ == '__main__':
    RandomDelete().run()