"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
/**
 * Convert an RGB array to a CSS string definition.
 * Converts white lines to black as the default.
 */
var _default = function _default(rgb) {
  if (rgb[0] === 255 && rgb[1] === 255 && rgb[2] === 255) {
    return 'rgb(0, 0, 0)';
  } else {
    return "rgb(".concat(rgb[0], ", ").concat(rgb[1], ", ").concat(rgb[2], ")");
  }
};
exports["default"] = _default;