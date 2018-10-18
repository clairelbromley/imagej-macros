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
from ij.process import FloatPolygon, ImageConverter
from ij.plugin.filter import GaussianBlur, ParticleAnalyzer
from ij.plugin.frame import RoiManager
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

def find_basal_edges(imp, search_range=10):
	edges = [];
	for fridx in range(0, imp.getNFrames()):
		print("Examining frame " + str(fridx) + "...");
		#imp.setPosition(1, 1, fridx+1);
		imp.setSliceWithoutUpdate(fridx + 1)
		if (fridx == 0):
			edge = imp.getWidth() * [-1];
			for xidx in range(0, imp.getWidth()):
				yidx = imp.getHeight() - 1;
				pix_val = imp.getPixel(xidx, yidx)[0];
				while (pix_val == 0):
					yidx = yidx - 1;
					pix_val = imp.getPixel(xidx, yidx)[0];
				edge[xidx] = yidx;
		else:
			# confine search for edge to region of search_range (10 pix default) either side
			# of the last frame's edge. If no edge is found in that region, must be a hole in 
			# the binary image. Assign a dummy value and deal with it in second loop. 
			edge = imp.getWidth() * [-1];
			for xidx in range(0, imp.getWidth()):
				yidx = int(edges[fridx-1][xidx] + search_range);
				pix_val = imp.getPixel(xidx, yidx)[0];

				while (pix_val==0) and (yidx > (edges[fridx-1][xidx] - search_range)):
					yidx = yidx - 1;
					pix_val = imp.getPixel(xidx, yidx)[0];
				if (pix_val != 0):
					edge[xidx] = yidx;
			
			# deal with pixels we've marked as missing an edge
			xidx = -1;
			while xidx < imp.getWidth() - 1:
				xidx = xidx + 1;
				# if first position along edge is anomalous, take the value from the previous 
				# frame's edge as a reasonable approximation
				if (xidx==0) and (edge[xidx]==-1):
					edge[xidx] = edges[fridx-1][xidx];
					xidx = xidx + 1;
				# if later positions are anomalous, interpolate between previous and next 
				# successfully found edges
				if (edge[xidx]==-1):
					# last good edge position
					x1 = xidx - 1;
					y1 = edge[x1];
					# find next good edge position
					sub_xidx = xidx + 1;
					wp = imp.getWidth() - 1;
					if (sub_xidx < wp):
						while (edge[sub_xidx]==-1):
							sub_xidx = sub_xidx + 1;
							if (sub_xidx >= wp):
								break;
					# deal with case when no further good positions exisit - just continue
					# edge using last good y position to the end of the image in x direction, 
					# and terminate outer loop over x positions
					if (sub_xidx >= wp):
						for subsub_xidx in range(x1, imp.getWidth()):
							edge[subsub_xidx] = y1;
						xidx = wp;
					# deal with case when edge exists again after a while
					else:
						x2 = sub_xidx;
						y2 = edge[x2];
						# interpolate between last good position and next good position
						for subsub_xidx in range((x1 + 1), x2):
							edge[subsub_xidx] = round((float(subsub_xidx - x1)/
															(x2 - x1)) * (y2 - y1) +  y1);
						# get outer loop to skip over section we've just dealt with by updating
						# xidx accordingly
						xidx = x2 - 1;
		edges.append(edge);	
	return edges;

def main():
	#print (sys.version_info) # debug
	#print(sys.path) # debug
	data_root = r'C:\Users\dougk\Desktop\test'; # debug
	output_root = r'C:\Users\dougk\Desktop\test'; #debug
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
		ImageConverter(myo_imp).convertToGray8();
		frames = myo_imp.getNFrames();	
		gb = GaussianBlur();
		for fridx in range(0, frames):
			myo_imp.setSliceWithoutUpdate(fridx + 1);
			ip = myo_imp.getProcessor();
			gb.blurGaussian(ip, 5.0, 1.0, 0.02); # assymmetrical Gaussian
		IJ.run(myo_imp, "Convert to Mask", "method=Otsu background=Dark calculate");
		IJ.run("Despeckle", "stack");
		title = myo_imp.getTitle();

		# assume that first frame is good quality image...
		basal_edges = find_basal_edges(myo_imp);
		#myo_imp.hide()
		mem_imp.hide();

		# draw some edges for checking
		roim = RoiManager();
		xs = [x for x in range(1, trim_imp.getWidth()+1)];
		trim_imp.show();
		for fridx in range(0, myo_imp.getNFrames()):
			trim_imp.setPosition(2, 1, fridx+1);
			IJ.run("Enhance Contrast", "saturated=0.35");
					
			roi = PolygonRoi(xs, basal_edges[fridx], Roi.POLYLINE);
			trim_imp.setRoi(roi);
			roim.addRoi(roi);
		#myo_imp.show()

		# after getting rid of incorrectly segmented non-basal myosin, 
		# perform previous edge search to identify the bottom AND TOP edges of the bright band
		# then can draw these on the masks, fill holes and have a mask that effectively collects
		# all basal myosin, as well as a line that delineates the end of the cell
		
		
	

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main()