#!/usr/bin/env python3
"""
line animator - create CSS3 animations that look as if someone is drawing them by hand

Copyright (C) 2018-2021, Maren Hachmann <marenhachmann@yahoo.com>

using path length measuring code from measure.py, written by:
    Copyright (C) 2015 ~suv <suv-sf@users.sf.net>
    Copyright (C) 2010 Alvin Penner
    Copyright (C) 2006 Georg Wiora
    Copyright (C) 2006 Nathan Hurst
    Copyright (C) 2005 Aaron Spike, aaron@ekips.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

__version__ = 1.0

import re
import sys
from lxml import etree

# local libraries
import inkex
from inkex.bezier import csplength

# TODO:
# - do not add class style tag with anything but animation name list (needs to be parsed! animation-name: animation_1, animation_2;), but repeat all the other data for each path. This is the only way to add two different animations to a single path.
# - fix delay
# - implement removal of animations


class LineAnimator(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--duration", type=float, default=10.0, help="Duration in seconds")
        pars.add_argument("--repeat", type=int, default=1, help="Number of repetitions for looping, 0 means infinite")
        pars.add_argument("--delay", type=float, default=0.0, help="Delay of animation start in seconds")
        pars.add_argument("--identifier", default="animation_1", help="Unique identifier for the animation (only A-Z, a-z, 0-1, _)")
        pars.add_argument("--remove_from", default="selected", help="Remove animations from selected items")
        pars.add_argument("--action", default="add_anim", help="The active tab when Apply is pressed.")
        pars.add_argument("--timing", default="ease")

    def effect(self):
        self.root = self.document.getroot()

        '''
        some workaround creating a dummy style tag, because applying this extension causes issue: 
        the first style tag, which contains keyframes, is always incomplete. But when creating a dummy first, all following style tags are fine (CDATA).
        tested with Inkscape 1.2.1 on Fedora 37 with lxml 4.9.1 at Python 3.10
        '''
        dummy_style_tag = etree.SubElement(self.root, 'style', {'id': "dummy"})
        dummy_style_tag.text = "This is just a dummy style tag which can be deleted. It is getting creating due to a bug which causes that the first path_anim style is incomplete in it's formatting. This seems to be an lxml etree issue."

        id_regex = re.compile('^[a-zA-Z0-9_]+$')
        if not id_regex.match(self.options.identifier):
            inkex.errormsg(_("Please make sure that the animation's name does not contain any other characters than uppercase or lowercase letters from A to Z, numbers from 0 to 9, or underscores."))

        if self.options.repeat == 0:
            self.options.repeat = "infinite"

        if self.options.action == 'remove_anim':
            if self.options.remove_from == 'selected':
                self.remove_selected()
            else:
                self.remove_all()
        elif len(self.svg.selected):
            self.add_animation(self.options.identifier,
                               self.options.duration,
                               self.options.delay,
                               self.options.repeat,
                               self.options.timing)
            if self.options.delay > 0:
                self.add_animation("delay_{0}".format(self.options.identifier),
                                    self.options.delay,
                                    0,
                                    1,
                                    "linear",
                                    True)
        else:
            inkex.errormsg(_('Please select one or more paths to animate.'))

    def add_animation(self, id, duration, delay, repetitions, timing, is_delay_anim=False):

        animation_style_id = "anim_{0}".format(id)
        # inkex.utils.debug('animation_style_id: '+animation_style_id)

        to_animate = []
        for thing in self.svg.selection.rendering_order():
            to_animate.append(thing)

        lengths = [] # relevant lengths of all subsequently animated paths
        for element in to_animate:
            if element.tag == inkex.addNS('path','svg'):
                lengths.append(self.get_animatable_length(element))
            else:
                inkex.errormsg(_('At least one of the selected objects is not a path: {}\nPlease convert all objects to paths before running this extension.\n').format(element.get('id')))
            total_length = sum(lengths)
        #inkex.utils.debug(total_length)
        #inkex.utils.debug(lengths)

        end_percent = 0

        for index, length in enumerate(lengths):

            # if we're creating an animation just to
            # hide a path during delay time
            if is_delay_anim == True:
                # TODO: fix delay!
                inkex.errormsg(_("Sorry, delay isn't working currently. Please set back to zero."))
                sys.exit()
                self.animate_path(to_animate[index], 0, 100, length, length, length, animation_style_id, True)
            else:
                # start where we ended before
                start_percent = end_percent
                # compute new end
                end_percent += round(length/total_length*100, 3)
                if end_percent > 100:
                    end_percent = 100

                self.animate_path(to_animate[index], start_percent, end_percent, length, length, 0, animation_style_id, is_delay_anim)

        animation_style_content = """
        .{id} {{
          animation-duration: {duration}s;
          animation-timing-function: {timing};
          animation-delay: {delay}s;
          animation-iteration-count: {repetitions};
          animation-fill-mode: forwards;
          }}\n""".format(id=animation_style_id, duration=duration, delay=delay, repetitions=repetitions, timing=timing)

        # create general style tag for animation that applies to all objects
        self.add_or_replace_style_tag(animation_style_id, animation_style_content)


    def animate_path(self, element, start_percent, end_percent, length, start_length, end_length, animation_identifier, is_delay_anim=False):

        path_identifier = element.get('id')
        animation_name = path_identifier
        if is_delay_anim:
            animation_name = 'delay_'+path_identifier
        path_style_content = """#{id} {{
    animation-name: {animation_name};
    stroke-dasharray: {length} !important;
}}

@keyframes {animation_name} {{
    0%, {start_percent}% {{stroke-dashoffset: {start_length};}}
    {end_percent}%, 100% {{stroke-dashoffset: {end_length};}}
}}""".format(id=path_identifier,
        animation_name=animation_name,
        length=length,
        start_percent=start_percent,
        start_length=start_length,
        end_percent=end_percent,
        end_length=end_length)
        # inkex.utils.debug(path_style_content)

        # inkex.utils.debug('self.add_or_replace_style_tag('+'pathanim_' + animation_name + ','+path_style_content+')')
        self.add_or_replace_style_tag('pathanim_' + animation_name, path_style_content)
        # only change the element's class when we add the real animation
        if is_delay_anim == False:
            element.set("class", animation_identifier)

    def get_animatable_length(self, elem):
        # csp = elem.path.transform(elem.composed_transform()).to_superpath()
        csp = elem.path.to_superpath()
        subpath_lengths, path_length = csplength(csp)

        # if there are subpaths, we do not want to extend the animation
        # for longer than necessary (subpaths are animated in parallel)
        if len(subpath_lengths) > 1:
            path_length = max([sum(subpath_segments) for subpath_segments in subpath_lengths])

        return path_length

    def add_or_replace_style_tag(self, tag_id, content):

        # inkex.utils.debug(tag_id)
        old_tag = self.get_style_tag(tag_id)
        # inkex.utils.debug('old_tag: '+str(old_tag))
        if old_tag != False:
            (self.root.remove(old_tag))
        style_tag = etree.SubElement(self.root, 'style', {'id': tag_id})
        style_tag.text = content

    def get_style_tags(self):
        style_tags = []
        for element in self.root.getchildren():
            if element.tag == inkex.addNS('style', 'svg'):
                style_tags.append(element)   
        return style_tags

    def get_style_tag(self, id):
       for tag in self.get_style_tags():
           if tag.get('id') == id:
               return tag
       return False


    def remove_all(self):
        inkex.utils.debug('Removing all not implemented yet.')

    def remove_selected(self):

        if len(self.svg.selected) == 0:
            inkex.errormsg(_("Please select items to remove the animation from."))
        inkex.utils.debug('Removing selected not implemented yet.')

if __name__ == '__main__':
    LineAnimator().run()
