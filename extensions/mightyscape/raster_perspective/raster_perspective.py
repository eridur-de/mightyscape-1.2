#!/usr/bin/env python3

# Copyright (C) 2022 Samir OUCHENE, samirmath01@gmail.com

import os
import sys

import io
import inkex
from inkex import Image
from PIL import Image as PIL_Image
from PIL.Image import Transform, Resampling
import base64
import numpy


try:
    from base64 import decodebytes
except ImportError:
    from base64 import decodestring as decodebytes


class RasterPerspective(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    @staticmethod
    def mime_to_ext(mime):
        """Return an extension based on the mime type"""
        # Most extensions are automatic (i.e. extension is same as minor part of mime type)
        part = mime.split("/", 1)[1].split("+")[0]
        return (
            "."
            + {
                # These are the non-matching ones.
                "svg+xml": ".svg",
                "jpeg": ".jpg",
                "icon": ".ico",
            }.get(part, part)
        )

    def extract_image(self, node):
        """Extract the node as if it were an image."""
        xlink = node.get("xlink:href")
        if not xlink.startswith("data:"):
            return  # Not embedded image data

        try:
            data = xlink[5:]
            (mimetype, data) = data.split(";", 1)
            (base, data) = data.split(",", 1)
        except ValueError:
            inkex.errormsg("Invalid image format found")
            return

        if base != "base64":
            inkex.errormsg("Can't decode encoding: {}".format(base))
            return

        file_ext = self.mime_to_ext(mimetype)
        return decodebytes(data.encode("utf-8"))

    def find_coeffs(self, source_coords, target_coords):
        matrix = []
        for s, t in zip(source_coords, target_coords):
            matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
            matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
        A = numpy.array(matrix, dtype=float)
        B = numpy.array(source_coords).reshape(8)
        res = numpy.linalg.inv(A.T @ A) @ A.T @ B
        return numpy.array(res).reshape(8)

    def effect(self):
        WARN = "Your selection must contain an image and a path with at least 4 points."
        if len(self.options.ids) < 2:
            inkex.errormsg(WARN)
            exit()
        
        the_image_node, envelope_node = self.svg.selection
        if str(envelope_node) == "image" and str(the_image_node) == "path":
            envelope_node, the_image_node = self.svg.selection #switch

        if str(the_image_node) != "image" and str(envelope_node) != "path":
            inkex.utils.debug(WARN)
            return
        img_width, img_height = the_image_node.width, the_image_node.height

        try:
            unit_to_vp = self.svg.unit_to_viewport
        except AttributeError:
            unit_to_vp = self.svg.uutounit

        try:
            vp_to_unit = self.svg.viewport_to_unit
        except AttributeError:
            vp_to_unit = self.svg.unittouu

        img_width = unit_to_vp(img_width)
        img_height = unit_to_vp(img_height)

        nodes_pts = list(envelope_node.path.control_points)
        node1 = (unit_to_vp(nodes_pts[0][0]), unit_to_vp(nodes_pts[0][1]))
        node2 = (unit_to_vp(nodes_pts[1][0]), unit_to_vp(nodes_pts[1][1]))
        node3 = (unit_to_vp(nodes_pts[2][0]), unit_to_vp(nodes_pts[2][1]))
        node4 = (unit_to_vp(nodes_pts[3][0]), unit_to_vp(nodes_pts[3][1]))

        nodes = [node1, node2, node3, node4]

        xMax = max([node[0] for node in nodes])
        xMin = min([node[0] for node in nodes])
        yMax = max([node[1] for node in nodes])
        yMin = min([node[1] for node in nodes])
        # add some assertions (FIXME)

        img_data = self.extract_image(the_image_node)
        orig_image = PIL_Image.open(io.BytesIO(img_data))
        pil_img_size = orig_image.size
        scale = pil_img_size[0] / img_width

        coeffs = self.find_coeffs(
            [
                (0, 0),
                (img_width * scale, 0),
                (img_width * scale, img_height * scale),
                (0, img_height * scale),
            ],
            [
                (node1[0] - xMin, node1[1] - yMin),
                (node2[0] - xMin, node2[1] - yMin),
                (node3[0] - xMin, node3[1] - yMin),
                (node4[0] - xMin, node4[1] - yMin),
            ],
        )

        W, H = xMax - xMin, yMax - yMin

        final_w, final_h = int(W), int(H)

        # Check if the image has transparency
        hasTransparency = orig_image.mode in ("RGBA", "LA") or (
            orig_image.mode == "P" and "transparency" in orig_image.info
        )

        transp_img = orig_image

        # If the original image is not transparent, create a new image with alpha channel
        if not hasTransparency:
            transp_img = PIL_Image.new("RGBA", orig_image.size)
            transp_img.format = "PNG"
            transp_img.paste(orig_image)

        image = transp_img.transform(
            (final_w, final_h), Transform.PERSPECTIVE, coeffs, Resampling.BICUBIC
        )

        obj = inkex.Image()
        obj.set("x", vp_to_unit(xMin))
        obj.set("y", vp_to_unit(yMin))
        obj.set("width", vp_to_unit(final_w))
        obj.set("height", vp_to_unit(final_h))
        # embed the transformed image
        persp_img_data = io.BytesIO()
        image.save(persp_img_data, transp_img.format)
        mime = PIL_Image.MIME[transp_img.format]
        b64 = base64.b64encode(persp_img_data.getvalue()).decode("utf-8")
        uri = f"data:{mime};base64,{b64}"
        obj.set("xlink:href", uri)
        self.svg.add(obj)


RasterPerspective = RasterPerspective()
RasterPerspective.run()
