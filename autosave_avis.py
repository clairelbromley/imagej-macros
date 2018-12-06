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

def rescale_stack(imp, scaling):
	"""Rescale whole stack so that contrast adjustment propagates to avi"""
	stats = StackStatistics(imp);
	rng = float(stats.max - stats.min);
	IJ.run(imp, "Subtract...", "value=" + str(stats.min) + " stack");
	IJ.run(imp, "Multiply...", "value=" + str(float(scaling * imp.getProcessor().maxValue())/rng) + " stack");
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
		#imp.show();
		imp = rescale_stack(imp, additional_scaling_factor);
		output_path = os.path.join(output_folder, (os.path.splitext(tiff_file)[0] + " autocontrast avi.avi"));
		print("output_path = " + output_path);
		IJ.run(imp, "AVI... ", "compression=None frame=" + str(frame_rate_fps) + " save=[" + output_path + "]");
		imp.close();
WaitForUserDialog("DONE!").show();