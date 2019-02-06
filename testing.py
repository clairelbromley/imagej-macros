# @ImagePlus imp

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
from loci.plugins import BF as bf

def pause_for_debug():
	gd = GenericDialog("Continue?");
	gd.showDialog();
	if gd.wasCanceled():
		raise Exception("Run interupted");


def find_basal_edges(imp, search_range=10):
	edges = [];
	for fridx in range(0, imp.getNFrames()):
		print("Examining frame " + str(fridx) + "...");
		imp.setPosition(1, 1, fridx+1);
		#imp.setSliceWithoutUpdate(fridx + 1)
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
				try:
					pix_val = imp.getPixel(xidx, yidx)[0];
				except TypeError:
					print(xidx);
					print(yidx);
					raise TypeError;
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
						print("edge exists again");
						x2 = sub_xidx;
						y2 = edge[x2];
						print('x1 = ' + str(x1));
						print('y1 = ' + str(y1));
						print('x2 = ' + str(x2));
						print('y2 = ' + str(y2));
						
						
						# interpolate between last good position and next good position
						for subsub_xidx in range((x1 + 1), x2):
							edge[subsub_xidx] = round((float(subsub_xidx - x1)/
															(x2 - x1)) * (y2 - y1) +  y1);
							print(edge[x1:x2]);
						pause_for_debug();
						# get outer loop to skip over section we've just dealt with by updating
						# xidx accordingly
						xidx = x2 - 1;
		edges.append(edge);	
	return edges;

# assume that first frame is good quality image...
basal_edges = find_basal_edges(imp);
xs = [x for x in range(1, imp.getWidth()+1)];
for fridx in range(0, imp.getNFrames()):
	imp.setPosition(1, 1, fridx+1);
	roi = PolygonRoi(xs, basal_edges[fridx], Roi.POLYLINE);
	imp.setRoi(roi);
	pause_for_debug();

