"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.process = exports["default"] = exports.TYPE = void 0;
var _common = _interopRequireDefault(require("./common"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var TYPE = 'SOLID';
exports.TYPE = TYPE;
var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];
    switch (type) {
      case 10:
        entity.corners[0].x = value;
        break;
      case 20:
        entity.corners[0].y = value;
        break;
      case 30:
        entity.corners[0].z = value;
        break;
      case 11:
        entity.corners[1].x = value;
        break;
      case 21:
        entity.corners[1].y = value;
        break;
      case 31:
        entity.corners[1].z = value;
        break;
      case 12:
        entity.corners[2].x = value;
        break;
      case 22:
        entity.corners[2].y = value;
        break;
      case 32:
        entity.corners[2].z = value;
        break;
      case 13:
        entity.corners[3].x = value;
        break;
      case 23:
        entity.corners[3].y = value;
        break;
      case 33:
        entity.corners[3].z = value;
        break;
      case 39:
        entity.thickness = value;
        break;
      default:
        Object.assign(entity, (0, _common["default"])(type, value));
        break;
    }
    return entity;
  }, {
    type: TYPE,
    corners: [{}, {}, {}, {}]
  });
};
exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports["default"] = _default;