"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _logger = _interopRequireDefault(require("../util/logger"));
var _point = _interopRequireDefault(require("./entity/point"));
var _line = _interopRequireDefault(require("./entity/line"));
var _lwpolyline = _interopRequireDefault(require("./entity/lwpolyline"));
var _polyline = _interopRequireDefault(require("./entity/polyline"));
var _vertex = _interopRequireDefault(require("./entity/vertex"));
var _circle = _interopRequireDefault(require("./entity/circle"));
var _arc = _interopRequireDefault(require("./entity/arc"));
var _ellipse = _interopRequireDefault(require("./entity/ellipse"));
var _spline = _interopRequireDefault(require("./entity/spline"));
var _solid = _interopRequireDefault(require("./entity/solid"));
var _hatch = _interopRequireDefault(require("./entity/hatch"));
var _mtext = _interopRequireDefault(require("./entity/mtext"));
var _attdef = _interopRequireDefault(require("./entity/attdef"));
var _attrib = _interopRequireDefault(require("./entity/attrib"));
var _insert = _interopRequireDefault(require("./entity/insert"));
var _threeDFace = _interopRequireDefault(require("./entity/threeDFace"));
var _dimension = _interopRequireDefault(require("./entity/dimension"));
var _text = _interopRequireDefault(require("./entity/text"));
var _viewport = _interopRequireDefault(require("./entity/viewport"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var handlers = [_point["default"], _line["default"], _lwpolyline["default"], _polyline["default"], _vertex["default"], _circle["default"], _arc["default"], _ellipse["default"], _spline["default"], _solid["default"], _hatch["default"], _mtext["default"], _attdef["default"], _attrib["default"], _text["default"], _insert["default"], _dimension["default"], _threeDFace["default"], _viewport["default"]].reduce(function (acc, mod) {
  acc[mod.TYPE] = mod;
  return acc;
}, {});
var _default = function _default(tuples) {
  var entities = [];
  var entityGroups = [];
  var currentEntityTuples;

  // First group them together for easy processing
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    if (type === 0) {
      currentEntityTuples = [];
      entityGroups.push(currentEntityTuples);
    }
    currentEntityTuples.push(tuple);
  });
  var currentPolyline;
  entityGroups.forEach(function (tuples) {
    var entityType = tuples[0][1];
    var contentTuples = tuples.slice(1);
    if (handlers[entityType] !== undefined) {
      var e = handlers[entityType].process(contentTuples);
      // "POLYLINE" cannot be parsed in isolation, it is followed by
      // N "VERTEX" entities and ended with a "SEQEND" entity.
      // Essentially we convert POLYLINE to LWPOLYLINE - the extra
      // vertex flags are not supported
      if (entityType === 'POLYLINE') {
        currentPolyline = e;
        entities.push(e);
      } else if (entityType === 'VERTEX') {
        if (currentPolyline) {
          currentPolyline.vertices.push(e);
        } else {
          _logger["default"].error('ignoring invalid VERTEX entity');
        }
      } else if (entityType === 'SEQEND') {
        currentPolyline = undefined;
      } else {
        // All other entities
        entities.push(e);
      }
    } else {
      _logger["default"].warn('unsupported type in ENTITIES section:', entityType);
    }
  });
  return entities;
};
exports["default"] = _default;