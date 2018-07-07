//This macro will aide in combining the four detector channels from the Two-Photon microscope
// Currently, this version only works when both 930nm and 1040nm lasers are used with upper and lower detectors for each.
// Created by Eritano AS., Wang YC., Kelly DJ.
// contact: dougkelly88@gmail.com

setOption("ExpandableArrays", true);

// user parameters
stack_order = "xyctz";
file_extension = ".tif";

function filterByFileType(files, extension){
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

function combineChannels(file_name, channel_name, channel_number1, channel_number2, slices, frames, out_path)
{
	// sum channels into a single stack
	file_string = split(file_name, ".");
	file_string = file_string[0];
	print("filename = " + file_name);
	print("channel_name = " + channel_name);
	print("channel_number1 = " + channel_number1);
	print("channel_number2 = " + channel_number2);
	print("slices = " + slices);
	print("frames = " + frames);
	selectWindow(file_name);
	run("Make Substack...", "channels=" + channel_number1 + " slices=1-" + slices + " frames=1-" + frames + "");
	rename("channel" + channel_number1);
	selectWindow(file_name);
	run("Make Substack...", "channels=" + channel_number2 + " slices=1-" + slices + " frames=1-" + frames + "");
	rename("channel" + channel_number2);
	imageCalculator("Add create stack", "channel" + channel_number1, "channel" + channel_number2);
	run("Grays");
	if ((frames > 1) || (slices > 1))
	{
		Stack.getStatistics(area, mean, min, max);
	}
	else
	{
		getStatistics(area, mean, min, max);
	}
	setMinAndMax(min, max);
	run("16-bit");
	rename(channel_name);
	run("Duplicate...", "duplicate");
	saveAs("tiff", out_path + File.separator + file_string + " - " + channel_name);
}

// get the files
data_root = getDirectory("Choose a folder containing data...");
files = getFileList(data_root);


// get the file-related parameters
Dialog.create("Looped 2p combiner");
Dialog.addChoice("File format:", newArray(".oir",".tif"));
Dialog.addMessage("Please name the output folder:");
Dialog.addString("File Name", "output");
Dialog.show();
file_extension = Dialog.getChoice();
output_folder = Dialog.getString();
output_path = data_root + File.separator + output_folder;

// set default channel parameters based on file format
if (file_extension == ".tif")
{
	default_channels = newArray(1, 2, 3, 4);
}
else if (file_extension == ".oir")
{
	default_channels = newArray(1, 3, 2, 4);
}

// get the channel-related parameters
Dialog.create("Channel definitions...")
Dialog.addString("Red Channel Name", "myomK");
Dialog.addNumber("Red Channel", default_channels[0]);
Dialog.addNumber("Red Channel", default_channels[1]);
Dialog.addString("Green Channel Name", "evemNG");
Dialog.addNumber("Green Channel", default_channels[2]);
Dialog.addNumber("Green Channel", default_channels[3]);
Dialog.show();
red_channel_name = Dialog.getString();
red_channel_number1 =  Dialog.getNumber();
red_channel_number2 = Dialog.getNumber();
green_channel_name = Dialog.getString();
green_channel_number1 = Dialog.getNumber();
green_channel_number2 = Dialog.getNumber();

// loop over files, combining channels
filtered_files = filterByFileType(files, file_extension);
if (filtered_files.length > 0)
{
	File.makeDirectory(output_path);
}

for (fidx = 0; fidx < filtered_files.length; fidx++)
{
	data_path = data_root + File.separator + filtered_files[fidx];
	subfolder_name = split(filtered_files[fidx], ".");
	subfolder_name = subfolder_name[0];
	output_subfolder = output_path + File.separator + subfolder_name;
	File.makeDirectory(output_subfolder);
	run("Bio-Formats", "open=[" + data_path + "]autoscale color_mode=Default stack_order=" + toUpperCase(stack_order));
	file_name = getInfo("image.filename");
	selectWindow(file_name); 
	getDimensions(w, h, channels, slices, frames);

	if (channels == 2)
	{
		red_channel_number1 = 1;
		red_channel_number2 = 2;
	}

	combineChannels(file_name, red_channel_name, red_channel_number1, red_channel_number2, slices, frames, output_subfolder);
	
	if (channels > 2)
	{
		combineChannels(file_name, green_channel_name, green_channel_number1, green_channel_number2, slices, frames, output_subfolder);
		run("Merge Channels...", "c1=" + red_channel_name + " c2=" + green_channel_name + " create");
		if (slices > 1)
		{
			selectWindow("Composite");
		}
		else if (frames > 1)
		{
			selectWindow("Merged");
		}
		saveAs("tiff", output_subfolder + File.separator + subfolder_name +"_merged");
	}

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