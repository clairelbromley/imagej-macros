
# @ImagePlus imp
import math
import os
import json
from ij import IJ
from ij.gui import GenericDialog, Line
from ij.gui import WaitForUserDialog
from ij.io import SaveDialog

class LineScanOverlayMetadata:
	"""class to handle all the information used to construct overlays"""

	def __init__(self, 
					p1=(0,0), 
					p2=(1,1),
					referenceRoiOffsetXY=(0,0),
					frameIntervalS=1.0):
		self.p1=p1;
		self.p2=p2;
		self.referenceRoiOffsetXY=referenceRoiOffsetXY;
		self.frameIntervalS=frameIntervalS;		
		self.__line_scan_overlay_data__=True;

	def setLineHighResCoords(self, p1_tup, p2_tup):
		"""set all parameters to describe ROI"""
		self.p1=p1_tup;
		self.p2=p2_tup;

	def setReferenceRoiOffsetXY(self, xy_tup):
		"""set offset from (0,0) of cropped low magnification image"""
		self.referenceRoiOffsetXY=xy_tup;

	def setFrameIntervalS(self, frameIntervalS):
		"""set frame interval for timestamping"""
		self.frameIntervalS=frameIntervalS;

	def generateOverlayRoi(self):
		"""Generate the overlay ROI"""
		if (abs(self.p1[0] - self.p2[0])) > 800:	# assume for now that lines run full length of image
			factor = 1024.0/800;
			loresp1x = int(round(self.p1[0]/factor)) - self.referenceRoiOffsetXY[0];
			loresp1y = int(round(self.p1[1]/factor)) - self.referenceRoiOffsetXY[1];
			loresp2x = int(round(self.p2[0]/factor)) - self.referenceRoiOffsetXY[0];
			loresp2y = int(round(self.p2[1]/factor)) - self.referenceRoiOffsetXY[1];
			#print([(loresp1x, loresp1y), (loresp2x,loresp2y)]);
			return Line(loresp1x, loresp1y, loresp2x, loresp2y);
		else:
			return Line(self.p1[0] - self.referenceRoiOffsetXY[0], 
						self.p1[1] - self.referenceRoiOffsetXY[1], 
						self.p2[0] - self.referenceRoiOffsetXY[0], 
						self.p2[1] - self.referenceRoiOffsetXY[1]);

	def parse_xytuple_from_string(tup_str):
		"""Handle loading string versions of tuples back to integer tuples"""
		import re;
		fmt_str = r'\((?P<x>\d+)\,\s*(?P<y>\d+)\)';
		m = re.match(fmt_str, tup_str);
		output=None;
		if bool(m):
			d = m.groupdict();
			output=(int(d['x']), int(d['y']));
		return output;

	def save_to_json(self, file_path, append=False):
		try:
			if append:
				f = open(file_path, 'a');
			else:
				f = open(file_path, 'w');
			json.dump(self.__dict__, f);
		finally:
			f.close();
		return;

	def load_from_json(self, file_path):
		try:
			f = open(file_path, 'r');
			dct = json.loads(f.read());
			if "__line_scan_overlay_data__" in dct:
				self.setLineHighResCoords(self.parse_xytuple_from_string(dct['p1']), 
										self.parse_xytuple_from_string(dct['p2']));
				self.setReferenceRoiOffsetXY(self.parse_xytuple_from_string(dct['referenceRoiOffsetXY']));
				self.setFrameIntervalS(float(dct['frameIntervalS']));
			else:
				raise ValueError("JSON file doesn't translate to line scan overlay format")
		except IOError:
			print("IOError reading from JSON file");
			return False;
		except: 
			return False;
		finally:
			f.close();
		return True;


def main():
	metadatas = [];
	runagain = True;
	offsetx = 0;
	offsety = 0;
	interval = 50.0;
	IJ.run(imp, "RGB Color", "");
	IJ.run("Colors...", "foreground=cyan background=white selection=yellow");
	while runagain:
		dialog = GenericDialog("Define 5x ROI parameters...");
		dialog.enableYesNoCancel("Continue and quit", "Continue and add another line");
		dialog.addNumericField("Line scan position 1 X, Y: ", 0, 0);
		dialog.addToSameRow();
		dialog.addNumericField(", ", 0, 0);
		dialog.addNumericField("Line scan position 2 X, Y: ", 0, 0);
		dialog.addToSameRow();
		dialog.addNumericField(", ", 0, 0);
		dialog.addNumericField("Reference image crop origin X, Y: ", offsetx, 0);
		dialog.addToSameRow();
		dialog.addNumericField(", ", offsety, 0);
		dialog.addNumericField("Frame interval (s): ", interval, 2);
		
		dialog.showDialog();
		
		p1x = dialog.getNextNumber();
		p1y = dialog.getNextNumber();
		p2x = dialog.getNextNumber();
		p2y = dialog.getNextNumber();
		offsetx = dialog.getNextNumber();
		offsety = dialog.getNextNumber();
		interval = dialog.getNextNumber();
		linescan_overlay = LineScanOverlayMetadata((p1x,p1y), (p2x,p2y), (offsetx,offsety), interval);
		metadatas.append(linescan_overlay);
		roi = linescan_overlay.generateOverlayRoi();
		imp.setRoi(roi);
		IJ.run("Draw", "stack");

		if dialog.wasOKed():
			runagain = False;
		elif dialog.wasCanceled():
			return;
	
	sd = SaveDialog("Save as AVI...", os.path.splitext(imp.getTitle())[0], "line scan overlay.avi");
	if sd.getFileName is not None:
		metadatas[0].save_to_json(os.path.join(sd.getDirectory(), 
													   os.path.splitext(os.path.basename(sd.getFileName()))[0] + "line scan metadata.json"));
		if len(metadatas) > 1: # append: multiple writes=slow, but easiest way based on existing framework
			for midx in range(1, len(metadatas)):
				metadatas[midx].save_to_json(os.path.join(sd.getDirectory(), 
													   os.path.splitext(os.path.basename(sd.getFileName()))[0] + "line scan metadata.json"), 
											append=True);
		IJ.saveAs(imp, "Tiff", os.path.join(sd.getDirectory(), 
				os.path.splitext(os.path.basename(sd.getFileName()))[0] + " + line scan ROI, no timestamp.tif"));
		IJ.run(imp, "Label...", "format=00:00:00 starting=0 interval=" + str(interval) + " x=5 y=20 font=18 text=[] range=1-"+str(imp.getNFrames()));
		IJ.run(imp, "AVI... ", "compression=None frame=10 save=[" + os.path.join(sd.getDirectory(), (os.path.splitext(sd.getFileName())[0] + " + line scan ROI.avi")) + "]");
		IJ.saveAs(imp, "Tiff", os.path.join(sd.getDirectory(), 
				os.path.splitext(os.path.basename(sd.getFileName()))[0] + " + line scan ROI.tif"));

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main()