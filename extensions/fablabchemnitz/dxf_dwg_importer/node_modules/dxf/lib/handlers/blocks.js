"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _entities = _interopRequireDefault(require("./entities"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var _default = function _default(tuples) {
  var state;
  var blocks = [];
  var block;
  var entitiesTuples = [];
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    var value = tuple[1];
    if (value === 'BLOCK') {
      state = 'block';
      block = {};
      entitiesTuples = [];
      blocks.push(block);
    } else if (value === 'ENDBLK') {
      if (state === 'entities') {
        block.entities = (0, _entities["default"])(entitiesTuples);
      } else {
        block.entities = [];
      }
      entitiesTuples = undefined;
      state = undefined;
    } else if (state === 'block' && type !== 0) {
      switch (type) {
        case 1:
          block.xref = value;
          break;
        case 2:
          block.name = value;
          break;
        case 10:
          block.x = value;
          break;
        case 20:
          block.y = value;
          break;
        case 30:
          block.z = value;
          break;
        case 67:
          {
            if (value !== 0) block.paperSpace = value;
          }
          break;
        case 410:
          block.layout = value;
          break;
        default:
          break;
      }
    } else if (state === 'block' && type === 0) {
      state = 'entities';
      entitiesTuples.push(tuple);
    } else if (state === 'entities') {
      entitiesTuples.push(tuple);
    }
  });
  return blocks;
};
exports["default"] = _default;