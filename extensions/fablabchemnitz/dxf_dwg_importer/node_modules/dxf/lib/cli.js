#!/usr/bin/env node
"use strict";

var _commander = _interopRequireDefault(require("commander"));
var _fs = _interopRequireDefault(require("fs"));
var _ = require("./");
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
_commander["default"].version(require('../package.json').version).description('Converts a dxf file to a svg file.').arguments('<dxfFile> [svgFile]').option('-v --verbose', 'Verbose output').action(function (dxfFile, svgFile, options) {
  var parsed = (0, _.parseString)(_fs["default"].readFileSync(dxfFile, 'utf-8'));
  if (options.verbose) {
    var groups = (0, _.groupEntitiesByLayer)((0, _.denormalise)(parsed));
    console.log('[layer : number of entities]');
    Object.keys(groups).forEach(function (layer) {
      console.log("".concat(layer, " : ").concat(groups[layer].length));
    });
  }
  _fs["default"].writeFileSync(svgFile || "".concat(dxfFile.split('.').slice(0, -1).join('.'), ".svg"), (0, _.toSVG)(parsed), 'utf-8');
}).parse(process.argv);
if (!process.argv.slice(2).length) {
  _commander["default"].help();
}