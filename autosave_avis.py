import os
from ij import IJ
from ij.gui import WaitForUserDialog
from ij.io import FileSaver
from ij.process import StackStatistics;
from loci.plugins import BF as bf

#----- user parameters -----
root_folder = "C:\\Users\\dougk\\Desktop\\output";
output_folder = "C:\\Users\\dougk\\Desktop\\avis";
frame_rate_fps = 10;
additional_scaling_factor = 0.5	# should be between 0 and 1
#---------------------------

def rescale_stack(imp, scaling, subtract_minimum=True):
	"""Rescale whole stack so that contrast adjustment propagates to avi"""
	if imp.getNSlices()>1:
		stats = StackStatistics(imp);
	else:
		stats = imp.getStatistics();
	if subtract_minimum:		
		rng = float(stats.max - stats.min);
		IJ.run(imp, "Subtract...", "value=" + str(stats.min) + " stack");
	else:
		rng = float(stats.max);
	multiplier = float(scaling * imp.getProcessor().maxValue())/rng;
	print("Multiplier = " + str(multiplier));
	IJ.run(imp, "Multiply...", "value=" + str(multiplier) + " stack");
	#imp.show();
	#WaitForUserDialog("scaled image").show();
	#imp.hide();
	return imp;

# make output folder if necessary
if not os.path.isdir(output_folder):
	os.makedirs(output_folder);

# find tiffs in subfolders of root folder and save these as avis to the output folder
root_contents = os.listdir(root_folder);
subfolders = [os.path.join(root_folder, content) for content in root_contents if os.path.isdir(os.path.join(root_folder, content))];

for subfolder in subfolders:
	subfolder_contents = os.listdir(subfolder);
	tiff_files = [content for content in subfolder_contents if os.path.splitext(content)[1]=='.tif']
	for tiff_file in tiff_files:
		image_path = os.path.join(subfolder, tiff_file);
		print("input path = "  + image_path);
		bfimp = bf.openImagePlus(image_path);
		imp = bfimp[0];
		IJ.run(imp, "8-bit", "");
		#imp.show();
		imp = rescale_stack(imp, additional_scaling_factor, subtract_minimum=True);
		#IJ.run("Enhance Contrast", "saturated=0.35"); 
		#WaitForUserDialog("Enhance!").show();
		output_path = os.path.join(output_folder, (os.path.splitext(tiff_file)[0] + " autocontrast avi.avi"));
		IJ.run(imp, "AVI... ", "compression=None frame=" + str(frame_rate_fps) + " save=[" + output_path + "]");
		#cal = imp.getCalibration();
		#cal.fps = frame_rate_fps;
		#imp.setCalibration(cal);
		print("output_path = " + output_path);
		#IJ.saveAs(imp, "Gif", output_path);
		imp.close();
WaitForUserDialog("DONE!").show();