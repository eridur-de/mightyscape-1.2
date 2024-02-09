"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
/**
 * Rotate a points by the given angle.
 *
 * @param points the points
 * @param angle the rotation angle
 */
var _default = function _default(p, angle) {
  return {
    x: p.x * Math.cos(angle) - p.y * Math.sin(angle),
    y: p.y * Math.cos(angle) + p.x * Math.sin(angle)
  };
};
exports["default"] = _default;