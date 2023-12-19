
from os.path import join, basename
from math import sqrt, floor

from color.colors import *
from color import mixers
from palette.palette import *

class Storage(object):

    name = None
    title = None
    filters = []

    can_load = False
    can_save = False

    def __init__(self, palette=None):
        self.palette = palette

    @classmethod
    def get_filter(cls):
        return u"{} ({})".format(cls.title, u" ".join(cls.filters))

    @staticmethod
    def check(filename):
        return True

    @staticmethod
    def get_options_widget(dialog, filename):
        return None

    def load(self, mixer, file_r, *args, **kwargs):
        raise NotImplemented

    def save(self, file_w):
        raise NotImplemented

def create_palette(colors, mixer=None, ncols=None):
    """Create Palette from list of Colors."""
    if mixer is None:
        mixer = mixers.MixerRGB
    palette = Palette(mixer)
    palette.ncols = ncols

    all_slots = []

    for clr in colors:
        slot = Slot(clr, user_defined=True)
        all_slots.append(slot)

    n_colors = len(all_slots)

    if palette.ncols is None:
        if n_colors > MAX_COLS:
            palette.ncols = max( int( floor(sqrt(n_colors)) ), 1)
        else:
            palette.ncols = n_colors

    palette.setSlots(all_slots)
    return palette

