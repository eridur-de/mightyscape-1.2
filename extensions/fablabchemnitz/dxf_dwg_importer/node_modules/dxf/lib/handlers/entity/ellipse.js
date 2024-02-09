"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.process = exports["default"] = exports.TYPE = void 0;
var _common = _interopRequireDefault(require("./common"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var TYPE = 'ELLIPSE';
exports.TYPE = TYPE;
var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];
    switch (type) {
      case 10:
        entity.x = value;
        break;
      case 11:
        entity.majorX = value;
        break;
      case 20:
        entity.y = value;
        break;
      case 21:
        entity.majorY = value;
        break;
      case 30:
        entity.z = value;
        break;
      case 31:
        entity.majorZ = value;
        break;
      case 40:
        entity.axisRatio = value;
        break;
      case 41:
        entity.startAngle = value;
        break;
      case 42:
        entity.endAngle = value;
        break;
      default:
        Object.assign(entity, (0, _common["default"])(type, value));
        break;
    }
    return entity;
  }, {
    type: TYPE
  });
};
exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports["default"] = _default;