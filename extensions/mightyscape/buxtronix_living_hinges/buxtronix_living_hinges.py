#!/usr/bin/env python3

import inkex
cut_colour = '#ff0000'
engrave_colour = '#0000ff'

class Generator(object):
    """A generic generator, subclassed for each different lattice style."""

    def __init__(self, x, y, width, height, stroke_width, svg, e_length, p_spacing):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.stroke_width = stroke_width
        self.svg = svg
        self.canvas = self.svg.get_current_layer()
        self.e_length = e_length
        self.e_height = 0  # Provided by sub-classes.
        self.p_spacing = p_spacing
        self.fixed_commands = ""

    def draw_one(self, x, y):
        return "M %f,%f %s" % (x, y, self.fixed_commands)

    def parameter_text(self):
        return "length: %.f spacing: %.1f" % (
            self.e_length,
            self.p_spacing,
        )

    def draw_swatch(self):
        border = self.canvas.add(inkex.PathElement())
        # Curve radius
        cr = self.svg.unittouu('10mm')
        # Swatch padding
        sp = self.svg.unittouu('30mm')
        # Handle length
        hl = cr/2
        path_command = (
                'm %f,%f l %f,%f c %f,%f %f,%f %f,%f'
                'l %f,%f c %f,%f %f,%f %f,%f '
                'l %f,%f c %f,%f %f,%f %f,%f '
                'l %f,%f c %f,%f %f,%f %f,%f ') % (
                cr, 0,

                self.width - 2*cr, 0,

                hl, 0,
                cr, cr-hl,
                cr, cr,

                0, self.height - 2*cr + 1.5*sp,

                0, cr/2,
                0-cr+hl, cr,
                0-cr, cr,

                0-self.width + 2*cr, 0,

                0-hl, 0,
                0-cr, 0-cr+hl,
                0-cr, 0-cr,

                0, 0-self.height - 1.5*sp + 2*cr,

                0, 0-hl,
                cr-hl, 0-cr,
                cr, 0-cr
                )

        style = {
            "stroke": cut_colour,
            "stroke-width": str(self.stroke_width),
            "fill": "none",
        }
        border.update(**{"style": style, "inkscape:label": "lattice_border", "d": path_command})

        c = self.canvas.add(inkex.Circle(
            style=str(inkex.Style(style)),
            cx=str(cr),
            cy=str(cr),
            r=str(self.svg.unittouu('4mm'))))

        self.y += sp

        text_style = {
                'fill': engrave_colour,
                'font-size': '9px',
                'font-family': 'sans-serif',
                'text-anchor': 'middle',
                'text-align': 'center',
                }
        text = self.canvas.add(
                inkex.TextElement(
                    style=str(inkex.Style(text_style)),
                    x=str(self.x + self.width/2),
                    y=str(self.y - sp/2)))
        text.text = "Style: %s" % self.name

        text_style['font-size'] = "3px"
        text = self.canvas.add(
                inkex.TextElement(
                    style=str(inkex.Style(text_style)),
                    x=str(self.x + self.width/2),
                    y=str(self.y - sp/4)))
        text.text = self.parameter_text()

        text = self.canvas.add(
                inkex.TextElement(
                    style=str(inkex.Style(text_style)),
                    x=str(self.x + self.width/2),
                    y=str(self.y +self.height + sp/4)))
        text.text = "https://github.com/buxtronix/living-hinge"

    def generate(self, swatch):
        if swatch:
            self.draw_swatch()
        # Round width/height to integer number of patterns.
        self.e_length = self.width / max(round(self.width / self.e_length), 1.0)
        self.e_height = self.height / max(round(self.height / self.e_height), 1.0)
        self.prerender()
        style = {
            "stroke": cut_colour,
            "stroke-width": str(self.stroke_width),
            "fill": "none",
        }
        path_command = ""
        y = self.y
        while y < self.y + self.height:
            x = self.x
            while x < self.x + self.width:
                path_command = "%s %s " % (path_command, self.draw_one(x, y))
                x += self.e_length
            y += self.e_height

        link = self.canvas.add(inkex.PathElement())
        link.update(**{"style": style, "inkscape:label": "lattice", "d": path_command})
        link.insert(0, inkex.Desc("%s hinge %s" % (self.name, self.parameter_text())))

class StraightLatticeGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(StraightLatticeGenerator, self).__init__(*args)
        self.link_gap = kwargs['link_gap']
        self.e_height = 2 * self.p_spacing
        self.name = "straight"

    def prerender(self):
        self.e_height = 2 * self.p_spacing
        w = self.e_length
        lg = self.link_gap

        if lg < 0.1:
            # Single line for 0 height gap.
            self.fixed_commands = " m %f,%f h %f m %f,%f h %f m %f,%f h %f" % (
                0, self.e_height / 2,
                w * 2 / 5,

                0 - w / 5, 0 - self.e_height / 2,
                w * 3 / 5,

                0 - w / 5, self.e_height / 2,
                w * 2 / 5,
            )
        else:
            self.fixed_commands = (
                " m %f,%f h %f v %f h %f"
                " m %f,%f h %f v %f h %f v %f"
                " m %f,%f h %f v %f h %f "
            ) % (
                0,
                self.e_height / 2,
                w * 2 / 5,
                lg,
                0 - w * 2 / 5,
                w / 8,
                0 - lg - self.e_height / 2,
                w * 3 / 4,
                lg,
                0 - w * 3 / 4,
                0 - lg,
                w * 7 / 8,
                lg + self.e_height / 2,
                0 - w * 2 / 5,
                0 - lg,
                w * 2 / 5,
            )

    def parameter_text(self):
        text = super(StraightLatticeGenerator, self).parameter_text()
        return "%s element_height: %.1f" % (text, self.link_gap)


class DiamondLatticeGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(DiamondLatticeGenerator, self).__init__(*args)
        self.e_height = self.p_spacing
        self.diamond_curve = kwargs['diamond_curve']
        self.name = "diamond"

    def prerender(self):
        h = self.e_height
        w = self.e_length
        # Diamond curve
        dc = 0-self.diamond_curve
        # Horiz handle length.
        hhl = abs(dc * w * 0.2)
        # Endpoint horiz handle length
        ehhl = hhl if dc > 0 else 0
        # Vert handle length
        vhl = abs(dc * h / 8) if dc < 0 else 0
        # Left
        self.fixed_commands = " m %f,%f c %f,%f %f,%f %f,%f c %f,%f %f,%f %f,%f " % (
            0, h / 4,

            hhl, 0,
            w * 0.4 - ehhl, h / 4 - vhl,
            w * 0.4, h / 4,

            0 - ehhl, vhl,
            0 - (w * 0.4 - hhl), h / 4,
            0 - w * 0.4, h / 4,
        )

        # Bottom
        self.fixed_commands = "%s m %f,%f c %f,%f %f,%f %f,%f s %f,%f %f,%f " % (
            self.fixed_commands,
            w * 0.1, h / 4,

            ehhl, 0 - vhl,
            w * 0.4 - hhl, 0 - h / 4,
            w * 0.4, 0 - h / 4,

            w * 0.4 - ehhl, h / 4 - vhl,
            w * 0.4, h / 4,
        )

        # Top
        self.fixed_commands = "%s m %f,%f c %f,%f %f,%f %f,%f s %f,%f %f,%f " % (
            self.fixed_commands,
            0 - w * 0.8, 0 - h,

            ehhl, vhl,
            w * 0.4 - hhl, h / 4,
            w * 0.4, h / 4,

            w * 0.4 - ehhl, 0 - h / 4 + vhl,
            w * 0.4, 0 - h / 4,
        )

        # Right
        self.fixed_commands = "%s m %f,%f c %f,%f %f,%f %f,%f c %f,%f %f,%f %f,%f " % (
            self.fixed_commands,
            w * 0.1, h *0.75,

            0 - hhl, 0,
            (0 - w * 0.4) + ehhl,  0 - h / 4 + vhl,
            0 - w * 0.4, 0 - h / 4,

            ehhl, 0 - vhl,
            w * 0.4 - hhl, 0 - h / 4,
            w * 0.4, 0 - h / 4,
        )

    def draw_one(self, x, y):
        return "M %f,%f %s" % (x, y, self.fixed_commands)

    def parameter_text(self):
        text = super(DiamondLatticeGenerator, self).parameter_text()
        return "%s curve: %.1f" % (text, self.diamond_curve)


class CrossLatticeGenerator(Generator):
    def __init__(self, *args):
        super(CrossLatticeGenerator, self).__init__(*args)
        self.e_height = self.p_spacing
        self.name = "cross"

    def prerender(self):
        l = self.e_length
        h = self.e_height
        self.fixed_commands = (
            "m %f,%f l %f,%f l %f,%f m %f,%f l %f,%f"
            "m %f,%f l %f,%f l %f,%f l %f,%f "
            "m %f,%f l %f,%f l %f,%f l %f,%f "
            "m %f,%f l %f,%f l %f,%f m %f,%f l %f,%f"
        ) % (
            # Left
            0, h * 0.5,
            l * 0.2, 0,
            l * 0.2, 0 - h * 0.3,
            0 - l * 0.2, h * 0.3,
            l * 0.2, h * 0.3,
            # Top
            0 - l * 0.3, 0 - h * 0.5,
            l * 0.2, 0 - h * 0.3,
            l * 0.4, 0,
            l * 0.2, h * 0.3,
            # Bottom
            0, h * 0.4,
            0 - l * 0.2, h * 0.3,
            0 - l * 0.4, 0,
            0 - l * 0.2, 0 - h * 0.3,
            # Right
            l * 0.5, 0 - h * 0.5,
            l * 0.2, h * 0.3,
            0 - l * 0.2, h * 0.3,
            l * 0.2, 0 - h * 0.3,
            l * 0.2, 0,
        )


class WavyLatticeGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(WavyLatticeGenerator, self).__init__(*args)
        self.e_height = self.p_spacing
        self.name = "wavy"

    def prerender(self):
        h = self.e_height
        w = self.e_length
        self.fixed_commands = (
            " m %f,%f h %f c %f,%f %f,%f %f,%f h %f "
            "m %f,%f h %f c %f,%f %f,%f %f,%f h %f "
        ) % (
            0, h,  # Start of element (left)
            w * 0.1,  # Short horiz line.

            w * 0.1, 0,  # Control 1
            w * 3 / 40, 0 - h / 2,  # Control 2
            w * 0.2, 0 - h / 2,  # Curve top.

            w * 0.175,  # Top horiz line.

            0 - w * 0.1, 0 - h / 2,  # Move to higher line.
            w * 0.3,  # Long higher horiz line.

            w / 5, 0,  # Control 1
            w / 10, h,  # Control 2
            w * 0.25, h,  # Curve down.

            w * 0.075, # End horiz line.
        ) 


class BuxtronixLivingHinges(inkex.EffectExtension):
    """
    Extension to create laser cut bend lattices.
    """

    def add_arguments(self, pars):
        pars.add_argument("--tab", help="Bend pattern to generate")
        pars.add_argument("--unit", help="Units for dimensions")
        pars.add_argument("--swatch", type=inkex.Boolean, help="Draw as a swatch card")

        pars.add_argument("--width", type=float, default=300, help="Width of pattern")
        pars.add_argument("--height", type=float, default=100, help="Height of pattern")

        pars.add_argument("--sl_length", type=int, default=20, help="Length of links")
        pars.add_argument("--sl_gap", type=float, default=0.5, help="Gap between links")
        pars.add_argument("--sl_spacing", type=float, default=20, help="Spacing of links")

        pars.add_argument("--dl_curve", type=float, default=0.5, help="Curve of diamonds")
        pars.add_argument("--dl_length", type=float, default=24, help="Length of diamonds")
        pars.add_argument("--dl_spacing", type=float, default=4, help="Spacing of diamonds")

        pars.add_argument("--cl_length", type=float, default=24, help="Length of combs")
        pars.add_argument("--cl_spacing", type=float, default=6, help="Spacing of combs")

        pars.add_argument("--wl_length", type=int, default=20, help="Length of links")
        pars.add_argument("--wl_interval", type=int, default=30, help="Interval between links")
        pars.add_argument("--wl_spacing", type=float, default=0.5, help="Spacing between links")

    def convert(self, value):
        return self.svg.unittouu(str(value) + self.options.unit)

    def convertmm(self, value):
        return self.svg.unittouu('%fmm' % value)

    def effect(self):
        stroke_width = self.svg.unittouu("0.2mm")
        self.options.width = self.convert(self.options.width)
        self.options.height = self.convert(self.options.height)

        def draw_one(x, y):
            if self.options.tab == "straight_lattice":
                generator = StraightLatticeGenerator(
                    x,
                    y,
                    self.options.width,
                    self.options.height,
                    stroke_width,
                    self.svg,
                    self.convertmm(self.options.sl_length),
                    self.convertmm(self.options.sl_spacing),
                    link_gap=self.convertmm(self.options.sl_gap),
                )
            elif self.options.tab == "diamond_lattice":
                generator = DiamondLatticeGenerator(
                    x,
                    y,
                    self.options.width,
                    self.options.height,
                    stroke_width,
                    self.svg,
                    self.convertmm(self.options.dl_length),
                    self.convertmm(self.options.dl_spacing),
                    diamond_curve=self.options.dl_curve,
                )
            elif self.options.tab == "cross_lattice":
                generator = CrossLatticeGenerator(
                    x,
                    y,
                    self.options.width,
                    self.options.height,
                    stroke_width,
                    self.svg,
                    self.convertmm(self.options.cl_length),
                    self.convertmm(self.options.cl_spacing),
                )
            elif self.options.tab == "wavy_lattice":
                generator = WavyLatticeGenerator(
                    x,
                    y,
                    self.options.width,
                    self.options.height,
                    stroke_width,
                    self.svg,
                    self.convertmm(self.options.wl_length),
                    self.convertmm(self.options.wl_spacing),
                )
            else:
                inkex.errormsg("Select a valid pattern tab before rendering.")
                return
            generator.generate(self.options.swatch)

        if self.options.swatch or not self.svg.selected:
            draw_one(0, 0)
        else:
            for elem in self.svg.selected.values():
                bbox = elem.bounding_box()
                self.options.width = self.svg.unittouu(bbox.width)
                self.options.height = self.svg.unittouu(bbox.height)
                x = self.svg.unittouu(bbox.x.minimum)
                y = self.svg.unittouu(bbox.y.minimum)
                draw_one(x, y)

BuxtronixLivingHinges().run()