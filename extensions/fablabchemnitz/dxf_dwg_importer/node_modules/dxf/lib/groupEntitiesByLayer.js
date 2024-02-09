"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _default = function _default(entities) {
  return entities.reduce(function (acc, entity) {
    var layer = entity.layer;
    if (!acc[layer]) {
      acc[layer] = [];
    }
    acc[layer].push(entity);
    return acc;
  }, {});
};
exports["default"] = _default;