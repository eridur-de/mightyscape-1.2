"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = exports.process = exports.TYPE = void 0;
var TYPE = 'VERTEX';
exports.TYPE = TYPE;

var process = function process(tuples) {
  return tuples.reduce(function (entity, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 10:
        entity.x = value;
        break;

      case 20:
        entity.y = value;
        break;

      case 30:
        entity.z = value;
        break;

      case 42:
        entity.bulge = value;
        break;

      default:
        break;
    }

    return entity;
  }, {});
};

exports.process = process;
var _default = {
  TYPE: TYPE,
  process: process
};
exports["default"] = _default;