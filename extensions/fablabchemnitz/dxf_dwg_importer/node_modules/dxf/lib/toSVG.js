"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.piecewiseToPaths = exports["default"] = void 0;
var _vecks = require("vecks");
var _entityToPolyline = _interopRequireDefault(require("./entityToPolyline"));
var _denormalise = _interopRequireDefault(require("./denormalise"));
var _getRGBForEntity = _interopRequireDefault(require("./getRGBForEntity"));
var _logger = _interopRequireDefault(require("./util/logger"));
var _rotate = _interopRequireDefault(require("./util/rotate"));
var _rgbToColorAttribute = _interopRequireDefault(require("./util/rgbToColorAttribute"));
var _toPiecewiseBezier = _interopRequireWildcard(require("./util/toPiecewiseBezier"));
var _transformBoundingBoxAndElement = _interopRequireDefault(require("./util/transformBoundingBoxAndElement"));
function _getRequireWildcardCache(nodeInterop) { if (typeof WeakMap !== "function") return null; var cacheBabelInterop = new WeakMap(); var cacheNodeInterop = new WeakMap(); return (_getRequireWildcardCache = function _getRequireWildcardCache(nodeInterop) { return nodeInterop ? cacheNodeInterop : cacheBabelInterop; })(nodeInterop); }
function _interopRequireWildcard(obj, nodeInterop) { if (!nodeInterop && obj && obj.__esModule) { return obj; } if (obj === null || _typeof(obj) !== "object" && typeof obj !== "function") { return { "default": obj }; } var cache = _getRequireWildcardCache(nodeInterop); if (cache && cache.has(obj)) { return cache.get(obj); } var newObj = {}; var hasPropertyDescriptor = Object.defineProperty && Object.getOwnPropertyDescriptor; for (var key in obj) { if (key !== "default" && Object.prototype.hasOwnProperty.call(obj, key)) { var desc = hasPropertyDescriptor ? Object.getOwnPropertyDescriptor(obj, key) : null; if (desc && (desc.get || desc.set)) { Object.defineProperty(newObj, key, desc); } else { newObj[key] = obj[key]; } } } newObj["default"] = obj; if (cache) { cache.set(obj, newObj); } return newObj; }
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = null == arr ? null : "undefined" != typeof Symbol && arr[Symbol.iterator] || arr["@@iterator"]; if (null != _i) { var _s, _e, _x, _r, _arr = [], _n = !0, _d = !1; try { if (_x = (_i = _i.call(arr)).next, 0 === i) { if (Object(_i) !== _i) return; _n = !1; } else for (; !(_n = (_s = _x.call(_i)).done) && (_arr.push(_s.value), _arr.length !== i); _n = !0); } catch (err) { _d = !0, _e = err; } finally { try { if (!_n && null != _i["return"] && (_r = _i["return"](), Object(_r) !== _r)) return; } finally { if (_d) throw _e; } } return _arr; } }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }
var addFlipXIfApplicable = function addFlipXIfApplicable(entity, _ref) {
  var bbox = _ref.bbox,
    element = _ref.element;
  if (entity.extrusionZ === -1) {
    return {
      bbox: new _vecks.Box2().expandByPoint({
        x: -bbox.min.x,
        y: bbox.min.y
      }).expandByPoint({
        x: -bbox.max.x,
        y: bbox.max.y
      }),
      element: "<g transform=\"matrix(-1 0 0 1 0 0)\">\n        ".concat(element, "\n      </g>")
    };
  } else {
    return {
      bbox: bbox,
      element: element
    };
  }
};

/**
 * Create a <path /> element. Interpolates curved entities.
 */
var polyline = function polyline(entity) {
  var vertices = (0, _entityToPolyline["default"])(entity);
  var bbox = vertices.reduce(function (acc, _ref2) {
    var _ref3 = _slicedToArray(_ref2, 2),
      x = _ref3[0],
      y = _ref3[1];
    return acc.expandByPoint({
      x: x,
      y: y
    });
  }, new _vecks.Box2());
  var d = vertices.reduce(function (acc, point, i) {
    acc += i === 0 ? 'M' : 'L';
    acc += point[0] + ',' + point[1];
    return acc;
  }, '');
  // Empirically it appears that flipping horzontally does not apply to polyline
  return (0, _transformBoundingBoxAndElement["default"])(bbox, "<path d=\"".concat(d, "\" />"), entity.transforms);
};

/**
 * Create a <circle /> element for the CIRCLE entity.
 */
var circle = function circle(entity) {
  var bbox0 = new _vecks.Box2().expandByPoint({
    x: entity.x + entity.r,
    y: entity.y + entity.r
  }).expandByPoint({
    x: entity.x - entity.r,
    y: entity.y - entity.r
  });
  var element0 = "<circle cx=\"".concat(entity.x, "\" cy=\"").concat(entity.y, "\" r=\"").concat(entity.r, "\" />");
  var _addFlipXIfApplicable = addFlipXIfApplicable(entity, {
      bbox: bbox0,
      element: element0
    }),
    bbox = _addFlipXIfApplicable.bbox,
    element = _addFlipXIfApplicable.element;
  return (0, _transformBoundingBoxAndElement["default"])(bbox, element, entity.transforms);
};

/**
 * Create a a <path d="A..." /> or <ellipse /> element for the ARC or ELLIPSE
 * DXF entity (<ellipse /> if start and end point are the same).
 */
var ellipseOrArc = function ellipseOrArc(cx, cy, majorX, majorY, axisRatio, startAngle, endAngle, flipX) {
  var rx = Math.sqrt(majorX * majorX + majorY * majorY);
  var ry = axisRatio * rx;
  var rotationAngle = -Math.atan2(-majorY, majorX);
  var bbox = bboxEllipseOrArc(cx, cy, majorX, majorY, axisRatio, startAngle, endAngle, flipX);
  if (Math.abs(startAngle - endAngle) < 1e-9 || Math.abs(startAngle - endAngle + Math.PI * 2) < 1e-9) {
    // Use a native <ellipse> when start and end angles are the same, and
    // arc paths with same start and end points don't render (at least on Safari)
    var element = "<g transform=\"rotate(".concat(rotationAngle / Math.PI * 180, " ").concat(cx, ", ").concat(cy, ")\">\n      <ellipse cx=\"").concat(cx, "\" cy=\"").concat(cy, "\" rx=\"").concat(rx, "\" ry=\"").concat(ry, "\" />\n    </g>");
    return {
      bbox: bbox,
      element: element
    };
  } else {
    var startOffset = (0, _rotate["default"])({
      x: Math.cos(startAngle) * rx,
      y: Math.sin(startAngle) * ry
    }, rotationAngle);
    var startPoint = {
      x: cx + startOffset.x,
      y: cy + startOffset.y
    };
    var endOffset = (0, _rotate["default"])({
      x: Math.cos(endAngle) * rx,
      y: Math.sin(endAngle) * ry
    }, rotationAngle);
    var endPoint = {
      x: cx + endOffset.x,
      y: cy + endOffset.y
    };
    var adjustedEndAngle = endAngle < startAngle ? endAngle + Math.PI * 2 : endAngle;
    var largeArcFlag = adjustedEndAngle - startAngle < Math.PI ? 0 : 1;
    var d = "M ".concat(startPoint.x, " ").concat(startPoint.y, " A ").concat(rx, " ").concat(ry, " ").concat(rotationAngle / Math.PI * 180, " ").concat(largeArcFlag, " 1 ").concat(endPoint.x, " ").concat(endPoint.y);
    var _element = "<path d=\"".concat(d, "\" />");
    return {
      bbox: bbox,
      element: _element
    };
  }
};

/**
 * Compute the bounding box of an elliptical arc, given the DXF entity parameters
 */
var bboxEllipseOrArc = function bboxEllipseOrArc(cx, cy, majorX, majorY, axisRatio, startAngle, endAngle, flipX) {
  // The bounding box will be defined by the starting point of the ellipse, and ending point,
  // and any extrema on the ellipse that are between startAngle and endAngle.
  // The extrema are found by setting either the x or y component of the ellipse's
  // tangent vector to zero and solving for the angle.

  // Ensure start and end angles are > 0 and well-ordered
  while (startAngle < 0) startAngle += Math.PI * 2;
  while (endAngle <= startAngle) endAngle += Math.PI * 2;

  // When rotated, the extrema of the ellipse will be found at these angles
  var angles = [];
  if (Math.abs(majorX) < 1e-12 || Math.abs(majorY) < 1e-12) {
    // Special case for majorX or majorY = 0
    for (var i = 0; i < 4; i++) {
      angles.push(i / 2 * Math.PI);
    }
  } else {
    // reference https://github.com/bjnortier/dxf/issues/47#issuecomment-545915042
    angles[0] = Math.atan(-majorY * axisRatio / majorX) - Math.PI; // Ensure angles < 0
    angles[1] = Math.atan(majorX * axisRatio / majorY) - Math.PI;
    angles[2] = angles[0] - Math.PI;
    angles[3] = angles[1] - Math.PI;
  }

  // Remove angles not falling between start and end
  for (var _i2 = 4; _i2 >= 0; _i2--) {
    while (angles[_i2] < startAngle) angles[_i2] += Math.PI * 2;
    if (angles[_i2] > endAngle) {
      angles.splice(_i2, 1);
    }
  }

  // Also to consider are the starting and ending points:
  angles.push(startAngle);
  angles.push(endAngle);

  // Compute points lying on the unit circle at these angles
  var pts = angles.map(function (a) {
    return {
      x: Math.cos(a),
      y: Math.sin(a)
    };
  });

  // Transformation matrix, formed by the major and minor axes
  var M = [[majorX, -majorY * axisRatio], [majorY, majorX * axisRatio]];

  // Rotate, scale, and translate points
  var rotatedPts = pts.map(function (p) {
    return {
      x: p.x * M[0][0] + p.y * M[0][1] + cx,
      y: p.x * M[1][0] + p.y * M[1][1] + cy
    };
  });

  // Compute extents of bounding box
  var bbox = rotatedPts.reduce(function (acc, p) {
    acc.expandByPoint(p);
    return acc;
  }, new _vecks.Box2());
  return bbox;
};

/**
 * An ELLIPSE is defined by the major axis, convert to X and Y radius with
 * a rotation angle
 */
var ellipse = function ellipse(entity) {
  var _ellipseOrArc = ellipseOrArc(entity.x, entity.y, entity.majorX, entity.majorY, entity.axisRatio, entity.startAngle, entity.endAngle),
    bbox0 = _ellipseOrArc.bbox,
    element0 = _ellipseOrArc.element;
  var _addFlipXIfApplicable2 = addFlipXIfApplicable(entity, {
      bbox: bbox0,
      element: element0
    }),
    bbox = _addFlipXIfApplicable2.bbox,
    element = _addFlipXIfApplicable2.element;
  return (0, _transformBoundingBoxAndElement["default"])(bbox, element, entity.transforms);
};

/**
 * An ARC is an ellipse with equal radii
 */
var arc = function arc(entity) {
  var _ellipseOrArc2 = ellipseOrArc(entity.x, entity.y, entity.r, 0, 1, entity.startAngle, entity.endAngle, entity.extrusionZ === -1),
    bbox0 = _ellipseOrArc2.bbox,
    element0 = _ellipseOrArc2.element;
  var _addFlipXIfApplicable3 = addFlipXIfApplicable(entity, {
      bbox: bbox0,
      element: element0
    }),
    bbox = _addFlipXIfApplicable3.bbox,
    element = _addFlipXIfApplicable3.element;
  return (0, _transformBoundingBoxAndElement["default"])(bbox, element, entity.transforms);
};
var piecewiseToPaths = function piecewiseToPaths(k, knots, controlPoints) {
  var paths = [];
  var controlPointIndex = 0;
  var knotIndex = k;
  while (knotIndex < knots.length - k + 1) {
    var m = (0, _toPiecewiseBezier.multiplicity)(knots, knotIndex);
    var cp = controlPoints.slice(controlPointIndex, controlPointIndex + k);
    if (k === 4) {
      paths.push("<path d=\"M ".concat(cp[0].x, " ").concat(cp[0].y, " C ").concat(cp[1].x, " ").concat(cp[1].y, " ").concat(cp[2].x, " ").concat(cp[2].y, " ").concat(cp[3].x, " ").concat(cp[3].y, "\" />"));
    } else if (k === 3) {
      paths.push("<path d=\"M ".concat(cp[0].x, " ").concat(cp[0].y, " Q ").concat(cp[1].x, " ").concat(cp[1].y, " ").concat(cp[2].x, " ").concat(cp[2].y, "\" />"));
    }
    controlPointIndex += m;
    knotIndex += m;
  }
  return paths;
};
exports.piecewiseToPaths = piecewiseToPaths;
var bezier = function bezier(entity) {
  var bbox = new _vecks.Box2();
  entity.controlPoints.forEach(function (p) {
    bbox = bbox.expandByPoint(p);
  });
  var k = entity.degree + 1;
  var piecewise = (0, _toPiecewiseBezier["default"])(k, entity.controlPoints, entity.knots);
  var paths = piecewiseToPaths(k, piecewise.knots, piecewise.controlPoints);
  var element = "<g>".concat(paths.join(''), "</g>");
  return (0, _transformBoundingBoxAndElement["default"])(bbox, element, entity.transforms);
};

/**
 * Switcth the appropriate function on entity type. CIRCLE, ARC and ELLIPSE
 * produce native SVG elements, the rest produce interpolated polylines.
 */
var entityToBoundsAndElement = function entityToBoundsAndElement(entity) {
  switch (entity.type) {
    case 'CIRCLE':
      return circle(entity);
    case 'ELLIPSE':
      return ellipse(entity);
    case 'ARC':
      return arc(entity);
    case 'SPLINE':
      {
        var hasWeights = entity.weights && entity.weights.some(function (w) {
          return w !== 1;
        });
        if ((entity.degree === 2 || entity.degree === 3) && !hasWeights) {
          try {
            return bezier(entity);
          } catch (err) {
            return polyline(entity);
          }
        } else {
          return polyline(entity);
        }
      }
    case 'LINE':
    case 'LWPOLYLINE':
    case 'POLYLINE':
      {
        return polyline(entity);
      }
    default:
      _logger["default"].warn('entity type not supported in SVG rendering:', entity.type);
      return null;
  }
};
var _default = function _default(parsed) {
  var entities = (0, _denormalise["default"])(parsed);
  var _entities$reduce = entities.reduce(function (acc, entity, i) {
      var rgb = (0, _getRGBForEntity["default"])(parsed.tables.layers, entity);
      var boundsAndElement = entityToBoundsAndElement(entity);
      // Ignore entities like MTEXT that don't produce SVG elements
      if (boundsAndElement) {
        var _bbox = boundsAndElement.bbox,
          element = boundsAndElement.element;
        // Ignore invalid bounding boxes
        if (_bbox.valid) {
          acc.bbox.expandByPoint(_bbox.min);
          acc.bbox.expandByPoint(_bbox.max);
        }
        acc.elements.push("<g stroke=\"".concat((0, _rgbToColorAttribute["default"])(rgb), "\">").concat(element, "</g>"));
      }
      return acc;
    }, {
      bbox: new _vecks.Box2(),
      elements: []
    }),
    bbox = _entities$reduce.bbox,
    elements = _entities$reduce.elements;
  var viewBox = bbox.valid ? {
    x: bbox.min.x,
    y: -bbox.max.y,
    width: bbox.max.x - bbox.min.x,
    height: bbox.max.y - bbox.min.y
  } : {
    x: 0,
    y: 0,
    width: 0,
    height: 0
  };
  return "<?xml version=\"1.0\"?>\n<svg\n  xmlns=\"http://www.w3.org/2000/svg\"\n  xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"1.1\"\n  preserveAspectRatio=\"xMinYMin meet\"\n  viewBox=\"".concat(viewBox.x, " ").concat(viewBox.y, " ").concat(viewBox.width, " ").concat(viewBox.height, "\"\n  width=\"100%\" height=\"100%\"\n>\n  <g stroke=\"#000000\" stroke-width=\"0.1%\" fill=\"none\" transform=\"matrix(1,0,0,-1,0,0)\">\n    ").concat(elements.join('\n'), "\n  </g>\n</svg>");
};
exports["default"] = _default;