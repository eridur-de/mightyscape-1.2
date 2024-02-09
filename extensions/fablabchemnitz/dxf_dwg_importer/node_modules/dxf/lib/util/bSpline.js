"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _round = _interopRequireDefault(require("./round10"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
/**
 * Copied and ported to code standard as the b-spline library is not maintained any longer.
 * Source:
 * https://github.com/thibauts/b-spline
 * Copyright (c) 2015 Thibaut Séguy <thibaut.seguy@gmail.com>
 */
var _default = function _default(t, degree, points, knots, weights) {
  var n = points.length; // points count
  var d = points[0].length; // point dimensionality

  if (t < 0 || t > 1) {
    throw new Error('t out of bounds [0,1]: ' + t);
  }
  if (degree < 1) throw new Error('degree must be at least 1 (linear)');
  if (degree > n - 1) throw new Error('degree must be less than or equal to point count - 1');
  if (!weights) {
    // build weight vector of length [n]
    weights = [];
    for (var i = 0; i < n; i++) {
      weights[i] = 1;
    }
  }
  if (!knots) {
    // build knot vector of length [n + degree + 1]
    knots = [];
    for (var _i = 0; _i < n + degree + 1; _i++) {
      knots[_i] = _i;
    }
  } else {
    if (knots.length !== n + degree + 1) throw new Error('bad knot vector length');
  }
  var domain = [degree, knots.length - 1 - degree];

  // remap t to the domain where the spline is defined
  var low = knots[domain[0]];
  var high = knots[domain[1]];
  t = t * (high - low) + low;

  // Clamp to the upper &  lower bounds instead of
  // throwing an error like in the original lib
  // https://github.com/bjnortier/dxf/issues/28
  t = Math.max(t, low);
  t = Math.min(t, high);

  // find s (the spline segment) for the [t] value provided
  var s;
  for (s = domain[0]; s < domain[1]; s++) {
    if (t >= knots[s] && t <= knots[s + 1]) {
      break;
    }
  }

  // convert points to homogeneous coordinates
  var v = [];
  for (var _i2 = 0; _i2 < n; _i2++) {
    v[_i2] = [];
    for (var j = 0; j < d; j++) {
      v[_i2][j] = points[_i2][j] * weights[_i2];
    }
    v[_i2][d] = weights[_i2];
  }

  // l (level) goes from 1 to the curve degree + 1
  var alpha;
  for (var l = 1; l <= degree + 1; l++) {
    // build level l of the pyramid
    for (var _i3 = s; _i3 > s - degree - 1 + l; _i3--) {
      alpha = (t - knots[_i3]) / (knots[_i3 + degree + 1 - l] - knots[_i3]);

      // interpolate each component
      for (var _j = 0; _j < d + 1; _j++) {
        v[_i3][_j] = (1 - alpha) * v[_i3 - 1][_j] + alpha * v[_i3][_j];
      }
    }
  }

  // convert back to cartesian and return
  var result = [];
  for (var _i4 = 0; _i4 < d; _i4++) {
    result[_i4] = (0, _round["default"])(v[s][_i4] / v[s][d], -9);
  }
  return result;
};
exports["default"] = _default;