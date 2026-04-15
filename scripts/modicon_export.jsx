#target photoshop

// Passed in from Python via DoJavaScript:
// var TARGET_FOLDER_NAME = "...";
// var OUTPUT_FOLDER_PATH = "...";

var doc = app.activeDocument;
var outputFolder = new Folder(OUTPUT_FOLDER_PATH);

if (!outputFolder.exists) {
    outputFolder.create();
}

function exportAsPNG(filename) {
    var file = new File(outputFolder + "/" + filename + ".png");
    var options = new PNGSaveOptions();
    options.compression = 0;
    options.interlaced = false;
    doc.saveAs(file, options, true, Extension.LOWERCASE);
    $.writeln("Exported: " + filename + ".png");
}

var layers = doc.layers;

// Hide all folders
for (var i = 0; i < layers.length; i++) {
    if (layers[i].typename === "LayerSet") {
        layers[i].visible = false;
    }
}
$.writeln("All folders hidden");

// Show only target folder
var targetFound = false;
for (var i = 0; i < layers.length; i++) {
    if (layers[i].typename === "LayerSet" && layers[i].name === TARGET_FOLDER_NAME) {
        layers[i].visible = true;
        targetFound = true;
        $.writeln("Target folder visible: " + layers[i].name);
        break;
    }
}

if (!targetFound) {
    alert("Could not find folder: '" + TARGET_FOLDER_NAME + "'");
    exit();
}

exportAsPNG("modicon");

$.writeln("=== modicon_export complete ===");