"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;

var _logger = _interopRequireDefault(require("../util/logger"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }

var layerHandler = function layerHandler(tuples) {
  return tuples.reduce(function (layer, tuple) {
    var type = tuple[0];
    var value = tuple[1]; // https://www.autodesk.com/techpubs/autocad/acad2000/dxf/layer_dxf_04.htm

    switch (type) {
      case 2:
        layer.name = value;
        break;

      case 6:
        layer.lineTypeName = value;
        break;

      case 62:
        layer.colorNumber = value;
        break;

      case 70:
        layer.flags = value;
        break;

      case 290:
        layer.plot = parseInt(value) !== 0;
        break;

      case 370:
        layer.lineWeightEnum = value;
        break;

      default:
    }

    return layer;
  }, {
    type: 'LAYER'
  });
};

var styleHandler = function styleHandler(tuples) {
  return tuples.reduce(function (style, tuple) {
    var type = tuple[0];
    var value = tuple[1];

    switch (type) {
      case 2:
        style.name = value;
        break;

      case 6:
        style.lineTypeName = value;
        break;

      case 40:
        style.fixedTextHeight = value;
        break;

      case 41:
        style.widthFactor = value;
        break;

      case 50:
        style.obliqueAngle = value;
        break;

      case 71:
        style.flags = value;
        break;

      case 42:
        style.lastHeightUsed = value;
        break;

      case 3:
        style.primaryFontFileName = value;
        break;

      case 4:
        style.bigFontFileName = value;
        break;

      default:
    }

    return style;
  }, {
    type: 'STYLE'
  });
};

var tableHandler = function tableHandler(tuples, tableType, handler) {
  var tableRowsTuples = [];
  var tableRowTuples;
  tuples.forEach(function (tuple) {
    var type = tuple[0];
    var value = tuple[1];

    if ((type === 0 || type === 2) && value === tableType) {
      tableRowTuples = [];
      tableRowsTuples.push(tableRowTuples);
    } else {
      tableRowTuples.push(tuple);
    }
  });
  return tableRowsTuples.reduce(function (acc, rowTuples) {
    var tableRow = handler(rowTuples);

    if (tableRow.name) {
      acc[tableRow.name] = tableRow;
    } else {
      _logger["default"].warn('table row without name:', tableRow);
    }

    return acc;
  }, {});
};

var _default = function _default(tuples) {
  var tableGroups = [];
  var tableTuples;
  tuples.forEach(function (tuple) {
    // const type = tuple[0];
    var value = tuple[1];

    if (value === 'TABLE') {
      tableTuples = [];
      tableGroups.push(tableTuples);
    } else if (value === 'ENDTAB') {
      tableGroups.push(tableTuples);
    } else {
      tableTuples.push(tuple);
    }
  });
  var stylesTuples = [];
  var layersTuples = [];
  tableGroups.forEach(function (group) {
    if (group[0][1] === 'STYLE') {
      stylesTuples = group;
    } else if (group[0][1] === 'LTYPE') {
      _logger["default"].warn('LTYPE in tables not supported');
    } else if (group[0][1] === 'LAYER') {
      layersTuples = group;
    }
  });
  return {
    layers: tableHandler(layersTuples, 'LAYER', layerHandler),
    styles: tableHandler(stylesTuples, 'STYLE', styleHandler)
  };
};

exports["default"] = _default;