"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _logger = _interopRequireDefault(require("./util/logger"));
var _parseString = _interopRequireDefault(require("./parseString"));
var _denormalise2 = _interopRequireDefault(require("./denormalise"));
var _toSVG2 = _interopRequireDefault(require("./toSVG"));
var _toPolylines2 = _interopRequireDefault(require("./toPolylines"));
var _groupEntitiesByLayer = _interopRequireDefault(require("./groupEntitiesByLayer"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, _toPropertyKey(descriptor.key), descriptor); } }
function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }
function _toPropertyKey(arg) { var key = _toPrimitive(arg, "string"); return _typeof(key) === "symbol" ? key : String(key); }
function _toPrimitive(input, hint) { if (_typeof(input) !== "object" || input === null) return input; var prim = input[Symbol.toPrimitive]; if (prim !== undefined) { var res = prim.call(input, hint || "default"); if (_typeof(res) !== "object") return res; throw new TypeError("@@toPrimitive must return a primitive value."); } return (hint === "string" ? String : Number)(input); }
var Helper = /*#__PURE__*/function () {
  function Helper(contents) {
    _classCallCheck(this, Helper);
    if (!(typeof contents === 'string')) {
      throw Error('Helper constructor expects a DXF string');
    }
    this._contents = contents;
    this._parsed = null;
    this._denormalised = null;
  }
  _createClass(Helper, [{
    key: "parse",
    value: function parse() {
      this._parsed = (0, _parseString["default"])(this._contents);
      _logger["default"].info('parsed:', this.parsed);
      return this._parsed;
    }
  }, {
    key: "parsed",
    get: function get() {
      if (this._parsed === null) {
        this.parse();
      }
      return this._parsed;
    }
  }, {
    key: "denormalise",
    value: function denormalise() {
      this._denormalised = (0, _denormalise2["default"])(this.parsed);
      _logger["default"].info('denormalised:', this._denormalised);
      return this._denormalised;
    }
  }, {
    key: "denormalised",
    get: function get() {
      if (!this._denormalised) {
        this.denormalise();
      }
      return this._denormalised;
    }
  }, {
    key: "group",
    value: function group() {
      this._groups = (0, _groupEntitiesByLayer["default"])(this.denormalised);
    }
  }, {
    key: "groups",
    get: function get() {
      if (!this._groups) {
        this.group();
      }
      return this._groups;
    }
  }, {
    key: "toSVG",
    value: function toSVG() {
      return (0, _toSVG2["default"])(this.parsed);
    }
  }, {
    key: "toPolylines",
    value: function toPolylines() {
      return (0, _toPolylines2["default"])(this.parsed);
    }
  }]);
  return Helper;
}();
exports["default"] = Helper;