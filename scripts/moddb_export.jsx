#target photoshop

// Passed in from Python via DoJavaScript:
// var SELECTED_FOLDER_NAME = "...";
// var OUTPUT_FOLDER_PATH   = "...";

var doc = app.activeDocument;
var outputFolder = new Folder(OUTPUT_FOLDER_PATH);

if (!outputFolder.exists) {
    outputFolder.create();
}

function getLayerByName(parent, name) {
    var layers = parent.layers;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].name === name) {
            return layers[i];
        }
    }
    return null;
}

function exportAsPNG(filename) {
    var file = new File(outputFolder + "/" + filename + ".png");
    var options = new PNGSaveOptions();
    options.compression = 0;
    options.interlaced = false;
    doc.saveAs(file, options, true, Extension.LOWERCASE);
    $.writeln("Exported: " + filename + ".png");
}

function findVisibleFolderGroup(doc) {
    var layers = doc.layers;
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        if (layer.typename === "LayerSet" && layer.visible) {
            for (var j = 0; j < layer.layers.length; j++) {
                if (layer.layers[j].typename === "LayerSet") {
                    return layer;
                }
            }
        }
    }
    return null;
}

function findFolderAByName(folderGroup, name) {
    var layers = folderGroup.layers;
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].typename === "LayerSet" && layers[i].name === name) {
            return layers[i];
        }
    }
    return null;
}

// ============================================================
// MAIN
// ============================================================

var folderGroupA = findVisibleFolderGroup(doc);
if (!folderGroupA) {
    alert("Could not find a visible folder_group_A at root level!");
    exit();
}
$.writeln("folder_group_A found: " + folderGroupA.name);

// Make selected folder_A visible, hide all others in group
var folderA = null;
var groupLayers = folderGroupA.layers;
for (var i = 0; i < groupLayers.length; i++) {
    if (groupLayers[i].typename === "LayerSet") {
        if (groupLayers[i].name === SELECTED_FOLDER_NAME) {
            groupLayers[i].visible = true;
            folderA = groupLayers[i];
        } else {
            groupLayers[i].visible = false;
        }
    }
}

if (!folderA) {
    alert("Could not find folder: '" + SELECTED_FOLDER_NAME + "' in " + folderGroupA.name);
    exit();
}
$.writeln("folder_A selected: " + folderA.name);

var folder16x9 = getLayerByName(doc, "16x9");
var folder4x3  = getLayerByName(doc, "4x3");

if (!folder16x9) { alert("Could not find '16x9' layer/group at root!"); exit(); }
if (!folder4x3)  { alert("Could not find '4x3' layer/group at root!");  exit(); }

var logoFolder = getLayerByName(folderA, "logo");
if (!logoFolder) { alert("Could not find 'logo' folder inside: " + folderA.name); exit(); }

var folderALayers = folderA.layers;

// ============================================================
// STEP 1 — Export moddb-logo and moddb-thumbnail
// ============================================================

// 1.1) Make 'logo' visible, hide all other sub-folders in folder_A
for (var i = 0; i < folderALayers.length; i++) {
    folderALayers[i].visible = (folderALayers[i].name === "logo");
}
$.writeln("Step 1.1: logo visible, others hidden");

// 1.2) Make 16x9 visible, 4x3 invisible
folder16x9.visible = true;
folder4x3.visible  = false;
$.writeln("Step 1.2: 16x9 visible, 4x3 hidden");

// 1.3) Export moddb-logo
exportAsPNG("moddb-logo");

// 1.4) Make 4x3 visible, 16x9 invisible
folder4x3.visible  = true;
folder16x9.visible = false;
$.writeln("Step 1.4: 4x3 visible, 16x9 hidden");

// 1.5) Export moddb-thumbnail
exportAsPNG("moddb-thumbnail");

// ============================================================
// STEP 2 — Export each non-logo folder in folder_A
// ============================================================

// 2.1) Hide logo folder
logoFolder.visible = false;
$.writeln("Step 2.1: logo hidden");

// 2.x) Hide both aspect ratio folders
folder16x9.visible = false;
folder4x3.visible  = false;
$.writeln("Step 2.x: 16x9 and 4x3 both hidden");

// 2.2) Loop through each non-logo folder
for (var i = 0; i < folderALayers.length; i++) {
    var currentLayer = folderALayers[i];

    if (currentLayer.name === "logo") {
        continue;
    }
    if (currentLayer.typename !== "LayerSet") {
        continue;
    }

    currentLayer.visible = true;
    $.writeln("Step 2.2.1: visible -> " + currentLayer.name);

    exportAsPNG("moddb-" + currentLayer.name);

    currentLayer.visible = false;
    $.writeln("Step 2.2.3: hidden -> " + currentLayer.name);
}

$.writeln("=== moddb_export complete ===");