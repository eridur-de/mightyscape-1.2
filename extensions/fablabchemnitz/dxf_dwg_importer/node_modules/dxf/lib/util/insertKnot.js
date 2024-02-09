"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
/**
 * Knot insertion is known as "Boehm's algorithm"
 *
 * https://math.stackexchange.com/questions/417859/convert-a-b-spline-into-bezier-curves
 * code adapted from http://preserve.mactech.com/articles/develop/issue_25/schneider.html
 */
var _default = function _default(k, controlPoints, knots, newKnot) {
  var x = knots;
  var b = controlPoints;
  var n = controlPoints.length;
  var i = 0;
  var foundIndex = false;
  for (var j = 0; j < n + k; j++) {
    if (newKnot > x[j] && newKnot <= x[j + 1]) {
      i = j;
      foundIndex = true;
      break;
    }
  }
  if (!foundIndex) {
    throw new Error('invalid new knot');
  }
  var xHat = [];
  for (var _j = 0; _j < n + k + 1; _j++) {
    if (_j <= i) {
      xHat[_j] = x[_j];
    } else if (_j === i + 1) {
      xHat[_j] = newKnot;
    } else {
      xHat[_j] = x[_j - 1];
    }
  }
  var alpha;
  var bHat = [];
  for (var _j2 = 0; _j2 < n + 1; _j2++) {
    if (_j2 <= i - k + 1) {
      alpha = 1;
    } else if (i - k + 2 <= _j2 && _j2 <= i) {
      if (x[_j2 + k - 1] - x[_j2] === 0) {
        alpha = 0;
      } else {
        alpha = (newKnot - x[_j2]) / (x[_j2 + k - 1] - x[_j2]);
      }
    } else {
      alpha = 0;
    }
    if (alpha === 0) {
      bHat[_j2] = b[_j2 - 1];
    } else if (alpha === 1) {
      bHat[_j2] = b[_j2];
    } else {
      bHat[_j2] = {
        x: (1 - alpha) * b[_j2 - 1].x + alpha * b[_j2].x,
        y: (1 - alpha) * b[_j2 - 1].y + alpha * b[_j2].y
      };
    }
  }
  return {
    controlPoints: bHat,
    knots: xHat
  };
};
exports["default"] = _default;