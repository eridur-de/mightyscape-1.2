"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.process = exports["default"] = exports.TYPE = void 0;
var _common = _interopRequireDefault(require("./common"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var TYPE = 'LWPOLYLINE';
exports.TYPE = TYPE;
var process = function process(tuples) {
  var vertex;
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];
    switch (type) {
      case 70:
        entity.closed = (value & 1) === 1;
        break;
      case 10:
        vertex = {
          x: value,
          y: 0
        };
        entity.vertices.push(vertex);
        break;
      case 20:
        vertex.y = value;
        break;
      case 39:
        entity.thickness = value;
        break;
      case 42:
        // Bulge (multiple entries; one entry for each vertex)  (optional; default = 0).
        vertex.bulge = value;
        break;
      default:
        Object.assign(entity, (0, _common["default"])(type, value));
        break;
    }
    return entity;
  }, {
    type: TYPE,
    vertices: []
  });
};
exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports["default"] = _default;