"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.process = exports["default"] = exports.assign = exports.TYPE = void 0;
var _common = _interopRequireDefault(require("./common"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var TYPE = 'MTEXT';
exports.TYPE = TYPE;
var simpleCodes = {
  10: 'x',
  20: 'y',
  30: 'z',
  40: 'nominalTextHeight',
  41: 'refRectangleWidth',
  71: 'attachmentPoint',
  72: 'drawingDirection',
  7: 'styleName',
  11: 'xAxisX',
  21: 'xAxisY',
  31: 'xAxisZ',
  42: 'horizontalWidth',
  43: 'verticalHeight',
  73: 'lineSpacingStyle',
  44: 'lineSpacingFactor',
  90: 'backgroundFill',
  420: 'bgColorRGB0',
  421: 'bgColorRGB1',
  422: 'bgColorRGB2',
  423: 'bgColorRGB3',
  424: 'bgColorRGB4',
  425: 'bgColorRGB5',
  426: 'bgColorRGB6',
  427: 'bgColorRGB7',
  428: 'bgColorRGB8',
  429: 'bgColorRGB9',
  430: 'bgColorName0',
  431: 'bgColorName1',
  432: 'bgColorName2',
  433: 'bgColorName3',
  434: 'bgColorName4',
  435: 'bgColorName5',
  436: 'bgColorName6',
  437: 'bgColorName7',
  438: 'bgColorName8',
  439: 'bgColorName9',
  45: 'fillBoxStyle',
  63: 'bgFillColor',
  441: 'bgFillTransparency',
  75: 'columnType',
  76: 'columnCount',
  78: 'columnFlowReversed',
  79: 'columnAutoheight',
  48: 'columnWidth',
  49: 'columnGutter',
  50: 'columnHeights'
};
var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];
    assign(entity, type, value);
    return entity;
  }, {
    type: TYPE,
    string: ''
  });
};
exports.process = process;
var assign = function assign(entity, type, value) {
  if (simpleCodes[type] !== undefined) {
    entity[simpleCodes[type]] = value;
  } else if (type === 1 || type === 3) {
    entity.string += value;
  } else if (type === 50) {
    // Rotation angle in radians
    entity.xAxisX = Math.cos(value);
    entity.xAxisY = Math.sin(value);
  } else {
    Object.assign(entity, (0, _common["default"])(type, value));
  }
  return entity;
};
exports.assign = assign;
var _default = {
  TYPE: TYPE,
  process: process,
  assign: assign
};
exports["default"] = _default;