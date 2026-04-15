#target photoshop

var doc = app.activeDocument;

// Output next to the PSD file, not relative to this script's location
// since this script may be run as a combined temp file from a different path
var outputFile = new File(new File(doc.fullName).parent + "/_folder_names.txt");

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

var folderGroupA = findVisibleFolderGroup(doc);
if (!folderGroupA) {
    alert("Could not find a visible folder_group_A at root level!");
    exit();
}

// List all direct LayerSet children of folder_group_A
var names = [];
var layers = folderGroupA.layers;
for (var i = 0; i < layers.length; i++) {
    if (layers[i].typename === "LayerSet") {
        names.push(layers[i].name);
    }
}

outputFile.open("w");
for (var i = 0; i < names.length; i++) {
    outputFile.writeln(names[i]);
}
outputFile.close();

$.writeln("Folder names written to: " + outputFile.fsName);