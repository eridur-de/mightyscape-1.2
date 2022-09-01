from math import ceil, floor
from lxml import etree
import re
import inkex


# Constants
# =========


# A unit is represented as a conversion factor relative to the pixel unit. The
# keys must be identical to the optiongroup options defined in the .inx file.
UNITS = {
    "px": 1.0,
    "pt": 96.0 / 72.0,
    "in": 96.0,
    "cm": 96.0 / 2.54,
    "mm": 96.0 / 25.4
}

# EPSILON is used as a threshold by the rounding functions
EPSILON = 1e-3

# FOLD_LINE_TYPES defines the accepted values for horizontal and vertical
# fold lines that can be set on the command line.
NO_FOLD_LINE = "NoFoldLine"
HORIZONTAL_FOLD_LINE = "HorizontalFoldLine"
VERTICAL_FOLD_LINE = "VerticalFoldLine"
FOLD_LINE_TYPES = [NO_FOLD_LINE, HORIZONTAL_FOLD_LINE, VERTICAL_FOLD_LINE]


# Functions that change positions in some way
# ===========================================


def round_up(value, grid_size):
    """
    Return the smallest grid point that is greater or equal to the value.

    :type value: float
    :type grid_size: float
    :rtype: float
    """
    try:
        return ceil(value / grid_size - EPSILON) * grid_size
    except ZeroDivisionError:
        return value


def round_down(value, grid_size):
    """
    Return the greatest grid point that is less or equal to the value.

    :type value: float
    :type grid_size: float
    :rtype: float
     """
    try:
        return floor(value / grid_size + EPSILON) * grid_size
    except ZeroDivisionError:
        return value


def mirror_at(value, at):
    """
    Reflect the value at a given point.

    :type value: float
    :type at: float
    :rtype: float
    """
    return 2.0 * at - value


# Functions related to quantities and units
# =========================================


def convert_unit(source_unit, target_unit):
    """
    Returns a factor that converts from one unit to another.

    :type source_unit: str | float
    :type target_unit: str | float
    :rtype: float
    """

    # If the units are the same the conversion factor is obviously 1
    if source_unit == target_unit:
        return 1.0

    # If the unit is given as a float nothing needs to be done. Otherwise we
    # try to find the unit and its float value in the dictionary of valid
    # units.
    if not isinstance(source_unit, float):
        if source_unit not in UNITS.keys():
            raise ValueError("unexpected unit \"" + source_unit + "\"")
        source_unit = UNITS[source_unit]
    if not isinstance(target_unit, float):
        if target_unit not in UNITS.keys():
            raise ValueError("unexpected unit \"" + target_unit + "\"")
        target_unit = UNITS[target_unit]

    return source_unit / target_unit


def make_quantity(magnitude, unit):
    """
    Create a quantity from a magnitude and a unit.

    :type magnitude: float
    :type unit: str
    """
    return "{0}{1}".format(magnitude, unit)


def split_quantity(quantity):
    """
    Split a quantity into its magnitude and unit and return them as a tuple.

    :type quantity: str
    :rtype: (float, str) | (float, NoneType)
    """

    # Matches a floating point number optionally followed by letters. The
    # floating point number is the magnitude and the letters are the unit.
    pattern = re.compile(r'(?P<magnitude>[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)'
                         r'(?P<unit>[a-zA-Z]+)?')
    match = re.match(pattern, quantity)
    if match:
        return (float(match.group("magnitude")), match.group("unit"))
    else:
        return (0, None)


def convert_quantity(quantity, target_unit):
    """
    Convert the unit of a quantity to another unit.

    :type quantity: str
    :type taget_unit: str | float
    :rtype: str
    """
    return "{0}{1}".format(convert_magnitude(quantity, target_unit), target_unit)


def convert_magnitude(quantity, target_unit):
    """
    Convert the unit of a quantity to another unit and return only the new magnitude.

    :type quantity: str
    :type target_unit: str | float
    :rtype: float
    """
    magnitude, source_unit = split_quantity(quantity)
    new_magnitude = magnitude * convert_unit(source_unit, target_unit)
    return new_magnitude


# Functions related to the placement of cards
# ===========================================


def calculate_positions_without_fold_line(page_size, margin_size, card_size,
                                          bleed_size, grid_size, min_spacing,
                                          grid_aligned):
    """
    Position cards along one direction of the page without a fold line.

    The calculated positions are the positions of the right edges or bottom
    edges of the cards. The other edges and the positions of the bleeds can be
    easily derived by adding card_size, -bleed_size, and card_size+bleed_size.

    All sizes and spacings must be given as magnitudes, i.e. without units.
    Their units are assumed to be identical but can be arbitrary.

    :param page_size: The width or height of the page.
    :type page_size: float
    :param margin_size: The empty margin of the page. Nothing will be placed in
    the margin except for the frame.
    :type margin_size: float
    :param card_size: The width or height of each card.
    :type card_size: float
    :param bleed_size: The bleed around each card. This can be zero.
    :type bleed_size: float
    :param grid_size: The size of the alignment grid. The value is ignored if
    grid_aligned is False.
    :type grid_size: float
    :param min_spacing: The minimum distance between two cards.
    :type min_spacing: float
    :param grid_aligned: Whether or not the beginning of a card should be on a
    grid point.
    :type grid_aligned: bool
    :return: A list containing the beginnings of each card
    :rtype: [float]
    """
    # The bleed of the first card begins where the page margin ends. The card
    # is then moved to the next grid point if grid_aligned is True.
    card_begin = margin_size + bleed_size
    if grid_aligned:
        card_begin = round_up(card_begin, grid_size)
    card_end = card_begin + card_size

    # There are to bleeds between the end of the first card and the beginning
    # of the next. The spacing between two cards is two bleeds or min_spacing,
    # whichever is greater. If grid_aligned is True the next card is moved even
    # farther away so that it begins at the next grid point.
    spacing = max(min_spacing, 2.0 * bleed_size)
    if grid_aligned:
        spacing = round_up(card_end + spacing, grid_size) - card_end

    # We add cards and spacings until we run out of enough empty space.
    cards = []
    remaining = 0
    while True:
        card_end = card_begin + card_size
        next_remaining = page_size - margin_size - card_end - bleed_size
        if next_remaining < 0:
            break
        remaining = next_remaining
        cards.append(card_begin)
        card_begin = card_end + spacing

    # Shift everything towards the center of the page.
    shift = remaining / 2.0
    if grid_aligned:
        shift = round_down(shift, grid_size)
    cards = [card + shift for card in cards]

    return cards


def calculate_positions_with_fold_line(page_size, margin_size, card_size,
                                       bleed_size, grid_size, min_spacing,
                                       min_fold_line_spacing, grid_aligned):
    """
    Position the cards along one direction of the page with a central fold line.

    The calculated positions are the positions of the right edges or bottom
    edges of the cards. The other edges and the positions of the bleeds can be
    easily derived by adding card_size, -bleed_size, and card_size+bleed_size.

    All sizes and spacings must be given as magnitudes, i.e. without units.
    Their units are assumed to be identical but can be arbitrary.

    :param page_size: The width or height of the page.
    :type page_size: float
    :param margin_size: The empty margin of the page. Nothing will be placed in
    the margin.
    :type margin_size: float
    :param card_size: The width or height of each card.
    :type card_size: float
    :param bleed_size: The bleed around each card. This can be zero.
    :type bleed_size: float
    :param grid_size: The size of the alignment grid. The value is ignored if
    grid_aligned is False.
    :type grid_size: float
    :param min_spacing: The minimum distance between two cards.
    :type min_spacing: float
    :param min_fold_line_spacing: The minimum distance between a card and the 
    fold line.
    :type min_fold_line_spacing: float
    :param grid_aligned: Whether or not the beginning of a card should be on a
    grid point.
    :type grid_aligned: bool
    :return: A tuple with a list containing the beginnings of each card and the
    position of the fold line.
    :rtype: ([float], float)
    """
    # The spacing between the two central cards at the fold line must be at
    # at least 2*bleed_size or 2*min_fold_line_spacing or min_spacing, 
    # whichever is the greatest.
    central_spacing = max(2.0 * min_fold_line_spacing,
                          max(min_spacing, 2.0 * bleed_size))

    # First we assume that the fold line is at the center of the page. This
    # might change a bit later if we want grid alignment. We then place the
    # first card before the fold line so that there is an empty space of 
    # central_spacing/2 between the card and the fold line.
    card_begin = (page_size - central_spacing) / 2.0 - card_size
    if grid_aligned:
        card_begin = round_down(card_begin, grid_size)
    card_end = card_begin + card_size

    # The card on the other side can be placed by mirroring the first card at
    # the fold line. But this card is not neccessarily grid aligned. We fix that
    # by increasing the central spacing so that the first card on the other side
    # of the fold line is also grid aligned.
    if grid_aligned:
        central_spacing = round_up(
            card_end + central_spacing, grid_size) - card_end

    # The fold line should not be at the center of the page but in the middle
    # between the two central cards. If we don't use grid alignment then this
    # is also the center of the page.
    fold_line = card_end + central_spacing / 2.0

    # The spacing between all remaining cards might be different because we
    # don't use min_fold_line_spacing. But the calculation remains the same as
    # for the two central cards.
    spacing = max(min_spacing, 2.0 * bleed_size)
    if grid_aligned:
        spacing = round_up(card_end + spacing, grid_size) - card_end

    # Now that we have calculated all spacings we start adding cards to both
    # sides of the fold line beginning at the center and moving outwards.
    cards = []
    while True:
        if card_begin < margin_size:
            break
        cards.append(card_begin)
        cards.append(mirror_at(card_end, fold_line))
        card_begin -= card_size + spacing
        card_end = card_begin + card_size

    # We sort the positions of the cards so that the positions start with the
    # lowest and end with the highest value.
    cards.sort()

    return (cards, fold_line)


class PlayingCardsExtension(inkex.EffectExtension):
    """
    Implements the interface for Inkscape addons.

    An instance of this class is created in main(). __init__() sets up the 
    OptionParser provided by the base class to recognize all needed command 
    line parameters. Then in main() inkex.Effect.run() is called which then 
    parses the command line and calls effect(). This is where we do our work.
    """

    # Constants passed from the command line
    PAGE_WIDTH = None
    PAGE_HEIGHT = None
    CARD_WIDTH = None
    CARD_HEIGHT = None
    BLEED_SIZE = None
    MIN_CARD_SPACING = None
    CROP_MARK_SPACING = None
    MIN_FOLD_LINE_SPACING = None
    PAGE_MARGIN = None
    GRID_SIZE = None
    ALIGN_TO_GRID = None
    FOLD_LINE_TYPE = None
    FRAME_SPACING = None
    DRAW_GUIDES = None
    DRAW_CARDS = None
    DRAW_BLEEDS = None
    DRAW_CROP_LINES = None
    DRAW_FOLD_LINE = None
    DRAW_PAGE_MARGIN = None
    DRAW_FRAME = None

    USER_UNIT = None                 # The unit used in the document
    horizontal_card_positions = None # Calculated horizontal positions
    vertical_card_positions = None   # Calculated vertical positions
    fold_line_position = None        # Calculated position of the fold line

    def add_arguments(self, pars):
        """
        Initialize the OptionParser with recognized parameters.

        The option names must be identical to those defined in the .inx file.
        The option values are later used to initialize the class constants.
        """
        pars.add_argument("--pageName", type=str)

        pars.add_argument("--cardWidth", type=float)
        pars.add_argument("--cardWidthUnit", choices=UNITS.keys())

        pars.add_argument("--cardHeight", type=float)
        pars.add_argument("--cardHeightUnit", choices=UNITS.keys())

        pars.add_argument("--bleedSize", type=float, action="store")
        pars.add_argument("--bleedSizeUnit", choices=UNITS.keys())

        pars.add_argument("--minCardSpacing", type=float)
        pars.add_argument("--minCardSpacingUnit", choices=UNITS.keys())

        pars.add_argument("--cropMarkSpacing", type=float)
        pars.add_argument("--cropMarkSpacingUnit", choices=UNITS.keys())

        pars.add_argument("--minFoldLineSpacing", type=float)
        pars.add_argument("--minFoldLineSpacingUnit", choices=UNITS.keys())

        pars.add_argument("--pageMargin", type=float)
        pars.add_argument("--pageMarginUnit", choices=UNITS.keys())

        pars.add_argument("--frameSpacing", type=float)
        pars.add_argument("--frameSpacingUnit", choices=UNITS.keys())

        pars.add_argument("--gridSize", type=float)
        pars.add_argument("--gridSizeUnit", choices=UNITS.keys())

        pars.add_argument("--gridAligned", type=inkex.Boolean)
        pars.add_argument("--foldLineType", choices=FOLD_LINE_TYPES)
        pars.add_argument("--drawGuides", type=inkex.Boolean)
        pars.add_argument("--drawCards", type=inkex.Boolean)
        pars.add_argument("--drawBleeds", type=inkex.Boolean)
        pars.add_argument("--drawCropLines", type=inkex.Boolean)
        pars.add_argument("--drawFoldLine", type=inkex.Boolean)
        pars.add_argument("--drawPageMargin", type=inkex.Boolean)
        pars.add_argument("--drawFrame", type=inkex.Boolean)

    def init_user_unit(self):
        """
        Determine the user unit from the document contents.
        """
        root = self.document.getroot()
        view_box = root.get("viewBox")

        # If the document has a valid viewBox we try to derive the user unit
        # from that.
        valid_view_box = view_box and len(view_box.split()) == 4
        if valid_view_box:
            view_box = root.get("viewBox").split()
            view_box_width, view_box_width_unit = split_quantity(view_box[2])
            # If the viewBox has a unit use that.
            if view_box_width_unit:
                self.USER_UNIT = view_box_width_unit
            # If the viewBox has no unit derive the unit from the ratio between
            # the document width and the viewBox width.
            else:
                document_width, document_width_unit = split_quantity(
                    self.document_width())
                self.USER_UNIT = document_width / view_box_width
                if document_width_unit:
                    self.USER_UNIT *= UNITS[document_width_unit]
        # If the document has no valid viewBox we try to derive the user unit
        # from the document width.
        else:
            document_width, document_width_unit = split_quantity(
                self.document_width())
            if document_width_unit:
                self.USER_UNIT = UNITS[document_width_unit]
            else:
                # This might be problematic because v0.91 uses 90dpi and v0.92
                # uses 96dpi
                self.USER_UNIT = UNITS["px"]

    def init_constants(self):
        """
        Initialize the class constants from the OptionParser values and the
        document contents.

        This converts all quantities from the unit given on the command line to
        the user unit.
        """

        self.PAGE_WIDTH = self.to_user_unit(self.document_width())
        self.PAGE_HEIGHT = self.to_user_unit(self.document_height())
        self.CARD_WIDTH = self.to_user_unit(
            make_quantity(self.options.cardWidth,
                          self.options.cardWidthUnit))
        self.CARD_HEIGHT = self.to_user_unit(
            make_quantity(self.options.cardHeight,
                          self.options.cardHeightUnit))
        self.BLEED_SIZE = self.to_user_unit(
            make_quantity(self.options.bleedSize,
                          self.options.bleedSizeUnit))
        self.GRID_SIZE = self.to_user_unit(
            make_quantity(self.options.gridSize,
                          self.options.gridSizeUnit))
        self.MIN_CARD_SPACING = self.to_user_unit(
            make_quantity(self.options.minCardSpacing,
                          self.options.minCardSpacingUnit))
        self.CROP_MARK_SPACING = self.to_user_unit(
            make_quantity(self.options.cropMarkSpacing,
                          self.options.cropMarkSpacingUnit))
        self.MIN_FOLD_LINE_SPACING = self.to_user_unit(
            make_quantity(self.options.minFoldLineSpacing,
                          self.options.minFoldLineSpacingUnit))
        self.PAGE_MARGIN = self.to_user_unit(
            make_quantity(self.options.pageMargin,
                          self.options.pageMarginUnit))
        self.FRAME_SPACING = self.to_user_unit(
            make_quantity(self.options.frameSpacing,
                          self.options.frameSpacingUnit))
        self.ALIGN_TO_GRID = self.options.gridAligned
        self.FOLD_LINE_TYPE = self.options.foldLineType
        self.DRAW_GUIDES = self.options.drawGuides
        self.DRAW_CARDS = self.options.drawCards
        self.DRAW_BLEEDS = self.options.drawBleeds
        self.DRAW_CROP_LINES = self.options.drawCropLines
        self.DRAW_FOLD_LINE = self.options.drawFoldLine
        self.DRAW_PAGE_MARGIN = self.options.drawPageMargin
        self.DRAW_FRAME = self.options.drawFrame

    def effect(self):
        self.init_user_unit()
        self.init_constants()

        self.calculate_positions()

        # Create one layer for the things that we want to print and another
        # layer for things that we don't want to print but are useful while
        # working on the cards.
        non_printing_layer = self.create_layer("(template) non printing")
        printing_layer = self.create_layer("(template) printing")

        if self.DRAW_GUIDES:
            self.create_guides()

        if self.DRAW_CARDS:
            self.create_cards(non_printing_layer)

        if self.DRAW_BLEEDS:
            self.create_bleeds(non_printing_layer)

        if self.DRAW_CROP_LINES:
            self.create_crop_lines(printing_layer)

        if self.DRAW_FOLD_LINE:
            self.create_fold_line(printing_layer)

        if self.DRAW_PAGE_MARGIN:
            self.create_margin(non_printing_layer)

        if self.DRAW_FRAME:
            self.create_frame(printing_layer)

    def to_user_unit(self, quantity):
        """
        Convert a quantity to the user unit and return its magnitude.

        :type quantity: str
        :rtype: float
        """
        return convert_magnitude(quantity, self.USER_UNIT)

    def document_width(self):
        """
        Return the document width.

        The width is read from the document. It may or may not contain a unit.
        """
        return self.document.getroot().get("width")

    def document_height(self):
        """
        Return the document height.

        The height is read from the document. It may or may not contain a unit.
        """
        return self.document.getroot().get("height")

    def calculate_positions(self):
        """
        Calculate the horizontal and vertical positions of all cards.

        The results are stored in self.horizontal_card_positions,
        self.vertical_card_positions, and self.fold_line_position.
        """
        if self.FOLD_LINE_TYPE == VERTICAL_FOLD_LINE:
            self.horizontal_card_positions, self.fold_line_position = \
                calculate_positions_with_fold_line(
                    self.PAGE_WIDTH,
                    self.PAGE_MARGIN,
                    self.CARD_WIDTH,
                    self.BLEED_SIZE,
                    self.GRID_SIZE,
                    self.MIN_CARD_SPACING,
                    self.MIN_FOLD_LINE_SPACING,
                    self.ALIGN_TO_GRID)
        else:
            self.horizontal_card_positions = \
                calculate_positions_without_fold_line(
                    self.PAGE_WIDTH,
                    self.PAGE_MARGIN,
                    self.CARD_WIDTH,
                    self.BLEED_SIZE,
                    self.GRID_SIZE,
                    self.MIN_CARD_SPACING,
                    self.ALIGN_TO_GRID)

        if self.FOLD_LINE_TYPE == HORIZONTAL_FOLD_LINE:
            self.vertical_card_positions, self.fold_line_position = \
                calculate_positions_with_fold_line(
                    self.PAGE_HEIGHT,
                    self.PAGE_MARGIN,
                    self.CARD_HEIGHT,
                    self.BLEED_SIZE,
                    self.GRID_SIZE,
                    self.MIN_CARD_SPACING,
                    self.MIN_FOLD_LINE_SPACING,
                    self.ALIGN_TO_GRID)
        else:
            self.vertical_card_positions = \
                calculate_positions_without_fold_line(
                    self.PAGE_HEIGHT,
                    self.PAGE_MARGIN,
                    self.CARD_HEIGHT,
                    self.BLEED_SIZE,
                    self.GRID_SIZE,
                    self.MIN_CARD_SPACING,
                    self.ALIGN_TO_GRID)
    
    # Functions related to the structure of the document
    # ==================================================

    def create_group(self, parent, label):
        """
        Create a new group in the svg document.

        :type parent: lxml.etree._Element
        :type label: str
        :rtype: lxml.etree._Element
        """
        group = etree.SubElement(parent, "g")
        group.set(inkex.addNS("label", "inkscape"), label)
        return group

    def create_layer(self, label, is_visible=True, is_locked=True):
        """
        Create a new layer in the svg document.

        :type label: str
        :rtype: lxml.etree._Element
        """
        layer = self.create_group(self.document.getroot(), label)
        layer.set(inkex.addNS("groupmode", "inkscape"), "layer")
        # The Inkscape y-axis runs from bottom to top, the SVG y-axis runs from
        # top to bottom. Therefore we need to transform all y coordinates.
        layer.set(
            "transform", "matrix(1 0 0 -1 0 {0})".format(self.PAGE_HEIGHT))

        # Don't show the layer contents
        if not is_visible:
            layer.set("style", "display:none")

        # Lock the layer
        if is_locked:
            layer.set(inkex.addNS("insensitive", "sodipodi"), "true")

        return layer

    # Functions related to the contents of the document
    # =================================================

    def create_guide(self, x, y, orientation):
        """
        Create an arbitrary guide.

        :type x: float
        :type y: float
        :type orientation: str
        """
        view = self.document.getroot().find(inkex.addNS("namedview", "sodipodi"))
        guide = etree.SubElement(view, inkex.addNS("guide", "sodipodi"))
        guide.set("orientation", orientation)
        guide.set("position", "{0},{1}".format(x, y))
    
    def create_horizontal_guide(self, y):
        """
        Create a horizontal guide.
        """
        self.create_guide(0, y, "0,1")

    def create_vertical_guide(self, x):
        """
        Create a vertical guide.
        """
        self.create_guide(x, 0, "1,0")

    def create_guides(self):
        """
        Create guides at all sides of all cards and bleeds.
        """
        for x in self.horizontal_card_positions:
            self.create_vertical_guide(x)
            self.create_vertical_guide(x + self.CARD_WIDTH)
            if self.BLEED_SIZE > 0:
                self.create_vertical_guide(x - self.BLEED_SIZE)
                self.create_vertical_guide(x + self.CARD_WIDTH + self.BLEED_SIZE)

        for y in self.vertical_card_positions:
            self.create_horizontal_guide(y)
            self.create_horizontal_guide(y + self.CARD_HEIGHT)
            if self.BLEED_SIZE > 0:
                self.create_horizontal_guide(y - self.BLEED_SIZE)
                self.create_horizontal_guide(y + self.CARD_HEIGHT + self.BLEED_SIZE)

    def create_bleeds(self, parent):
        """
        Creates a rectangle for each bleed.

        :type parent: lxml.etree._Element
        """
        if self.BLEED_SIZE <= 0:
            return

        attributes = {"x": str(-self.BLEED_SIZE),
                      "y": str(-self.BLEED_SIZE),
                      "width": str(self.CARD_WIDTH + 2.0 * self.BLEED_SIZE),
                      "height": str(self.CARD_HEIGHT + 2.0 * self.BLEED_SIZE),
                      "stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "fill": "none"}

        for y in self.vertical_card_positions:
            for x in self.horizontal_card_positions:
                attributes["transform"] = "translate({0},{1})".format(x, y)
                etree.SubElement(parent, "rect", attributes)

    def create_cards(self, parent):
        """
        Create a rectangle for each card.

        :type parent: lxml.etree._Element
        """
        attributes = {"x": str(0),
                      "y": str(0),
                      "width": str(self.CARD_WIDTH),
                      "height": str(self.CARD_HEIGHT),
                      "stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "fill": "none"}

        for y in self.vertical_card_positions:
            for x in self.horizontal_card_positions:
                attributes["transform"] = "translate({0},{1})".format(x, y)
                etree.SubElement(parent, "rect", attributes)

    def create_fold_line(self, parent):
        """
        Create a horizontal or vertical fold line.

        :type parent: lxml.etree._Element
        """
        attributes = {"stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "fill": "none"}

        if self.FOLD_LINE_TYPE == HORIZONTAL_FOLD_LINE:
            attributes["d"] = "M 0,{0} H {1}".format(
                self.fold_line_position, self.PAGE_WIDTH)
        elif self.FOLD_LINE_TYPE == VERTICAL_FOLD_LINE:
            attributes["d"] = "M {0},0 V {1}".format(
                self.fold_line_position, self.PAGE_HEIGHT)
        else:
            return

        etree.SubElement(parent, "path", attributes)

    def create_crop_lines(self, parent):
        """
        Create horizontal and vertical crop lines.

        :type parent: lxml.etree._Element
        """
        attributes = {"stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "fill": "none"}

        # (begin, end) pairs for vertical crop line between bleeds
        pairs = []
        begin = 0
        for y in self.vertical_card_positions:
            end = y - self.BLEED_SIZE - self.CROP_MARK_SPACING
            # Only add lines if they fit between two bleeds
            if end - begin >= EPSILON:
                pairs.append((begin, end))
            begin = end + self.CARD_HEIGHT \
                + 2.0 * self.BLEED_SIZE \
                + 2.0 * self.CROP_MARK_SPACING
        pairs.append((begin, self.PAGE_HEIGHT))

        # One crop line consists of many short strokes
        attributes["d"] = " ".join(["M 0,{0} 0,{1}".format(begin, end)
                                    for (begin, end) in pairs])

        # Shifted copies of the crop line
        for x in self.horizontal_card_positions:
            attributes["transform"] = "translate({0},0)".format(x)
            etree.SubElement(parent, "path", attributes)
            attributes["transform"] = "translate({0},0)".format(
                x + self.CARD_WIDTH)
            etree.SubElement(parent, "path", attributes)

        # (begin, end) pairs for horizontal crop line between bleeds
        pairs = []
        begin = 0
        for x in self.horizontal_card_positions:
            end = x - self.BLEED_SIZE - self.CROP_MARK_SPACING
            # Only add lines if they fit between two bleeds
            if end - begin >= EPSILON:
                pairs.append((begin, end))
            begin = end + self.CARD_WIDTH \
                + 2.0 * self.BLEED_SIZE \
                + 2.0 * self.CROP_MARK_SPACING
        pairs.append((begin, self.PAGE_WIDTH))

        # One crop line consists of many short strokes
        attributes["d"] = " ".join(["M {0},0 {1},0".format(begin, end)
                                    for (begin, end) in pairs])

        # Shifted copies of the crop line
        for y in self.vertical_card_positions:
            attributes["transform"] = "translate(0,{0})".format(y)
            etree.SubElement(parent, "path", attributes)
            attributes["transform"] = "translate(0,{0})".format(
                y + self.CARD_HEIGHT)
            etree.SubElement(parent, "path", attributes)

    def create_margin(self, parent):
        """
        Create a rectangle for the page margin.

        :type parent: lxml.etree._Element
        """
        if self.PAGE_MARGIN <= 0:
            return

        attributes = {"x": str(self.PAGE_MARGIN),
                      "y": str(self.PAGE_MARGIN),
                      "width": str(self.PAGE_WIDTH - 2.0 * self.PAGE_MARGIN),
                      "height": str(self.PAGE_HEIGHT - 2.0 * self.PAGE_MARGIN),
                      "stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "stroke-dasharray": "0.5,0.5",
                      "fill": "none"}

        etree.SubElement(parent, "rect", attributes)
    
    def create_frame(self, parent):
        """
        Create a frame around the cards.
        """

        # If we don't have any cards we can't draw a frame around them
        if len(self.horizontal_card_positions) == 0 or \
           len(self.vertical_card_positions) == 0:
            return

        XMIN = min(self.horizontal_card_positions)
        XMAX = max(self.horizontal_card_positions)
        YMIN = min(self.vertical_card_positions)
        YMAX = max(self.vertical_card_positions)

        LEFT = XMIN - self.FRAME_SPACING
        BOTTOM = YMIN - self.FRAME_SPACING
        WIDTH = XMAX - XMIN + self.CARD_WIDTH + 2 * self.FRAME_SPACING
        HEIGHT = YMAX - YMIN + self.CARD_HEIGHT + 2 * self.FRAME_SPACING

        attributes = {"x": str(LEFT),
                      "y": str(BOTTOM),
                      "width": str(WIDTH),
                      "height": str(HEIGHT),
                      "stroke": "black",
                      "stroke-width": str(self.to_user_unit("0.25pt")),
                      "fill": "none"}

        etree.SubElement(parent, "rect", attributes)


def main():
    PlayingCardsExtension().run()


if __name__ == '__main__':
    main()
