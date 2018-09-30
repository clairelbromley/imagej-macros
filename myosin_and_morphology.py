# Created by Bromley C.L., Kelly D.J.

# Python implementation of previous code for generating quantitative comparisons of myosin 
# intensity and morphological parameters against time. 

# python (jython) imports
import os, sys, math
from datetime import datetime

# java imports - aim to have UI components entirely swing, listeners and layouts awt
from java.awt import Dimension, GridBagLayout, GridBagConstraints, GridLayout
import javax.swing as swing
import javax.swing.table.TableModel

# imagej imports
from ij import IJ, WindowManager, ImagePlus
from ij.gui import Roi, PointRoi, PolygonRoi, GenericDialog, WaitForUserDialog
from ij.io import OpenDialog, DirectoryChooser, FileSaver
from ij.plugin import ChannelSplitter, Duplicator
from ij.process import FloatPolygon
from loci.plugins import BF as bf

# searches for chosen file type within selected folder
def filterByFileType(files, extension):
	return [f for f in files if (os.path.splitext(f)[1] == extension)]

def file_location_chooser(default_directory):
	# input
	dc = DirectoryChooser('Select the root folder for loading input images');
	input_root = dc.getDirectory();
	if input_root is None:
		print("no input root");
	# output
	DirectoryChooser.setDefaultDirectory(default_directory);
	dc = DirectoryChooser('Select the root folder for saving output');
	output_root = dc.getDirectory();
	if output_root is None:
		print("no output root");
	return input_root, output_root;

def pause_for_debug():
	gd = GenericDialog("Continue?");
	gd.showDialog();
	if gd.wasCanceled():
		raise Exception("Run interupted");
def main():
	#print (sys.version_info) # debug
	#print(sys.path) # debug
	data_root = r'C:\Users\Doug\Desktop\test'; # debug
	output_root = r'C:\Users\Doug\Desktop\test'; #debug
	#default_directory = r'C:\\Users\\Doug\\Desktop\\test';
	#data_root, output_root = file_location_chooser(default_directory);
	if (data_root is None) or (output_root is None):
		raise IOError("File location dialogs cancelled!");
	timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H.%M.%S")
	output_path = os.path.join(output_root,  (timestamp + " output"));
	for file_path in filterByFileType(os.listdir(data_root), '.tif'):
		subfolder_name = os.path.splitext(file_path)[0];
		output_subfolder = os.path.join(output_path, subfolder_name);
		print(output_subfolder);
		os.makedirs(output_subfolder);
		imps = bf.openImagePlus(os.path.join(data_root, file_path));
		imp = imps[0];
		imp.show();
		h = imp.height;
		w = imp.width;
		slices = imp.getNSlices();
		channels = imp.getNChannels();
		frames = imp.getNFrames();
		
		# rotation step - since using multiples of 90, TransformJ.Turn is more efficient
		IJ.run("Enhance Contrast", "saturated=0.35");
		angleZ = 1;
		while ((angleZ % 90) > 0):
			gd = GenericDialog("Rotate?");
			gd.addMessage("Define rotation angle - increments of 90. Apical at top");
			gd.addNumericField("Rotation angle", 0, 0);
			gd.showDialog();
			angleZ = int(gd.getNextNumber());
			
		if (angleZ > 1):
			IJ.run("TransformJ Turn",  "z-angle=" + str(angleZ) + " y-angle=0 x-angle=0");
			imp.close();
			imp = WindowManager.getCurrentImage();
			imp.setTitle(file_path);

		# trim time series
		IJ.run("Enhance Contrast", "saturated=0.35");
		imp.setDisplayMode(IJ.COLOR);
		WaitForUserDialog("Scroll to the first frame of the period of interest and click OK").show();
		start_frame = imp.getT();
		WaitForUserDialog("Scroll to the last frame of the period of interest and click OK").show();
		end_frame = imp.getT();
		trim_imp = Duplicator().run(imp, 1, channels, 1, slices, start_frame, end_frame);
		imp.close();
		trim_imp.show();
		dup_imp = Duplicator().run(trim_imp);

		# create images to process and find bounds for
		dup_imps = ChannelSplitter().split(dup_imp);
		myo_imp = dup_imps[1];
		mem_imp = dup_imps[0];
		FileSaver(myo_imp).saveAsTiffStack(os.path.join(output_subfolder, "myosin_channel.tif"));
		FileSaver(mem_imp).saveAsTiffStack(os.path.join(output_subfolder, "membrane_channel.tif"));

		# set basal bounds
		myo_imp.show();
	

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main()