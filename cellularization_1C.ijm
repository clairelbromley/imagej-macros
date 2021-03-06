// Cellularization analysis
// Created by Yu-Chiun Wang

fileName = getInfo("image.filename");
path = getDirectory("image");

//Creating a user interface using "Dialog"
Dialog.create("File Identifier");
Dialog.addString("Exp number", "Exp");
Dialog.addString("Embryo number", "E");
Dialog.addString("Analysis iteration", "01");
Dialog.addString("Channel", "myomK");
Dialog.show();
Exp_number	= Dialog.getString();
E_number	= Dialog.getString();
Analysis_iteration 	= Dialog.getString();
Ch	= Dialog.getString();

// Imaging parameters
Dialog.create("Get frame rate");
Dialog.addString("Frame rate (sec)", "2");
Dialog.show();
t_step = Dialog.getString();
getPixelSize(unit, pixelWidth, pixelHeight);

// Create folder
newFolder = "analysis" + Analysis_iteration + "_" + Exp_number + "_" + E_number + "_" + Ch;
// ** work out if can put in dialogue to warn if going to overwrite previous folder
newPath = path + newFolder
File.makeDirectory(newPath);

//Combined channels
selectWindow(fileName); 
// **add function enabling adding together of stacks to occur only when there are two channels i.e. not processed**
//run("Duplicate...", "title=G1 duplicate channels=1");
//selectWindow(fileName); 
//run("Duplicate...", "title=G2 duplicate channels=2");
//imageCalculator("Add create stack", "G1","G2");
run("Grays");
Stack.getStatistics(area, mean, min, max);
setMinAndMax(min, max);
run("8-bit");
newName = Ch + "_initial_input";
saveAs("tiff", newPath + File.separator + newName);
rename(newName);
//selectWindow("G1");
//close();
//selectWindow("G2");
//close();
//selectWindow(fileName); 
//close();

// Preprocessing + make kymograph
selectWindow(newName); 
run("Gaussian Blur...", "sigma=3 stack"); // preprocessing
waitForUser("Draw a straight segment across basal myosin (from top to bottom), decide on end point of analysis, then click OK");
getLine(x1, y1, x2, y2, lineWidth);
Dialog.create("Analysis end point");
Dialog.addNumber("Final t frame", 0);
Dialog.show();
final_t	= Dialog.getNumber();
print(final_t);

selectWindow(newName); 
run("Multi Kymograph", "linewidth=1"); //creates files called "Kymograph"
run("Duplicate...", "title=Kymo_raw"); //now have two windows called "Kymograph" and "Kymo_raw"
saveAs("tiff", newPath + File.separator + "Kymo_raw");
run("Duplicate...", "title=Kymo_processmethod_1");
run("Duplicate...", "title=Kymo_processmethod_2");
selectWindow("Kymo_processmethod_1");
run("Gaussian Blur...", "sigma=3 stack"); // preprocess kymograph
saveAs("tiff", newPath + File.separator + "Kymo_processmethod_1");
run("Duplicate...", "title=Kymo_seg");
run("Duplicate...", "title=Kymo_seg2");
setAutoThreshold("Otsu dark");
run("Duplicate...", "title=otsudark_threshold");
saveAs("tiff", newPath + File.separator + "threshold");
close();
waitForUser("check folder")
selectWindow("Kymo_seg");
run("8-bit");
run("Auto Local Threshold", "method=[Try all] radius=15 parameter_1=0 parameter_2=0 white");
saveAs("tiff", newPath + File.separator + "montage");
close();
waitForUser("test")
selectWindow("Kymo_seg2");
run("Make Binary");
saveAs("tiff", newPath + File.separator + "binary");
run("Outline");
saveAs("tiff", newPath + File.separator + "outline");


width = getWidth();
height = getHeight();
makeRectangle(0, 1, width, final_t);
run("Colors...", "foreground=black background=white selection=cyan");
run("Clear Outside");
run("Select None");
waitForUser("Use magic wand to select basal margin, then click OK");
run("Clear Outside");
selectWindow("Kymo_processmethod_1.tif");
run("8-bit");
run("Merge Channels...", "c1=Kymo_seg c4=Kymo_processmethod_1.tif create keep ignore");
saveAs("tiff", newPath + "/Merged_process1");
selectWindow("Kymo_seg");
saveAs("tiff", newPath + "/cellu_front_y_t");
close();
selectWindow(newName);
close();
selectWindow("Kymograph");
close();

// Save some txt files
print("\\Clear");
print("t_step_size", "pixel_size");
print(t_step, pixelHeight);
selectWindow("Log");
saveAs("txt", newPath + "/time_pixel_scales");

print("\\Clear");
print("Kymograph line segment coordinates:" + x1, y1, x2, y2);
selectWindow("Log");
saveAs("txt", newPath + "/Kymo_segment_cdn");

