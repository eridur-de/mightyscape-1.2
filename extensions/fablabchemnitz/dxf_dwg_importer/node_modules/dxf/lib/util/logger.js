"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _config = _interopRequireDefault(require("../config"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
function info() {
  if (_config["default"].verbose) {
    console.info.apply(undefined, arguments);
  }
}
function warn() {
  if (_config["default"].verbose) {
    console.warn.apply(undefined, arguments);
  }
}
function error() {
  console.error.apply(undefined, arguments);
}
var _default = {
  info: info,
  warn: warn,
  error: error
};
exports["default"] = _default;