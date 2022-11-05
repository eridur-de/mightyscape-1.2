#!/usr/bin/env python3

# pylint: disable=too-many-ancestors

# standard library
import os
import sys
import re
import argparse
from shutil import copy2
# from subprocess import Popen, PIPE
# import time
# from lxml import etree

# local library
import inkex
from inkex.command import inkscape
from inkex.elements import _selected as selection

MIN_PYTHON_VERSION = (3, 6)  # Mainly for f-strings
if (sys.version_info.major, sys.version_info.minor) < (3, 6):
    inkex.Effect.msg(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later required.")
    sys.exit(1)


class BaseExtension(inkex.Effect):
    """Custom class that makes creation of extensions easier.

    Users of this class need not worry about boilerplates, such as how to
    call inkscape via shell, and the management of tempfiles. Useful functions
    are also provided."""

    def __init__(self, custom_effect, args_adder=None):
        """Init base class.

        In a typical Inkscape extension that does not make use of BaseExtension,
        the effect is determined by the "effect" method of the extension class.
        This init function will take in a method, and run it in the "effect" method
        together with the other boilerplate.

        This init method takes in a function under the custom_effect argument.
        This function will handle the user's effects, minus the boilerplate. It
        has to return a list[str] object, with each str being a verb that inkscape
        can execute."""

        inkex.Effect.__init__(self)
        self.custom_effect = custom_effect

        self._msg = self.msg  # The old msg function provided by inkex (only accepts strings)
        def msg(*args, sep=' '):
            """Improved msg method, similar to Python's print"""
            self._msg(sep.join([str(arg) for arg in args]))
        self.msg = msg

        if args_adder is not None:
            args_adder(self.arg_parser)
            self.args_adder = args_adder




    def z_sort(self, alist):
        """Return new list sorted in document order (depth-first traversal)."""
        return list(self.z_iter(alist))


    def z_iter(self, alist):
        """Return iterator over ids in document order (depth-first traversal)."""
        id_list = list(alist)
        count = len(id_list)
        for element in self.document.getroot().iter():
            # element_id = element.get('id')
            # if element_id is not None and element_id in id_list:
            if element in alist:
                id_list.remove(element)
                yield element
                count -= 1
                if not count:
                    return

    @staticmethod
    def show(obj):
        """Returns a str representation of object"""
        def rep(obj):
            if hasattr(obj, 'get_id'):
                return f"{type(obj).__name__}({obj.get_id()})"
            return f"{type(obj).__name__}"


        if type(obj).__name__ == 'ElementList':
            return ('ElementList(' +
                ', '.join([rep(child) for child in obj.values()]) +
                ')')
        if isinstance(obj, list):
            return '[' + ', '.join(rep(child) for child in obj) + ']'


        return rep(obj)


    def find(self, obj: any, xpath='/*') -> list:
        """Returns a list of objects which satisfies XPath

        Args:
            obj (any): Parent object to recurse into. Examples include root, selected, or a group.
            xpath (str, optional): Defaults to '/*'.

        Returns:
            list: [description]
        """

        BASIC_TAGS = ('circle', 'ellipse', 'line', 'polygon', 'polyline', 'rect', 'path', 'image', 'g')
        SPECIAL_TAGS = {
            'l': "svg:g[@inkscape:groupmode='layer']",
            'p': 'svg:path'
        }

        xpath = re.sub(r'((?<=/)(' + '|'.join(BASIC_TAGS) + r')\b)', r'svg:\1', xpath)
        for k, v in SPECIAL_TAGS.items():
            xpath = re.sub('(?<=/)' + k + r'\b', v, xpath)

        xpath = re.sub(r'(?<=\[)(\d+):(\d+)(?=\])', r'position()>=\1 and position()<\2', xpath)

        if type(obj).__name__ != 'ElementList':
            obj = [obj]

        output = []
        for child in obj:
            matches =  child.xpath(xpath, namespaces={
                                'svg': 'http://www.w3.org/2000/svg',
                                'inkscape': 'http://www.inkscape.org/namespaces/inkscape'})
            for match in matches:
                if type(match).__name__ not in ('Defs', 'NamedView', 'Metadata'):
                    output.append(match)

        return output


    def effect(self):
        """Main entry point to process current document. Not to be called externally."""

        actions_list = self.custom_effect(self)
        if actions_list is None or actions_list == []:
            self.msg("No actions received. Perhaps you are calling inkex object methods?")
        elif isinstance(actions_list, list):
            tempfile = self.options.input_file + "-BaseExtension.svg"
            copy2(self.options.input_file, tempfile)
            actions_list.append("export-type:svg")
            actions_list.append("export-filename:{}".format(tempfile))
            actions_list.append("export-do")
            actions = ";".join(actions_list)
            #inkex.utils.debug(actions)
            cli_output = inkscape(tempfile, actions=actions)
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)
            # replace current document with content of temp copy file
            self.document = inkex.load_svg(tempfile)
            # update self.svg
            self.svg = self.document.getroot()


        # Clean up tempfile
        try:
            os.remove(tempfile)
        except Exception:  # pylint: disable=broad-except
            pass

    def call(self, child, ext_options):
        """Used to call an extension from another extension"""

        old_options = self.options

        parser = argparse.ArgumentParser()
        child.args_adder(parser)
        self.options = parser.parse_args([])

        for k, v in ext_options.items():
            setattr(self.options, k, v)

        output = child.custom_effect(self)
        self.options = old_options

        return output
