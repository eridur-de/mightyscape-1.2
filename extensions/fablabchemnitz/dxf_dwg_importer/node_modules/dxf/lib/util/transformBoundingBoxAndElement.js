"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _vecks = require("vecks");
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = null == arr ? null : "undefined" != typeof Symbol && arr[Symbol.iterator] || arr["@@iterator"]; if (null != _i) { var _s, _e, _x, _r, _arr = [], _n = !0, _d = !1; try { if (_x = (_i = _i.call(arr)).next, 0 === i) { if (Object(_i) !== _i) return; _n = !1; } else for (; !(_n = (_s = _x.call(_i)).done) && (_arr.push(_s.value), _arr.length !== i); _n = !0); } catch (err) { _d = !0, _e = err; } finally { try { if (!_n && null != _i["return"] && (_r = _i["return"](), Object(_r) !== _r)) return; } finally { if (_d) throw _e; } } return _arr; } }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }
/**
 * Transform the bounding box and the SVG element by the given
 * transforms. The <g> element are created in reverse transform
 * order and the bounding box in the given order.
 */
var _default = function _default(bbox, element, transforms) {
  var transformedElement = '';
  var matrices = transforms.map(function (transform) {
    // Create the transformation matrix
    var tx = transform.x || 0;
    var ty = transform.y || 0;
    var sx = transform.scaleX || 1;
    var sy = transform.scaleY || 1;
    var angle = (transform.rotation || 0) / 180 * Math.PI;
    var cos = Math.cos,
      sin = Math.sin;
    var a, b, c, d, e, f;
    // In DXF an extrusionZ value of -1 denote a tranform around the Y axis.
    if (transform.extrusionZ === -1) {
      a = -sx * cos(angle);
      b = sx * sin(angle);
      c = sy * sin(angle);
      d = sy * cos(angle);
      e = -tx;
      f = ty;
    } else {
      a = sx * cos(angle);
      b = sx * sin(angle);
      c = -sy * sin(angle);
      d = sy * cos(angle);
      e = tx;
      f = ty;
    }
    return [a, b, c, d, e, f];
  });

  // Only transform the bounding box is it is valid (i.e. not Infinity)
  var transformedBBox = new _vecks.Box2();
  if (bbox.valid) {
    var bboxPoints = [{
      x: bbox.min.x,
      y: bbox.min.y
    }, {
      x: bbox.max.x,
      y: bbox.min.y
    }, {
      x: bbox.max.x,
      y: bbox.max.y
    }, {
      x: bbox.min.x,
      y: bbox.max.y
    }];
    matrices.forEach(function (_ref) {
      var _ref2 = _slicedToArray(_ref, 6),
        a = _ref2[0],
        b = _ref2[1],
        c = _ref2[2],
        d = _ref2[3],
        e = _ref2[4],
        f = _ref2[5];
      bboxPoints = bboxPoints.map(function (point) {
        return {
          x: point.x * a + point.y * c + e,
          y: point.x * b + point.y * d + f
        };
      });
    });
    transformedBBox = bboxPoints.reduce(function (acc, point) {
      return acc.expandByPoint(point);
    }, new _vecks.Box2());
  }
  matrices.reverse();
  matrices.forEach(function (_ref3) {
    var _ref4 = _slicedToArray(_ref3, 6),
      a = _ref4[0],
      b = _ref4[1],
      c = _ref4[2],
      d = _ref4[3],
      e = _ref4[4],
      f = _ref4[5];
    transformedElement += "<g transform=\"matrix(".concat(a, " ").concat(b, " ").concat(c, " ").concat(d, " ").concat(e, " ").concat(f, ")\">");
  });
  transformedElement += element;
  matrices.forEach(function (transform) {
    transformedElement += '</g>';
  });
  return {
    bbox: transformedBBox,
    element: transformedElement
  };
};
exports["default"] = _default;