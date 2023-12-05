#!/usr/bin/env python3
"""
Inkscape plugin: delete the selected object(s) and any objects on top of them.

I.E. delete the selected node(s) and any other nodes that are completely
within the bounding-boxes of the selected nodes that have a greater z-order

Simply put, you select a "background" rectangle, then use this plugin to
delete it and everything that appears on top of it.
"""

import collections
import subprocess
import os
import pprint
import inkex

Point = collections.namedtuple('Point', ['x', 'y'])

Box = collections.namedtuple('Box', ['tl', 'tr', 'br', 'bl'])
# tl=top left, tr=top right, br=bottom right, bl=bottom left

nodeInfo = collections.namedtuple('nodeInfo',
                                     ['x', 'y', 'width', 'height'])


def contains(outer, inner):
    """ Return true if the Box inner is completely within the Box outer """
    return inner.tl.x >= outer.tl.x and inner.tl.y >= outer.tl.y and \
           inner.br.x <= outer.br.x and inner.br.y <= outer.br.y


class DeleteAbove(inkex.EffectExtension):
    """ Delete the selected node and everything above it """
    node_info = None

    def load_node_info(self):
        """ Ask inkscape for information about all object bounding boxes """
        node_info = dict()
        command = ['inkscape', '--query-all', self.options.input_file]
        check_output = subprocess.check_output

        with open(os.devnull, 'w') as null:
            for line in check_output(command, stderr=null).splitlines():
                raw_id, raw_x, raw_y, raw_width, raw_height = line.split(b',')
                node_info[raw_id.decode("UTF-8")] = nodeInfo(float(raw_x),
                                                   float(raw_y),
                                                   float(raw_width),
                                                   float(raw_height))

        self.node_info = node_info
        return

    def remove(self, node):
        """ Remove the specified node from the document tree """
        parent = node.getparent()
        if parent is None:
            return
        parent.remove(node)

    def bbox(self, node):
        """ Return the bounding-box of the given node """
        node_id = node.get('id')
        #inkex.utils.debug("Check if " + str(node_id) + " is in " + str(self.node_info))
        info = self.node_info[node_id]           
        
        x = info.x
        y = info.y
        width = info.width
        height = info.height

        return Box(Point(x, y),
                   Point(x + width, y),
                   Point(x + width, y + height),
                   Point(x, y + height))

    def effect(self):
        """
        For every selected node, remove it and all items on top of it
        """
        self.load_node_info()
        nodes_to_remove = list()

        for id, node in self.svg.selected.items():
            selected_node_bbox = self.bbox(node)
            nodes_to_remove.append(node)

            # search the document tree for the selected node
            # when found, every subsequent node will be "above" it.
            # (i.e. svg documents draw from the background up, so a background
            # node will appear first, then nodes that are progressively
            # closer to the viewer will appear subsequently in the svg file)
            found_selected_node = False
            for node in self.document.getiterator():
                if not found_selected_node:
                    if node == node:
                        found_selected_node = True
                    continue
                # Hereafter we are iterating over all nodes above the
                # selected node. We need to delete them if they appear to
                # be "on top of" the selection (i.e. within the bounding box
                # of the selection)
                try:
                    node_bbox = self.bbox(node)
                except KeyError:
                    continue
                if contains(selected_node_bbox, node_bbox):
                    nodes_to_remove.append(node)

        # Now we remove the items we've previously found. Search and remove
        # need to be separate bulk steps because tree search is disrupted by
        # tree modification
        for condemned_node in set(nodes_to_remove):
            self.remove(condemned_node)

if __name__ == '__main__':
    if False:
        # Some tools for debug use
        PPRINTER = pprint.PrettyPrinter(indent=4)
        FMT = PPRINTER.pformat
        DUMP = lambda obj: inkex.debug(FMT(obj))

    DeleteAbove().run()