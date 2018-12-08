///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////        					 		 Cellularization analysis for defining time zero of 2P images         				   ////
////															by Y.-C. Wang												   ////
////													     Ver 1.04  2018/11/09 											   ////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// 1) This macro works for 2p time lapse series with an apical-basal cross-sectional view (e.g. coronal sectioning 
//    of cephalic furrow formation, for which the current version was developed and tested, and mis-sagittal section for 
//    drosal fold formation). 
// 
// 2) The macro asks the user to select an ROI that encompass the basal surface of the cell layer. The segmentation of 
//    the Kymograph is NOT optimized and the determination of zero time point requires user's judgemental call. An 8-bit image 
//    with overlays of the analysis ROIs and the time stamps is generated and can be saved in the designated folder.
//
// 3) ver 1.05 combines 1.02 with 1.04 and processes datasets that have both SqhGFP and Gap43mC. Also works for single channel 
//    datasets. 


// Preparation
fileName = getInfo("image.filename");
newName=File.nameWithoutExtension();
print(newName);

rename(newName);
run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
run("Set Measurements...", "centroid stack display nan redirect=None decimal=0");

choices = newArray("Yes", "No");
Dialog.create("");
Dialog.addChoice("Upside down?", choices);
Dialog.show();
result=Dialog.getChoice();

if (result == choices[0]) {
	run("Flip Vertically", "stack");
}

setTool("Line");
waitForUser("Draw a straight line to fit the basal boundary, then click OK");
run("Clear Results");
run("Measure");
Angle = getResult("Angle", 0);
run("Rotate... ", "angle="+Angle+" grid=1 interpolation=Bicubic stack");

path = getDirectory("Choose a Directory to save"); 

// SqhGFP

Dialog.create("");
Dialog.addChoice("Process Sqh-GFP channel?", choices);
Dialog.show();
Ch_result1=Dialog.getChoice();

if (Ch_result1 == choices[0]) {
	newName_G=newName+"_SqhG";
	selectWindow(newName);
	run("Duplicate...", "title=ch2 duplicate channels=1");
	rename(newName_G);
	run("Grays");

	waitForUser("Roughly decide the last frame of analysis, then click OK");
	fin_t=getSliceNumber();
	print(fin_t);
	
	getDimensions(width, height, channels, slices, frames);
	setTool("rectangle");
	makeRectangle(width/2, 0, 30, height);
	waitForUser("Adjust height and width, and position of the box, then click OK.");
	getSelectionBounds(x, y, width, height);
	run("Overlay Options...", "stroke=red width=1 fill=none");
	makeRectangle(x, y, width, height);
	run("Add Selection...");
	
	newImage("Cropped", "16-bit black", width, height, fin_t);
	newImage("Kymo_01", "16-bit black", fin_t, height, 1);
	setBatchMode(true);
	for (t = 0; t < fin_t; t++) {
		selectWindow(newName_G);
		setSlice(t+1);
		makeRectangle(x, y, width, height);
		run("Copy");
		selectWindow("Cropped");
		setSlice(t+1);
		run("Paste");
		for (j = 0; j < height; j++) {
			a = newArray(width);
			for (i = 0; i < width; i++) {
			selectWindow("Cropped");
			a[i]=getPixel(i, j);
			}	
		Array.getStatistics(a, min, max, mean, std);
		selectWindow("Kymo_01");
		setPixel(t, j, mean);
		}
	}
	close("Cropped");
	setBatchMode(false);
	
	run("Duplicate...", "title=Kymo_seg01");
	run("Enhance Contrast", "saturated=3");
	run("Apply LUT");
	run("8-bit");
	run("Subtract Background...", "rolling=100");
	run("Median...", "radius=25");
	setAutoThreshold("Otsu dark");
	run("Convert to Mask");
	run("Skeletonize");
	selectWindow("Kymo_01");
	run("Enhance Contrast", "saturated=0.35");
	run("8-bit");
	run("Merge Channels...", "c1=Kymo_01 c2=Kymo_seg01 create");
	rename("Kymo_01");
	
	setTool("point");
	waitForUser("Select the estimated final cellularization front, then click OK");
	run("Clear Results");
	run("Measure");
	
	choices = newArray("Yes", "No");
	Dialog.create("");
	Dialog.addChoice("Repeat?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	k=2;
	setTool("rectangle");
	if (result == choices[0]) {
		do {
			newImage("Cropped", "16-bit black", width, height, fin_t);
			newImage("Kymo_0"+k, "16-bit black", fin_t, height, 1);
			x=x+width;
			setBatchMode(true);
			for (t = 0; t < fin_t; t++) {
				selectWindow(newName_G);
				setSlice(t+1);
				makeRectangle(x, y, width, height);
				run("Copy");
				selectWindow("Cropped");
				setSlice(t+1);
				run("Paste");
				for (j = 0; j < height; j++) {
					a = newArray(width);
					for (i = 0; i < width; i++) {
					selectWindow("Cropped");
					a[i]=getPixel(i, j);
					}	
				Array.getStatistics(a, min, max, mean, std);
				selectWindow("Kymo_0"+k);
				setPixel(t, j, mean);
				}
			}
			close("Cropped");
			setBatchMode(false);
	
			selectWindow(newName_G);
			run("Overlay Options...", "stroke=red width=1 fill=none");
			makeRectangle(x, y, width, height);
			run("Add Selection...");
			
			selectWindow("Kymo_0"+k);
			run("Duplicate...", "title=Kymo_seg0"+k);
			run("Enhance Contrast", "saturated=3");
			run("Apply LUT");
			run("8-bit");
			run("Subtract Background...", "rolling=100");
			run("Median...", "radius=25");
			setAutoThreshold("Otsu dark");
			run("Convert to Mask");
			run("Skeletonize");
			selectWindow("Kymo_0"+k);
			run("Enhance Contrast", "saturated=0.35");
			run("8-bit");
			run("Merge Channels...", "c1=Kymo_0"+k+" c2=Kymo_seg0"+k+" create");
			rename("Kymo_0"+k);
			
			setTool("point");
			waitForUser("Select the estimated final cellularization front, then click OK");
			run("Measure");
				
				choices = newArray("Yes", "No");
				Dialog.create("");
				Dialog.addChoice("Continue?", choices);
				Dialog.show();
				result=Dialog.getChoice();
				k=k+1;
		} while (result == choices[0]) {
	}
		
	Dialog.create("");
	Dialog.addChoice("Save and close kymographs?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	if (result == choices[0]) {
		for (i = 1; i <= nResults; i++) {
			selectWindow("Kymo_0"+i);
			saveAs("tiff", path+"/"+newName_G+"_Kymo_0"+i+".tif");
			close();
		}
	}
	
	Dialog.create("");
	Dialog.addChoice("Save results?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	if (result == choices[0]) {
		Table.renameColumn("X", "Time Frame");
		Table.update;
		selectWindow("Results");
		saveAs("Results", path+"/"+newName_G+"_Zero_T_estimate.xls");
	}
	
	Dialog.create("");
	Dialog.addChoice("Lable the image series and save?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	if (result == choices[0]) {
			T = newArray(nResults);
			for (i = 0; i < nResults; i++) {
			T[i]=parseInt(getResult("Time Frame", i)); 
			}
			Array.getStatistics(T, min, max, mean, std);
			zeroT=parseInt(mean);
			Dialog.create("");
			Dialog.addNumber("Frame rate in sec", 10);
			Dialog.show();
			FR = Dialog.getNumber();
			selectWindow(newName_G);
			getDimensions(width, height, channels, slices, frames);
			F1=(1-zeroT)*FR;
			run("Label...", "format=0 starting="+F1+" interval="+FR+" x=20 y=30 font=20 text=[sec] range=1-"+frames+"use");
			run("8-bit");
			saveAs("tiff", path+"/"+newName_G+"_t_labeled.tif");
		}
	}
}

// Gap43mCh

Dialog.create("");
Dialog.addChoice("Process Gap43mCh channel?", choices);
Dialog.show();
Ch_result2=Dialog.getChoice();

if (Ch_result2 == choices[0]) {
	newName_R=newName+"_G43mC";
	selectWindow(newName);
	run("Duplicate...", "title=ch2 duplicate channels=2");
	rename(newName_R);
	run("Grays");

	waitForUser("Roughly decide the last frame of analysis, then click OK");
	fin_t=getSliceNumber();
	print(fin_t);
	
	getDimensions(width, height, channels, slices, frames);
	setTool("rectangle");
	makeRectangle(width/2, height/2, 200, 100);
	waitForUser("Adjust the size and position of the box, then click OK.");
	getSelectionBounds(x, y, width, height);
	run("Overlay Options...", "stroke=red width=1 fill=none");
	makeRectangle(x, y, width, height);
	run("Add Selection...");
	
	newImage("Cropped", "16-bit black", width, height, fin_t);
	newImage("Kymo", "16-bit black", fin_t, height, 1);
	setBatchMode(true);
	for (t = 0; t < fin_t; t++) {
		selectWindow(newName_R);
		setSlice(t+1);
		makeRectangle(x, y, width, height);
		run("Copy");
		selectWindow("Cropped");
		setSlice(t+1);
		run("Paste");
		for (j = 0; j < height; j++) {
			a = newArray(width);
			for (i = 0; i < width; i++) {
			selectWindow("Cropped");
			a[i]=getPixel(i, j);
			}	
		Array.getStatistics(a, min, max, mean, std);
		selectWindow("Kymo");
		setPixel(t, j, mean);
		}
	}
	close("Cropped");
	setBatchMode(false);
	
	run("Duplicate...", "title=Kymo_seg01");
	run("Enhance Contrast", "saturated=3");
	run("Apply LUT");
	run("8-bit");
	run("Gaussian Blur...", "sigma=5");
	run("Auto Local Threshold", "method=Otsu radius=50 parameter_1=0 parameter_2=0 white");
	setAutoThreshold("Otsu dark");
	run("Convert to Mask");
	
	run("Outline");
	selectWindow("Kymo");
	run("Enhance Contrast", "saturated=0.35");
	run("8-bit");
	run("Merge Channels...", "c1=Kymo c2=Kymo_seg01 create");
	rename("Kymo");
	
	setTool("point");
	waitForUser("Select the estimated final cellularization front, then click OK");
	run("Clear Results");
	run("Measure");
	
	Dialog.create("");
	Dialog.addChoice("Save and close the kymograph?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	if (result == choices[0]) {
		selectWindow("Kymo");
		saveAs("tiff", path+"/"+newName_R+"_Kymo.tif");
		close();
		}
	
	Table.renameColumn("X", "Time Frame");
	Table.update;
	
	Dialog.create("");
	Dialog.addChoice("Lable the image series and save?", choices);
	Dialog.show();
	result=Dialog.getChoice();
	
	if (result == choices[0]) {
		zeroT=parseInt(getResult("Time Frame", 0)); 
			
		Dialog.create("");
		Dialog.addNumber("Frame rate in sec", 10);
		Dialog.show();
		FR = Dialog.getNumber();
		selectWindow(newName_R);
		getDimensions(width, height, channels, slices, frames);
		F1=(1-zeroT)*FR;
		run("Label...", "format=0 starting="+F1+" interval="+FR+" x=20 y=30 font=20 text=[sec] range=1-"+frames+"use");
		run("8-bit");
		saveAs("tiff", path+"/"+newName_R+"_t_labeled.tif");
	}	
}
	
