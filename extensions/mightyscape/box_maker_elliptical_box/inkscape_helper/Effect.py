import inkex

errormsg = inkex.errormsg
debug = inkex.debug

class Effect(inkex.Effect):
    """
    Provides some extra features to inkex.Effect:
    - Allows you to pass a list of options in stead of setting them one by one
    - acces to unittouu() that is compatible between Inkscape versions 0.48 and 0.91
    """
    def __init__(self, options=None):
        inkex.Effect.__init__(self)
        self.knownUnits = ['in', 'pt', 'px', 'mm', 'cm', 'm', 'km', 'pc', 'yd', 'ft']

        if options != None:
            for opt in options:
                if len(opt) == 2:
                    self.arg_parser.add_argument('--' + opt[0], type = opt[1])
                else:
                    self.arg_parser.add_argument('--' + opt[0], type = opt[1],default = opt[2], help = opt[3])

    try:
        inkex.Effect.unittouu   # unitouu has moved since Inkscape 0.91
    except AttributeError:
        try:
            def unittouu(self, unit):
                return inkex.unittouu(unit)
        except AttributeError:
            pass

    def effect(self):
        """

        """
        pass
