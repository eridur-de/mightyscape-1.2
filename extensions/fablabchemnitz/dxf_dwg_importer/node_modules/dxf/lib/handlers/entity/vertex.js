"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.process = exports["default"] = exports.TYPE = void 0;
var TYPE = 'VERTEX';
exports.TYPE = TYPE;
var ensureFaces = function ensureFaces(entity) {
  entity.faces = entity.faces || [];
  if ('x' in entity && !entity.x) delete entity.x;
  if ('y' in entity && !entity.y) delete entity.y;
  if ('z' in entity && !entity.z) delete entity.z;
};
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
      case 71:
        ensureFaces(entity);
        entity.faces[0] = value;
        break;
      case 72:
        ensureFaces(entity);
        entity.faces[1] = value;
        break;
      case 73:
        ensureFaces(entity);
        entity.faces[2] = value;
        break;
      case 74:
        ensureFaces(entity);
        entity.faces[3] = value;
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