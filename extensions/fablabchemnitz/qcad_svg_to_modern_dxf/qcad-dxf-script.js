include("scripts/ImportExport/SvgImporter/SvgImporter.js")
include("scripts/ImportExport/SvgImporter/SvgImporterInit.js");
include("scripts/Pro/Draw/Polyline/PolylineFromSelection/PolylineFromSelection.js");
include("scripts/Pro/Modify/Detection/Duplicates/Duplicates.js");

RFileImporterRegistry.registerFileImporter(new SvgImporterFactory());
qApp.applicationName = "SVG-DXF";

var storage = new RMemoryStorage();
var spatialIndex = new RSpatialIndexSimple();
var doc = new RDocument(storage, spatialIndex);
var di = new RDocumentInterface(doc);
var tolerance = $QCAD_TOLERANCE$;

const importer = new SvgImporter(doc);

di.importFile("$SVG_PATH$");

var purge_duplicates = $QCAD_PURGE_DUPLICATES$;
if (purge_duplicates === true) {
    Duplicates.findDuplicates(di, true, tolerance, 0.0, true);
    var counter = doc.countSelectedEntities();
    var op = new RDeleteSelectionOperation();
    di.applyOperation(op);
    print("Purged duplicates: " + counter);
}

di.selectAll();

PolylineFromSelection.autoJoinSegments(di, tolerance);
di.exportFile("$EXPORT_PATH$", "$QCAD_DXF_FORMAT$");
di.destroy();