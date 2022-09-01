#!/usr/bin/env python3

import inkex

# ---------------------------------

# UTILITIES

# Common standards

UPPERCASE_PREFIXES = {
    chr(15): 0x2828,  # uppercase prefix: https://codepoints.net/U+000F
}


LOUIS_BRAILLE_NUMBERS_PREFIX = 0x283c  # Louis Braille's numbers prefix
LOUIS_BRAILLE_NUMBERS = {  # Louis Braille's original numbers codification
    "0": 0x281a,
    "1": 0x2801,
    "2": 0x2803,
    "3": 0x2809,
    "4": 0x2819,
    "5": 0x2811,
    "6": 0x280B,
    "7": 0x281b,
    "8": 0x2813,
    "9": 0x280a,
}

# ---------------------

# English based locales

EN_ASCII = " A1B'K2L@CIF/MSP\"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\\0Z7(_?W]#Y)="

# Spanish based locales

ES_LETTERS = {
    "A": 0x2801,
    "B": 0x2803,
    "C": 0x2809,
    "D": 0x2819,
    "E": 0x2811,
    "F": 0x280B,
    "G": 0x281b,
    "H": 0x2813,
    "I": 0x280a,
    "J": 0x281a,
    "K": 0x2805,
    "L": 0x2807,
    "M": 0x280d,
    "N": 0x281d,
    "Ñ": 0x283b,
    "O": 0x2815,
    "P": 0x280f,
    "Q": 0x281f,
    "R": 0x2817,
    "S": 0x280e,
    "T": 0x281e,
    "U": 0x2825,
    "V": 0x2827,
    "W": 0x283a,
    "X": 0x282d,
    "Y": 0x283d,
    "Z": 0x2835,
}

ES_SIGNS = {
    " ": 0x2800,  # braille space
    "ª": 0x2801,  # ordinal (feminine)  -> same as A
    "º": 0x2815,  # ordinal (masculine) -> same as O
    "&": 0x282f,
    ".": 0x2804,
    ",": 0x2802,
    ":": 0x2812,
    ";": 0x2806,
    "¿": 0x2822,
    "?": 0x2822,
    "¡": 0x2816,
    "!": 0x2816,
    '"': 0x2826,
    "(": 0x2823,
    ")": 0x281c,
    # "[": 0x2837,  collides with "Á" (Spanish and Catalan)
    # "]": 0x283e,  collides with "Ú" (Spanish and Catalan)
    "*": 0x2814,

    # math
    "-": 0x2824,
    "=": 0x2836,
    "×": 0x2826,  # multiplication
    "÷": 0x2832,  # division
    "+": 0x2816,
    "@": 0x2810,
}

ES_ACCENT_MARKS = {
    "Á": 0x2837,
    "É": 0x282e,
    "Í": 0x280c,
    "Ó": 0x282c,
    "Ú": 0x283e,
    "Ü": 0x2833,
}

ES_COMBINATIONS = {
    # signs
    "%": (0x2838, 0x2834),
    "‰": (0x2838, 0x2834, 0x2834),          # per mile
    "/": (0x2820, 0x2802),
    "\\": (0x2810, 0x2804),
    "<": (0x2810, 0x2805),
    ">": (0x2828, 0x2802),
    "|": (0x2838, 0x2807),
    "{": (0x2810, 0x2807),
    "}": (0x2838, 0x2802),
    "–": (0x2824, 0x2824),  # two different unicode dashes
    "—": (0x2824, 0x2824),
    "…": (0x2804, 0x2804, 0x2804),

    # legal
    "©": (0x2823, 0x2828, 0x2809, 0x281c),  # copyright
    "®": (0x2823, 0x2828, 0x2817, 0x281c),  # registered
    "℗": (0x2823, 0x2828, 0x280f, 0x281c),
    "🄯": (0x2823, 0x2828, 0x2807, 0x281c),

    # currencies
    "€": (0x2838, 0x2811),
    "$": (0x2838, 0x280e),
    "¢": (0x2818, 0x2809),
    "£": (0x2810, 0x282e),
    "¥": (0x2838, 0x283d),
    "￥": (0x2838, 0x283d),
}

CA_ACCENT_MARKS = {
    "É": 0x283f,
    "Í": 0x280c,
    "Ó": 0x282a,
    "Ú": 0x283e,
    "À": 0x2837,
    "È": 0x282e,
    "Ò": 0x282c,
    "Ï": 0x283b,
    "Ü": 0x2833,
    "Ç": 0x282f,
}

# French based locales

FR_LETTERS = {
    "A": 0x2801,
    "B": 0x2803,
    "C": 0x2809,
    "D": 0x2819,
    "E": 0x2811,
    "F": 0x280b,
    "G": 0x281b,
    "H": 0x2813,
    "I": 0x280a,
    "J": 0x281a,
    "K": 0x2805,
    "L": 0x2807,
    "M": 0x280d,
    "N": 0x281d,
    "O": 0x2815,
    "P": 0x280f,
    "Q": 0x281f,
    "R": 0x2817,
    "S": 0x280e,
    "T": 0x281e,
    "U": 0x2825,
    "V": 0x2827,
    "W": 0x283a,
    "X": 0x282d,
    "Y": 0x283d,
    "Z": 0x2835,
}

FR_ACCENT_MARKS = {
    "É": 0x283f,
    "À": 0x2837,
    "È": 0x282e,
    "Ù": 0x283e,
    "Â": 0x2821,
    "Ê": 0x2823,
    "Î": 0x2829,
    "Ô": 0x2839,
    "Û": 0x2831,
    "Ë": 0x282b,
    "Ï": 0x283b,
    "Ü": 0x2833,
    "Ç": 0x282f,
    "Œ": 0x282a,  # oe ligature
}

FR_SIGNS = {
    " ": 0x2800,  # braille space
    ",": 0x2802,
    ";": 0x2806,
    ":": 0x2812,
    ".": 0x2832,
    "?": 0x2822,
    "!": 0x2816,
    "«": 0x2836,
    "»": 0x2836,
    "“": 0x2836,
    "”": 0x2836,
    '"': 0x2836,
    "‘": 0x2836,
    "’": 0x2836,
    "(": 0x2826,
    ")": 0x2834,
    "'": 0x2804,
    "'": 0x2804,
    "/": 0x280c,
    "@": 0x281c,
    "^": 0x2808,  # elevation exponent
    "-": 0x2824,
    "+": 0x2816,
    "×": 0x2814,  # multiplication
    "÷": 0x2812,  # division
    "=": 0x2836,
}

FR_COMBINATIONS = {
    "↔": (0x282a, 0x2812, 0x2815),  # bidirectional arrow
    "←": (0x282a, 0x2812, 0x2812),  # left arrow
    "→": (0x2812, 0x2812, 0x2815),  # right arrow
    "…": (0x2832, 0x2832, 0x2832),  # unicode ellipsis
    "–": (0x2824, 0x2824),
    "—": (0x2824, 0x2824),
    "_": (0x2810, 0x2824),
    "[": (0x2818, 0x2826),
    "]": (0x2834, 0x2803),
    "°": (0x2810, 0x2815),  # degrees
    "§": (0x2810, 0x280f),  # paragraph/section symbol
    "&": (0x2810, 0x283f),
    "\\": (0x2810, 0x280c),
    "#": (0x2810, 0x283c),
    "{": (0x2820, 0x2820, 0x2826),
    "}": (0x2834, 0x2804, 0x2804),

    # math
    "µ": (0x2818, 0x280d),  # micron
    "π": (0x2818, 0x280f),
    "≤": (0x2818, 0x2823),
    "≥": (0x2818, 0x281c),
    "<": (0x2810, 0x2823),
    ">": (0x2810, 0x281c),
    "~": (0x2810, 0x2822),
    "*": (0x2810, 0x2814),
    "%": (0x2810, 0x282c),
    "‰": (0x2810, 0x282c, 0x282c),  # per mile

    # legal
    "©": (0x2810, 0x2809),  # copyright
    "®": (0x2810, 0x2817),  # registered
    "™": (0x2810, 0x281e),  # trademark

    # currencies
    "¢": (0x2818, 0x2809),
    "€": (0x2818, 0x2811),
    "£": (0x2818, 0x2807),
    "$": (0x2818, 0x280e),
    "¥": (0x2818, 0x283d),
    "￥": (0x2818, 0x283d),
}

# German based locales

DE_ACCENT_MARKS = {
    "Ä": 0x281c,
    "Ö": 0x282a,
    "Ü": 0x2833,
}

DE_SIGNS = {
    " ": 0x2800,  # braille space
    ",": 0x2802,
    ";": 0x2806,
    ":": 0x2812,
    "?": 0x2822,
    "!": 0x2816,
    "„": 0x2826,
    "“": 0x2834,
    "§": 0x282c,
    ".": 0x2804,
    "–": 0x2824,
    "‚": 0x2820,
}

DE_COMBINATIONS = {
    # signs
    "ß": (0x282e,),  # converted to 'SS' if uppercased, so defined in combinations
    "|": (0x2810, 0x2824),
    "[": (0x2818, 0x2837),
    "]": (0x2818, 0x283e),
    "/": (0x2818, 0x280c),
    "`": (0x2820, 0x2826),
    "´": (0x2820, 0x2834),
    "/": (0x2810, 0x2802),
    "&": (0x2810, 0x2825),
    "*": (0x2820, 0x2814),
    "→": (0x2812, 0x2812, 0x2815),
    "←": (0x282a, 0x2812, 0x2812),
    "↔": (0x282a, 0x2812, 0x2812, 0x2815),
    "%": (0x283c, 0x281a, 0x2834),
    "‰": (0x283c, 0x281a, 0x2834, 0x2834),
    "°": (0x2808, 0x2834),
    "′": (0x2808, 0x2814),
    "″": (0x2808, 0x2814, 0x2814),
    "@": (0x2808, 0x281c),
    "_": (0x2808, 0x2838),
    "#": (0x2808, 0x283c),

    # currencies
    "€": (0x2808, 0x2811),
    "$": (0x2808, 0x280e),
    "¢": (0x2808, 0x2809),
    "£": (0x2808, 0x2807),

    # legal
    "©": (0x2836, 0x2818, 0x2809, 0x2836),
    "®": (0x2836, 0x2818, 0x2817, 0x2836),
}

# END: UTILITIES

# ---------------------------------

# LOCALE FUNCTIONS

def en_char_map(char):
    """English chars mapper.

    Source: https://en.wikipedia.org/wiki/Braille_ASCII#Braille_ASCII_values
    """
    try:
        mapint = EN_ASCII.index(char.upper())
    except ValueError:
        return char
    return chr(mapint + 0x2800)

def numbers_singleuppers_combinations_factory(
    numbers_map,
    singleuppers_map,
    combinations_map,  # also individual characters that are modified if uppercased
    number_prefix,
    uppercase_prefix,
):
    """Wrapper for various character mappers implementations."""
    def char_mapper(char):
        if char.isnumeric():
            # numeric prefix + number
            return "".join([chr(number_prefix), chr(numbers_map[char])])
        try:
            bcharint = singleuppers_map[char.upper()]
        except KeyError:
            try:
                # combinations
                return "".join([chr(num) for num in combinations_map[char]])
            except KeyError:
                return char
        else:
            # if uppercase, add uppercase prefix before letter
            if char.isupper():
                return "".join([chr(uppercase_prefix), chr(bcharint)])
            return chr(bcharint)
    return char_mapper

def es_char_map_loader():
    """Spanish/Galician chars mappers.

    Source: https://sid.usal.es/idocs/F8/FDO12069/signografiabasica.pdf
    """
    return numbers_singleuppers_combinations_factory(
        LOUIS_BRAILLE_NUMBERS,
        {
            **ES_LETTERS,
            **ES_ACCENT_MARKS,
            **ES_SIGNS,
            **UPPERCASE_PREFIXES,
        },
        ES_COMBINATIONS,
        0x283c,
        0x2828,
    )

def eu_char_map_loader():
    """Euskera chars mapper.

    Uses the sample implementation as Spanish but without accent marks.

    Source: https://sid.usal.es/idocs/F8/FDO12069/signografiabasica.pdf
    """
    return numbers_singleuppers_combinations_factory(
        LOUIS_BRAILLE_NUMBERS,
        {
            **ES_LETTERS,
            **ES_SIGNS,
            **UPPERCASE_PREFIXES,
        },
        ES_COMBINATIONS,
        0x283c,
        0x2828,
    )

def ca_char_map_loader():
    """Catalan/Valencian chars mappers. Uses the same implementation as
    Spanish but different accent marks.

    Source: https://sid.usal.es/idocs/F8/FDO12069/signografiabasica.pdf
    """
    return numbers_singleuppers_combinations_factory(
        LOUIS_BRAILLE_NUMBERS,
        {
            **ES_LETTERS,
            **CA_ACCENT_MARKS,
            **ES_SIGNS,
            **UPPERCASE_PREFIXES,
        },
        ES_COMBINATIONS,
        0x283c,
        0x2828,
    )

def fr_char_map_loader():
    """French chars mapper.

    Source: https://sid.usal.es/idocs/F8/FDO12069/signografiabasica.pdf
    """
    return numbers_singleuppers_combinations_factory(
        LOUIS_BRAILLE_NUMBERS,
        {
            **FR_LETTERS,
            **FR_ACCENT_MARKS,
            **FR_SIGNS,
            **UPPERCASE_PREFIXES,
        },
        FR_COMBINATIONS,
        0x283c,
        0x2828,
    )

def de_char_map_loader():
    """German chars mapper.

    - For letters, uses the same dictionary as French implementation.

    Source: http://bskdl.org/textschrift.html
    """
    return numbers_singleuppers_combinations_factory(
        LOUIS_BRAILLE_NUMBERS,
        {
            **FR_LETTERS,  # Same as French implementation
            **DE_ACCENT_MARKS,
            **DE_SIGNS,
            **UPPERCASE_PREFIXES,
        },
        DE_COMBINATIONS,
        0x283c,
        0x2828,
    )

# END: LOCALE FUNCTIONS

LOCALE_CHARMAPS = {
    "en": en_char_map,         # English
    "es": es_char_map_loader,  # Spanish
    "fr": fr_char_map_loader,  # French
    "de": de_char_map_loader,  # German
    "gl": es_char_map_loader,  # Galician
    "eu": eu_char_map_loader,  # Euskera
    "ca": ca_char_map_loader,  # Catalan/Valencian
}

# ---------------------------------

# EXTENSION

class BrailleL18n(inkex.TextExtension):
    """Convert to Braille giving a localized map of replacements."""
    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--locale", type=str, dest="locale", default="en",
            choices=LOCALE_CHARMAPS.keys(),
            help="Locale to use converting to Braille.",
        )
    
    def process_chardata(self, text):
        """Replaceable chardata method for processing the text."""
        chars_mapper = LOCALE_CHARMAPS[self.options.locale]

        # `chars_mapper` could be a function loader or a characters mapper
        # itself, so check if the characters mapper is loaded and load it
        # if is created from a factory
        if "loader" in chars_mapper.__name__:
            chars_mapper = chars_mapper()

        return ''.join(map(chars_mapper, text))

if __name__ == '__main__':
    BrailleL18n().run()