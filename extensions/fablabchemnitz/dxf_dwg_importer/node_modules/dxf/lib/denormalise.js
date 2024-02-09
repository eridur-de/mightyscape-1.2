"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports["default"] = void 0;
var _cloneDeep = _interopRequireDefault(require("lodash/cloneDeep"));
var _logger = _interopRequireDefault(require("./util/logger"));
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }
var _default = function _default(parseResult) {
  var blocksByName = parseResult.blocks.reduce(function (acc, b) {
    acc[b.name] = b;
    return acc;
  }, {});
  var gatherEntities = function gatherEntities(entities, transforms) {
    var current = [];
    entities.forEach(function (e) {
      if (e.type === 'INSERT') {
        var _insert$rowCount, _insert$columnCount, _insert$rowSpacing, _insert$columnSpacing, _insert$rotation;
        var insert = e;
        var block = blocksByName[insert.block];
        if (!block) {
          _logger["default"].error('no block found for insert. block:', insert.block);
          return;
        }
        var rowCount = (_insert$rowCount = insert.rowCount) !== null && _insert$rowCount !== void 0 ? _insert$rowCount : 1;
        var columnCount = (_insert$columnCount = insert.columnCount) !== null && _insert$columnCount !== void 0 ? _insert$columnCount : 1;
        var rowSpacing = (_insert$rowSpacing = insert.rowSpacing) !== null && _insert$rowSpacing !== void 0 ? _insert$rowSpacing : 0;
        var columnSpacing = (_insert$columnSpacing = insert.columnSpacing) !== null && _insert$columnSpacing !== void 0 ? _insert$columnSpacing : 0;
        var rotation = (_insert$rotation = insert.rotation) !== null && _insert$rotation !== void 0 ? _insert$rotation : 0;

        // It appears that the rectangular array is affected by rotation, but NOT by scale.
        var rowVec, colVec;
        if (rowCount > 1 || columnCount > 1) {
          var cos = Math.cos(rotation * Math.PI / 180);
          var sin = Math.sin(rotation * Math.PI / 180);
          rowVec = {
            x: -sin * rowSpacing,
            y: cos * rowSpacing
          };
          colVec = {
            x: cos * columnSpacing,
            y: sin * columnSpacing
          };
        } else {
          rowVec = {
            x: 0,
            y: 0
          };
          colVec = {
            x: 0,
            y: 0
          };
        }

        // For rectangular arrays, add the block entities for each location in the array
        for (var r = 0; r < rowCount; r++) {
          for (var c = 0; c < columnCount; c++) {
            // Adjust insert transform by row and column for rectangular arrays
            var t = {
              x: insert.x + rowVec.x * r + colVec.x * c,
              y: insert.y + rowVec.y * r + colVec.y * c,
              scaleX: insert.scaleX,
              scaleY: insert.scaleY,
              scaleZ: insert.scaleZ,
              extrusionX: insert.extrusionX,
              extrusionY: insert.extrusionY,
              extrusionZ: insert.extrusionZ,
              rotation: insert.rotation
            };
            // Add the insert transform and recursively add entities
            var transforms2 = transforms.slice(0);
            transforms2.push(t);

            // Use the insert layer
            var blockEntities = block.entities.map(function (be) {
              var be2 = (0, _cloneDeep["default"])(be);
              be2.layer = insert.layer;
              // https://github.com/bjnortier/dxf/issues/52
              // See Issue 52. If we don't modify the
              // entity coordinates here it creates an issue with the
              // transformation matrices (which are only applied AFTER
              // block insertion modifications has been applied).
              switch (be2.type) {
                case 'LINE':
                  {
                    be2.start.x -= block.x;
                    be2.start.y -= block.y;
                    be2.end.x -= block.x;
                    be2.end.y -= block.y;
                    break;
                  }
                case 'LWPOLYLINE':
                case 'POLYLINE':
                  {
                    be2.vertices.forEach(function (v) {
                      v.x -= block.x;
                      v.y -= block.y;
                    });
                    break;
                  }
                case 'CIRCLE':
                case 'ELLIPSE':
                case 'ARC':
                  {
                    be2.x -= block.x;
                    be2.y -= block.y;
                    break;
                  }
                case 'SPLINE':
                  {
                    be2.controlPoints.forEach(function (cp) {
                      cp.x -= block.x;
                      cp.y -= block.y;
                    });
                    break;
                  }
              }
              return be2;
            });
            current = current.concat(gatherEntities(blockEntities, transforms2));
          }
        }
      } else {
        // Top-level entity. Clone and add the transforms
        // The transforms are reversed so they occur in
        // order of application - i.e. the transform of the
        // top-level insert is applied last
        var e2 = (0, _cloneDeep["default"])(e);
        e2.transforms = transforms.slice().reverse();
        current.push(e2);
      }
    });
    return current;
  };
  return gatherEntities(parseResult.entities, []);
};
exports["default"] = _default;