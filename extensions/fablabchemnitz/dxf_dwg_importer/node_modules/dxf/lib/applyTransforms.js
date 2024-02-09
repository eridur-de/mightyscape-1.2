"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
/**
 * Apply the transforms to the polyline.
 *
 * @param polyline the polyline
 * @param transform the transforms array
 * @returns the transformed polyline
 */
var _default = function _default(polyline, transforms) {
  transforms.forEach(function (transform) {
    polyline = polyline.map(function (p) {
      // Use a copy to avoid side effects
      var p2 = [p[0], p[1]];
      if (transform.scaleX) {
        p2[0] = p2[0] * transform.scaleX;
      }
      if (transform.scaleY) {
        p2[1] = p2[1] * transform.scaleY;
      }
      if (transform.rotation) {
        var angle = transform.rotation / 180 * Math.PI;
        p2 = [p2[0] * Math.cos(angle) - p2[1] * Math.sin(angle), p2[1] * Math.cos(angle) + p2[0] * Math.sin(angle)];
      }
      if (transform.x) {
        p2[0] = p2[0] + transform.x;
      }
      if (transform.y) {
        p2[1] = p2[1] + transform.y;
      }
      // Observed once in a sample DXF - some cad applications
      // use negative extruxion Z for flipping
      if (transform.extrusionZ === -1) {
        p2[0] = -p2[0];
      }
      return p2;
    });
  });
  return polyline;
};
exports["default"] = _default;