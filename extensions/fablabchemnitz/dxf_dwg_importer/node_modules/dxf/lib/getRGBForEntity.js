"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _colors = _interopRequireDefault(require("./util/colors"));
var _logger = _interopRequireDefault(require("./util/logger"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var _default = function _default(layers, entity) {
  var layerTable = layers[entity.layer];
  if (layerTable) {
    var colorDefinedInEntity = 'colorNumber' in entity && entity.colorNumber !== 256;
    var colorNumber = colorDefinedInEntity ? entity.colorNumber : layerTable.colorNumber;
    var rgb = _colors["default"][colorNumber];
    if (rgb) {
      return rgb;
    } else {
      _logger["default"].warn('Color index', colorNumber, 'invalid, defaulting to black');
      return [0, 0, 0];
    }
  } else {
    _logger["default"].warn('no layer table for layer:' + entity.layer);
    return [0, 0, 0];
  }
};
exports["default"] = _default;