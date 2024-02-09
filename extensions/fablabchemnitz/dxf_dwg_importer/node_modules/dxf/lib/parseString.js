"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _header = _interopRequireDefault(require("./handlers/header"));
var _tables = _interopRequireDefault(require("./handlers/tables"));
var _blocks = _interopRequireDefault(require("./handlers/blocks"));
var _entities = _interopRequireDefault(require("./handlers/entities"));
var _objects = _interopRequireDefault(require("./handlers/objects"));
var _logger = _interopRequireDefault(require("./util/logger"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it["return"] != null) it["return"](); } finally { if (didErr) throw err; } } }; }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) arr2[i] = arr[i]; return arr2; }
// Parse the value into the native representation
var parseValue = function parseValue(type, value) {
  if (type >= 10 && type < 60) {
    return parseFloat(value, 10);
  } else if (type >= 210 && type < 240) {
    return parseFloat(value, 10);
  } else if (type >= 60 && type < 100) {
    return parseInt(value, 10);
  } else {
    return value;
  }
};

// Content lines are alternate lines of type and value
var convertToTypesAndValues = function convertToTypesAndValues(contentLines) {
  var state = 'type';
  var type;
  var typesAndValues = [];
  var _iterator = _createForOfIteratorHelper(contentLines),
    _step;
  try {
    for (_iterator.s(); !(_step = _iterator.n()).done;) {
      var line = _step.value;
      if (state === 'type') {
        type = parseInt(line, 10);
        state = 'value';
      } else {
        typesAndValues.push([type, parseValue(type, line)]);
        state = 'type';
      }
    }
  } catch (err) {
    _iterator.e(err);
  } finally {
    _iterator.f();
  }
  return typesAndValues;
};
var separateSections = function separateSections(tuples) {
  var sectionTuples;
  return tuples.reduce(function (sections, tuple) {
    if (tuple[0] === 0 && tuple[1] === 'SECTION') {
      sectionTuples = [];
    } else if (tuple[0] === 0 && tuple[1] === 'ENDSEC') {
      sections.push(sectionTuples);
      sectionTuples = undefined;
    } else if (sectionTuples !== undefined) {
      sectionTuples.push(tuple);
    }
    return sections;
  }, []);
};

// Each section start with the type tuple, then proceeds
// with the contents of the section
var reduceSection = function reduceSection(acc, section) {
  var sectionType = section[0][1];
  var contentTuples = section.slice(1);
  switch (sectionType) {
    case 'HEADER':
      acc.header = (0, _header["default"])(contentTuples);
      break;
    case 'TABLES':
      acc.tables = (0, _tables["default"])(contentTuples);
      break;
    case 'BLOCKS':
      acc.blocks = (0, _blocks["default"])(contentTuples);
      break;
    case 'ENTITIES':
      acc.entities = (0, _entities["default"])(contentTuples);
      break;
    case 'OBJECTS':
      acc.objects = (0, _objects["default"])(contentTuples);
      break;
    default:
      _logger["default"].warn("Unsupported section: ".concat(sectionType));
  }
  return acc;
};
var _default = function _default(string) {
  var lines = string.split(/\r\n|\r|\n/g);
  var tuples = convertToTypesAndValues(lines);
  var sections = separateSections(tuples);
  var result = sections.reduce(reduceSection, {
    // Start with empty defaults in the event of empty sections
    header: {},
    blocks: [],
    entities: [],
    objects: {
      layouts: []
    },
    tables: {
      layers: {},
      styles: {},
      ltypes: {}
    }
  });
  return result;
};
exports["default"] = _default;