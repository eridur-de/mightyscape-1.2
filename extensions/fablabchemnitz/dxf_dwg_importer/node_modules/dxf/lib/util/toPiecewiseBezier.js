"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.multiplicity = exports["default"] = exports.computeInsertions = exports.checkPinned = void 0;
var _insertKnot = _interopRequireDefault(require("./insertKnot"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
/**
 * For a pinned spline, the knots have to be repeated k times
 * (where k is the order), at both the beginning and the end
 */
var checkPinned = function checkPinned(k, knots) {
  // Pinned at the start
  for (var i = 1; i < k; ++i) {
    if (knots[i] !== knots[0]) {
      throw Error("not pinned. order: ".concat(k, " knots: ").concat(knots));
    }
  }
  // Pinned at the end
  for (var _i = knots.length - 2; _i > knots.length - k - 1; --_i) {
    if (knots[_i] !== knots[knots.length - 1]) {
      throw Error("not pinned. order: ".concat(k, " knots: ").concat(knots));
    }
  }
};
exports.checkPinned = checkPinned;
var multiplicity = function multiplicity(knots, index) {
  var m = 1;
  for (var i = index + 1; i < knots.length; ++i) {
    if (knots[i] === knots[index]) {
      ++m;
    } else {
      break;
    }
  }
  return m;
};

/**
 * https://saccade.com/writing/graphics/KnotVectors.pdf
 * A quadratic piecewise Bézier knot vector with seven control points
 * will look like this [0 0 0 1 1 2 2 3 3 3]. In general, in a
 * piecewise Bézier knot vector the first k knots are the same,
 * then each subsequent group of k-1 knots is the same,
 * until you get to the end.
 */
exports.multiplicity = multiplicity;
var computeInsertions = function computeInsertions(k, knots) {
  var inserts = [];
  var i = k;
  while (i < knots.length - k) {
    var knot = knots[i];
    var m = multiplicity(knots, i);
    for (var j = 0; j < k - m - 1; ++j) {
      inserts.push(knot);
    }
    i = i + m;
  }
  return inserts;
};
exports.computeInsertions = computeInsertions;
var _default = function _default(k, controlPoints, knots) {
  checkPinned(k, knots);
  var insertions = computeInsertions(k, knots);
  return insertions.reduce(function (acc, tNew) {
    return (0, _insertKnot["default"])(k, acc.controlPoints, acc.knots, tNew);
  }, {
    controlPoints: controlPoints,
    knots: knots
  });
};
exports["default"] = _default;