"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.polyfaceOutline = exports.interpolateBSpline = exports["default"] = void 0;
var _bSpline = _interopRequireDefault(require("./util/bSpline"));
var _logger = _interopRequireDefault(require("./util/logger"));
var _createArcForLWPolyline = _interopRequireDefault(require("./util/createArcForLWPolyline"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }
function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }
function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it["return"] != null) it["return"](); } finally { if (didErr) throw err; } } }; }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
/**
 * Rotate a set of points.
 *
 * @param points the points
 * @param angle the rotation angle
 */
var rotate = function rotate(points, angle) {
  return points.map(function (p) {
    return [p[0] * Math.cos(angle) - p[1] * Math.sin(angle), p[1] * Math.cos(angle) + p[0] * Math.sin(angle)];
  });
};

/**
 * Interpolate an ellipse
 * @param cx center X
 * @param cy center Y
 * @param rx radius X
 * @param ry radius Y
 * @param start start angle in radians
 * @param start end angle in radians
 */
var interpolateEllipse = function interpolateEllipse(cx, cy, rx, ry, start, end, rotationAngle) {
  if (end < start) {
    end += Math.PI * 2;
  }

  // ----- Relative points -----

  // Start point
  var points = [];
  var dTheta = Math.PI * 2 / 72;
  var EPS = 1e-6;
  for (var theta = start; theta < end - EPS; theta += dTheta) {
    points.push([Math.cos(theta) * rx, Math.sin(theta) * ry]);
  }
  points.push([Math.cos(end) * rx, Math.sin(end) * ry]);

  // ----- Rotate -----
  if (rotationAngle) {
    points = rotate(points, rotationAngle);
  }

  // ----- Offset center -----
  points = points.map(function (p) {
    return [cx + p[0], cy + p[1]];
  });
  return points;
};

/**
 * Interpolate a b-spline. The algorithm examins the knot vector
 * to create segments for interpolation. The parameterisation value
 * is re-normalised back to [0,1] as that is what the lib expects (
 * and t i de-normalised in the b-spline library)
 *
 * @param controlPoints the control points
 * @param degree the b-spline degree
 * @param knots the knot vector
 * @returns the polyline
 */
var interpolateBSpline = function interpolateBSpline(controlPoints, degree, knots, interpolationsPerSplineSegment, weights) {
  var polyline = [];
  var controlPointsForLib = controlPoints.map(function (p) {
    return [p.x, p.y];
  });
  var segmentTs = [knots[degree]];
  var domain = [knots[degree], knots[knots.length - 1 - degree]];
  for (var k = degree + 1; k < knots.length - degree; ++k) {
    if (segmentTs[segmentTs.length - 1] !== knots[k]) {
      segmentTs.push(knots[k]);
    }
  }
  interpolationsPerSplineSegment = interpolationsPerSplineSegment || 25;
  for (var i = 1; i < segmentTs.length; ++i) {
    var uMin = segmentTs[i - 1];
    var uMax = segmentTs[i];
    for (var _k = 0; _k <= interpolationsPerSplineSegment; ++_k) {
      var u = _k / interpolationsPerSplineSegment * (uMax - uMin) + uMin;
      // Clamp t to 0, 1 to handle numerical precision issues
      var t = (u - domain[0]) / (domain[1] - domain[0]);
      t = Math.max(t, 0);
      t = Math.min(t, 1);
      var p = (0, _bSpline["default"])(t, degree, controlPointsForLib, knots, weights);
      polyline.push(p);
    }
  }
  return polyline;
};
exports.interpolateBSpline = interpolateBSpline;
var polyfaceOutline = function polyfaceOutline(entity) {
  var vertices = [];
  var faces = [];
  var _iterator = _createForOfIteratorHelper(entity.vertices),
    _step;
  try {
    for (_iterator.s(); !(_step = _iterator.n()).done;) {
      var v = _step.value;
      if (v.faces) {
        var _face = {
          indices: [],
          hiddens: []
        };
        var _iterator3 = _createForOfIteratorHelper(v.faces),
          _step3;
        try {
          for (_iterator3.s(); !(_step3 = _iterator3.n()).done;) {
            var i = _step3.value;
            if (i === 0) {
              break;
            }
            // Negative indices signify hidden edges
            _face.indices.push(i < 0 ? -i - 1 : i - 1);
            _face.hiddens.push(i < 0);
          }
        } catch (err) {
          _iterator3.e(err);
        } finally {
          _iterator3.f();
        }
        if ([3, 4].includes(_face.indices.length)) faces.push(_face);
      } else {
        vertices.push({
          x: v.x,
          y: v.y
        });
      }
    }

    // If a segment starts at the end of a previous line, continue it
  } catch (err) {
    _iterator.e(err);
  } finally {
    _iterator.f();
  }
  var polylines = [];
  var segment = function segment(a, b) {
    for (var _i = 0, _polylines = polylines; _i < _polylines.length; _i++) {
      var prev = _polylines[_i];
      if (prev.slice(-1)[0] === a) {
        return prev.push(b);
      }
    }
    polylines.push([a, b]);
  };
  for (var _i2 = 0, _faces = faces; _i2 < _faces.length; _i2++) {
    var face = _faces[_i2];
    for (var beg = 0; beg < face.indices.length; beg++) {
      if (face.hiddens[beg]) {
        continue;
      }
      var end = (beg + 1) % face.indices.length;
      segment(face.indices[beg], face.indices[end]);
    }
  }

  // Sometimes segments are not sequential, in that case
  // we need to find if they can mend gaps between others
  for (var _i3 = 0, _polylines2 = polylines; _i3 < _polylines2.length; _i3++) {
    var a = _polylines2[_i3];
    var _iterator2 = _createForOfIteratorHelper(polylines),
      _step2;
    try {
      for (_iterator2.s(); !(_step2 = _iterator2.n()).done;) {
        var b = _step2.value;
        if (a !== b && a[0] === b.slice(-1)[0]) {
          b.push.apply(b, _toConsumableArray(a.slice(1)));
          a.splice(0, a.length);
          break;
        }
      }
    } catch (err) {
      _iterator2.e(err);
    } finally {
      _iterator2.f();
    }
  }
  return polylines.filter(function (l) {
    return l.length;
  }).map(function (l) {
    return l.map(function (i) {
      return vertices[i];
    }).map(function (v) {
      return [v.x, v.y];
    });
  });
};

/**
 * Convert a parsed DXF entity to a polyline. These can be used to render the
 * the DXF in SVG, Canvas, WebGL etc., without depending on native support
 * of primitive objects (ellispe, spline etc.)
 */
exports.polyfaceOutline = polyfaceOutline;
var _default = function _default(entity, options) {
  options = options || {};
  var polyline;
  if (entity.type === 'LINE') {
    polyline = [[entity.start.x, entity.start.y], [entity.end.x, entity.end.y]];
  }
  if (entity.type === 'LWPOLYLINE' || entity.type === 'POLYLINE') {
    polyline = [];
    if (entity.polyfaceMesh) {
      var _polyline;
      // Only return the first polyline because we can't return many
      (_polyline = polyline).push.apply(_polyline, _toConsumableArray(polyfaceOutline(entity)[0]));
    } else if (entity.polygonMesh) {
      // Do not attempt to render polygon meshes
    } else if (entity.vertices.length) {
      if (entity.closed) {
        entity.vertices = entity.vertices.concat(entity.vertices[0]);
      }
      for (var i = 0, il = entity.vertices.length; i < il - 1; ++i) {
        var from = [entity.vertices[i].x, entity.vertices[i].y];
        var to = [entity.vertices[i + 1].x, entity.vertices[i + 1].y];
        polyline.push(from);
        if (entity.vertices[i].bulge) {
          polyline = polyline.concat((0, _createArcForLWPolyline["default"])(from, to, entity.vertices[i].bulge));
        }
        // The last iteration of the for loop
        if (i === il - 2) {
          polyline.push(to);
        }
      }
    } else {
      _logger["default"].warn('Polyline entity with no vertices');
    }
  }
  if (entity.type === 'CIRCLE') {
    polyline = interpolateEllipse(entity.x, entity.y, entity.r, entity.r, 0, Math.PI * 2);
    if (entity.extrusionZ === -1) {
      polyline = polyline.map(function (p) {
        return [-p[0], p[1]];
      });
    }
  }
  if (entity.type === 'ELLIPSE') {
    var rx = Math.sqrt(entity.majorX * entity.majorX + entity.majorY * entity.majorY);
    var ry = entity.axisRatio * rx;
    var majorAxisRotation = -Math.atan2(-entity.majorY, entity.majorX);
    polyline = interpolateEllipse(entity.x, entity.y, rx, ry, entity.startAngle, entity.endAngle, majorAxisRotation);
    if (entity.extrusionZ === -1) {
      polyline = polyline.map(function (p) {
        return [-p[0], p[1]];
      });
    }
  }
  if (entity.type === 'ARC') {
    // Why on earth DXF has degree start & end angles for arc,
    // and radian start & end angles for ellipses is a mystery
    polyline = interpolateEllipse(entity.x, entity.y, entity.r, entity.r, entity.startAngle, entity.endAngle, undefined, false);

    // I kid you not, ARCs and ELLIPSEs handle this differently,
    // as evidenced by how AutoCAD actually renders these entities
    if (entity.extrusionZ === -1) {
      polyline = polyline.map(function (p) {
        return [-p[0], p[1]];
      });
    }
  }
  if (entity.type === 'SPLINE') {
    polyline = interpolateBSpline(entity.controlPoints, entity.degree, entity.knots, options.interpolationsPerSplineSegment, entity.weights);
  }
  if (!polyline) {
    _logger["default"].warn('unsupported entity for converting to polyline:', entity.type);
    return [];
  }
  return polyline;
};
exports["default"] = _default;