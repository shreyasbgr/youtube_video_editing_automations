/*****************************
 * CONFIGURABLE PARAMETERS
 *****************************/

// File paths for input image and audio
var imagePath = "/Users/shreyas/Library/CloudStorage/GoogleDrive-k.urolagin@gmail.com/My Drive/DanuShree YouTube channel/Sai Satcharitre/6th Adhyay/cover-page.png"; // Full path to the image
var audioPath = "/Users/shreyas/Library/CloudStorage/GoogleDrive-k.urolagin@gmail.com/My Drive/DanuShree YouTube channel/Sai Satcharitre/6th Adhyay/raw-6th-sai-satcharitre.m4a"; // Full path to the audio

// Name for the new sequence
var sequenceName = "Automated Video";

// Name of the export preset to use (e.g., "My YouTube video preset")
var exportPresetName = "My YouTube video preset";

// Output path for the rendered video
var exportPath = "~/Downloads/output.mp4";

/*****************************
 * AUTOMATION SCRIPT
 *****************************/

// Reference to the active Premiere Pro project
var project = app.project;

// Create a new empty sequence
project.createNewSequenceFromClips(sequenceName, []);

// Get the active sequence
var sequence = project.activeSequence;

if (!sequence) {
    alert("Failed to create or access the sequence.");
    return;
}

// Import image and audio into the project
var importSuccess = project.importFiles([imagePath, audioPath], 1, project.rootItem, true);

if (!importSuccess || project.rootItem.children.numItems < 2) {
    alert("Failed to import media files. Please check the file paths.");
    return;
}

// Retrieve the imported media items
var image = project.rootItem.children[0];
var audio = project.rootItem.children[1];

// Insert the image into the first video track
sequence.videoTracks[0].insertClip(image, 0);

// Insert the audio into the first audio track
sequence.audioTracks[0].insertClip(audio, 0);

// Set the image duration to match the length of the audio
var audioDuration = audio.getMediaDuration();
if (audioDuration) {
    image.setOutPoint(audioDuration);
} else {
    alert("Failed to retrieve the audio duration.");
    return;
}

// Scale the image to the frame size
var videoClip = sequence.videoTracks[0].clips[0];
if (videoClip) {
    videoClip.setScaleToFrameSize();
} else {
    alert("Failed to access the video clip.");
    return;
}

// Find the export preset by name
var presetExists = false;
var presetCount = app.encoder.getNumPresets();
for (var i = 0; i < presetCount; i++) {
    if (app.encoder.getPresetName(i) === exportPresetName) {
        presetExists = true;
        break;
    }
}

// Check if the export preset exists
if (!presetExists) {
    alert("Export preset not found: " + exportPresetName);
    return;
}

// Queue the sequence for export with the specified preset
app.encoder.encodeSequence(sequence, exportPath, exportPresetName, 1, 1);

// Notify the user that the process is complete
alert("Export started: " + exportPath);
