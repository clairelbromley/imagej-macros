// Created by Bromley C.L., Kelly D.J.
// contact: dougkelly88@gmail.com

// loop over files in a folder, trimming and cropping and getting MANUAL membranes from user input, saving
// statistics from membrane line profiles as well as modified images, line profile X, Y and intensity. 

// semi-permanent user parameters
file_extension = ".tif";
line_width = 10; //l<-- add desired number of pixels for line width
draw_ch = 1; // channel to draw membranes in. Count from 1. 
analyse_ch = 2; // channel to get intensity profiles from. Count from 1. 

//means can add things to array without needing to decide array length at the start
setOption("ExpandableArrays", true);

// filterByFileType copied from DK 16bit 2P 4-channel combine.ijm --> searching for chosen file type within selected folder
function filterByFileType(files, extension)
{
	// filter file array according to file extension
	filtered = newArray();
	for (idx = 0; idx < files.length; idx++)
	{
		if (endsWith(files[idx], extension)){
			filtered[filtered.length] = files[idx];
		}
	}
	return filtered;
}

// calculate median value of an input array
function calculateMedian(arr)
{
	arr = Array.sort(arr);
	half_idx = arr.length/2 - 1; //-1 as indexed from zero
	if (half_idx == floor(half_idx))
	{
		median = (arr[half_idx] + arr[half_idx + 1])/2;
	}
	else
	{
		median = arr[half_idx + 1];
	}
	return median;
}

// prompt for user to draw membrane, returning profile from which to get intensity stats
function lineProfile(output_path, frame, channel_to_draw_in, channel_to_analyse)
{
	setTool("freeline");
	run("Line Width...", "line=5"); 
	getDimensions(w, h, channels, slices, frames);
	if ((channel_to_draw_in > channels) | (channel_to_analyse > channels))
	{
		exit("One (or both) of designated channels to draw in and analyse exceed the number of available channels");
	}
	Stack.setPosition(channel_to_draw_in, 0, 0);
	waitForUser("Draw a line from the apical surface to the basal surface and click OK when finished... BE SURE TO DRAW IN CORRECT DIRECTION");
	run("Fit Spline", "straighten");
	
	// clear output, get x, y, I values along the line and save
	run("Clear Results");
	Stack.setPosition(channel_to_analyse, 0, 0);
	profile = getProfile();
	getSelectionCoordinates(xpoints, ypoints);
	
	for (idx = 0; idx < profile.length; idx++)
	// if always draw lines in same direction, idx=0 is where start drawing. for ((START VALUE) idx = 0; (END VALUE) idx < profile.length/2; (MEANS WILL INCREASE BY ONE) idx++)
	{
		setResult("X", idx, xpoints[idx]);
		setResult("Y", idx, ypoints[idx]);
		setResult("Intensity", idx, profile[idx]);
	}
	updateResults();
	saveAs("Measurements", output_path + File.separator + "Line profile, frame = " + frame + ".csv");
	run("Clear Results");
	
// added ADDITIONAL LOOP
	for (idx = 0; idx < floor(profile.length/2); idx++)
	// if always draw lines in same direction, idx=0 is where start drawing. for ((START VALUE) idx = 0; (END VALUE) idx < profile.length/2; (MEANS WILL INCREASE BY ONE) idx++)
	{
		setResult("X", idx, xpoints[idx]);
		setResult("Y", idx, ypoints[idx]);
		setResult("Intensity", idx, profile[idx]);
	}
	updateResults();
	saveAs("Measurements", output_path + File.separator + "Half line profile, frame = " + frame + ".csv");
	// measurements is what saving, then output path follows
	run("Clear Results");

	return profile;
}

// get the files and filter by extension, and set up output folder
data_root = getDirectory("Choose a folder containing data...");
if (!endsWith(data_root, File.separator))
{
	data_root = data_root + File.separator;
}
files = getFileList(data_root);
filtered_files = filterByFileType(files, file_extension);
getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
timestamp = "" + year + "-" + IJ.pad(month+1, 2) + "-" + IJ.pad(dayOfMonth, 2) 
		+ " " + IJ.pad(hour, 2) + "." + IJ.pad(minute, 2) + "." + IJ.pad(second, 2);
output_path = data_root + timestamp + " output";
if (filtered_files.length > 0)
{
	File.makeDirectory(output_path);
}

// loop over files, prompting at each new file for the user to trim in space and time
for (fidx = 0; fidx < filtered_files.length; fidx++)
{
	// load file...
	data_path = data_root + filtered_files[fidx];
	subfolder_name = split(filtered_files[fidx], ".");
	subfolder_name = subfolder_name[0];
	output_subfolder = output_path + File.separator + subfolder_name;
	File.makeDirectory(output_subfolder);
	run("Bio-Formats", "open=[" + data_path + "]autoscale color_mode=Default");
	file_name = getInfo("image.filename");
	selectWindow(file_name); 
	getDimensions(w, h, channels, slices, frames);
	Stack.setDisplayMode("color");

	// trim time series...
	run("Enhance Contrast", "saturated=0.35");
	waitForUser("Scroll to the first frame of the period of interest and click OK");
	Stack.getPosition(channel, slice, start_frame);
	waitForUser("Scroll to the last frame of the period of interest and click OK");
	Stack.getPosition(channel, slice, end_frame);
	run("Make Substack...", "channels=1-" + channels + " frames=" + start_frame + "-" + end_frame);
	close("\\Others");
	
	// now crop spatially...
	run("Enhance Contrast", "saturated=0.35");
	Stack.setPosition(0, 0, 0);
	setTool("rectangle");
	waitForUser("Select spatial region to crop and click OK. ");
	run("Crop");

	// rename window and save to output folder
	image_name = split(file_name, '.');
	image_name = image_name[0] + " trimmed and cropped";
	rename(image_name);
	saveAs("tiff", output_subfolder + File.separator + image_name);

	// loop over frames in sequence, saving line profiles and storing intensity stats
	run("Enhance Contrast", "saturated=0.35");
	getDimensions(w, h, channels, slices, frames);
	means = newArray(frames);
	stdDevs = newArray(frames);
	mins = newArray(frames);
	maxs = newArray(frames);
	medians = newArray(frames);
	means_halfP = newArray(frames);
	stdDevs_halfP = newArray(frames);
	mins_halfP = newArray(frames);
	maxs_halfP = newArray(frames);
	medians_halfP = newArray(frames);
	ratio_halfP = newArray(frames);
	
	for (fridx = 1; fridx < frames + 1; fridx++)
	{
		Stack.setPosition(1, 0, fridx);
		profile = lineProfile(output_subfolder, fridx, draw_ch, analyse_ch);
		halfprofile = Array.trim(profile, floor(profile.length/2));
		Array.getStatistics(profile, min, max, mean, stdDev);
		means[fridx - 1] = mean;
		stdDevs[fridx - 1] = stdDev;
		mins[fridx - 1] = min;
		maxs[fridx - 1] = max;
		medians[fridx - 1] = calculateMedian(profile);
		Array.getStatistics(halfprofile, min, max, mean, stdDev);
		means_halfP[fridx - 1] = mean;
		stdDevs_halfP[fridx - 1] = stdDev;
		mins_halfP[fridx - 1] = min;
		maxs_halfP[fridx - 1] = max;
		medians_halfP[fridx - 1] = calculateMedian(halfprofile);
		// ratio increases with puncta, and accounts for photobleaching. 
		//95th percentile over median would be less susceptible to hot pixels
		ratio_halfP[fridx - 1] = max/mean;
	}

	// print stats to results screen and save as csv
	run("Clear Results");
	//fridx = frame index
	for (fridx = 0; fridx < frames; fridx++)
	{
		setResult("Frame", fridx, fridx + 1);
		setResult("Mean I", fridx, means[fridx]);
		setResult("Median I", fridx, medians[fridx]);
		setResult("StdDev I", fridx, stdDevs[fridx]);
		setResult("Min I", fridx, mins[fridx]);
		setResult("Max I", fridx, maxs[fridx]);
		setResult("Mean I - half profile", fridx, means_halfP[fridx]);
		setResult("Median I - half profile", fridx, medians_halfP[fridx]);
		setResult("StdDev I - half profile", fridx, stdDevs_halfP[fridx]);
		setResult("Min I - half profile", fridx, mins_halfP[fridx]);
		setResult("Max I - half profile", fridx, maxs_halfP[fridx]);
		setResult("Ratio max/mean - half profile", fridx, ratio_halfP[fridx]);
	}
	saveAs("Measurements", output_subfolder + File.separator + "Membrane intensity stats against time.csv");
	run("Close All");
}
if (filtered_files.length == 0)
{
	waitForUser("No files of the selected format exist in the selected folder!");
}
else
{
	waitForUser("Congratulations, you are done!"); 
}
