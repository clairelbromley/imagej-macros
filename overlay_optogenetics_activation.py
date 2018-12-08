# @ImagePlus imp
import math
import os
import json
from ij import IJ
from ij.gui import GenericDialog, Roi
from ij.io import SaveDialog

x_image_size_pix = 800.0;
y_image_size_pix = 600.0;
m2 = 3.0;
m1 = 5.0;

class ActivationOverlayMetadata:
	"""class to handle all the information used to construct overlays"""

	def __init__(self, 
					roiX=0,
					roiY=0, 
					roiW=1,
					roiH=1,
					lowMagRoiOffsetXY=(0,0),
					panUmXY=(0,0),
					frameIntervalS=1.0,
					lowMagM=3.0,
					highMagM=5.0,
					scanImageDimensionsXY=(800,600)):
		self.roiX=roiX;
		self.roiY=roiY;
		self.roiW=roiW;
		self.roiH=roiH;
		self.lowMagRoiOffsetXY=lowMagRoiOffsetXY;
		self.panUmXY=panUmXY;
		self.frameIntervalS=frameIntervalS;		
		self.lowMagM=lowMagM;
		self.highMagM=highMagM;
		self.scanImageDimensionsXY=scanImageDimensionsXY;
		self.__optogenetics_activation_overlay_data__=True;

	def setRoi(self, xywh_tup):
		"""set all parameters to describe ROI"""
		self.roiX=int(xywh_tup[0]);
		self.roiY=int(xywh_tup[1]);
		self.roiW=int(xywh_tup[2]);
		self.roiH=int(xywh_tup[3]);

	def setLowMagOffsetXY(self, xy_tup):
		"""set offset from (0,0) of cropped low magnification image"""
		self.setLowMagOffsetXY=xy_tup;

	def setPanUmXY(self, xy_tup):
		"""set stage pan that has occured between acquisition of low mag and high mag images"""
		self.panUmXY=xy_tup;

	def setFrameIntervalS(self, frameIntervalS):
		"""set frame interval for timestamping"""
		self.frameIntervalS=frameIntervalS;

	def setLowMagM(self, lowMagM):
		"""set magnification of low magnifcation image"""
		self.lowMagM=lowMagM;

	def setHighMagM(self, highMagM):
		"""set magnification of high magnification image"""
		self.highMagM=highMagM;

	def setScanImageDimensionsXY(self, im_dims):
		"""set the resolution at which the image was acquired from the microscope, irrespective of cropping"""
		self.scanImageDimensionsXY=im_dims;

	def getLowMagPixelSize(self, imp):
		"""from an input imageplus, return the pixel size at low magnification"""
		return round(imp.getCalibration().pixelHeight, 2);

	def generateOverlayRoi(self, imp):
		"""For a given ImagePlus, generate the overlay ROI"""
		pixSizeLowM = self.getLowMagPixelSize(imp);
		# zoom occurs around the center of the image, but positions are defined wrt the 
		# top left - so need to transfom to central origin coords (with x, y in normal directions)
		ox = self.scanImageDimensionsXY[0]/2.0;
		oy = self.scanImageDimensionsXY[1]/2.0;
		pixSizeHighM = pixSizeLowM * self.highMagM/self.lowMagM;
		xprime = self.roiX - ox - 0.5;
		yprime = oy - self.roiY + 0.5;

		w3x = math.ceil((self.lowMagM/self.highMagM) * self.roiW);
		h3x = math.ceil((self.lowMagM/self.highMagM) * self.roiH);

		xprime3x = (self.lowMagM/self.highMagM) * xprime + self.panUmXY[0]/pixSizeLowM;
		yprime3x = (self.lowMagM/self.highMagM) * yprime - self.panUmXY[1]/pixSizeLowM;

		x3x = math.ceil(ox + xprime3x - self.lowMagRoiOffsetXY[0] + 1);
		y3x = math.ceil(oy - yprime3x - self.lowMagRoiOffsetXY[1] + 1);
		print("X corner: " + str(x3x));
		print("Y corner: " + str(y3x));
		print("Width = " + str(w3x));
		print("Height = " + str(h3x));

		return Roi(x3x, y3x, w3x, h3x);

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

	def save_to_json(self, file_path):
		try:
			f = open(file_path, 'w');
			json.dump(self.__dict__, f);
		finally:
			f.close();
		return;

	def load_from_json(self, file_path):
		try:
			f = open(file_path, 'r');
			dct = json.loads(f.read());
			if "__optogenetics_activation_overlay_data__" in dct:
				self.setRoi((int(dct['roiX']), int(dct['roiY']), int(dct['roiW']), int(dct['roiH'])));
				self.setLowMagM(int(dct['lowMagM']));
				self.setHighMagM(int(dct['highMagM']));
				self.setLowMagOffsetXY(self.parse_xytuple_from_string(dct['lowMagOffsetXY']));
				self.setPanUmXY(self.parse_xytuple_from_string(dct['panUmXY']));
				self.setFrameIntervalS(float(dct['frameIntervalS']));
			else:
				raise ValueError("JSON file doesn't translate to optogenetics activation overlay format")
		except IOError:
			print("IOError reading from JSON file");
			return False;
		except: 
			return False;
		finally:
			f.close();
		return True;

activation_overlay_data = ActivationOverlayMetadata(lowMagM=m2, highMagM=m1, scanImageDimensionsXY=(x_image_size_pix,y_image_size_pix));

dialog = GenericDialog("Define 5x ROI parameters...");
dialog.addNumericField("ROI X position (software coordinates, pixels): ", 0, 0);
dialog.addNumericField("ROI Y position (software coordinates, pixels): ", 0, 0);
dialog.addNumericField("ROI width (pixels): ", 0, 0);
dialog.addNumericField("ROI height (pixels): ", 0, 0);
dialog.addNumericField("3x ROI X offset pixels: ", 0, 0);
dialog.addNumericField("3x ROI Y offset pixels: ", 0, 0);
dialog.addNumericField("Pan X (um): ", 0, 3);
dialog.addNumericField("Pan Y (um): ", 0, 3);
dialog.addNumericField("Frame interval (s): ", 1.0, 2);

dialog.showDialog();

x5x = dialog.getNextNumber();
y5x = dialog.getNextNumber();
w5x = dialog.getNextNumber();
h5x = dialog.getNextNumber();
activation_overlay_data.setRoi((x5x,y5x,w5x,h5x));
offsetx = dialog.getNextNumber();
offsety = dialog.getNextNumber();
activation_overlay_data.setLowMagOffsetXY((offsetx,offsety));
panx = dialog.getNextNumber();
pany = dialog.getNextNumber();
activation_overlay_data.setPanUmXY((panx,pany));
interval = dialog.getNextNumber();
activation_overlay_data.setFrameIntervalS(interval);

roi = activation_overlay_data.generateOverlayRoi(imp);
imp.setRoi(roi);
IJ.run(imp, "RGB Color", "");
IJ.run("Colors...", "foreground=cyan background=white selection=yellow");
IJ.run("Draw", "stack");

sd = SaveDialog("Save as AVI...", os.path.splitext(imp.getTitle())[0], ".avi");
if sd.getFileName is not None:
	activation_overlay_data.save_to_json(os.path.join(sd.getDirectory(), 
												   os.path.splitext(os.path.basename(sd.getFileName()))[0] + " metadata.json"));
	IJ.saveAs(imp, "Tiff", os.path.join(sd.getDirectory(), 
			os.path.splitext(os.path.basename(sd.getFileName()))[0] + " + ROI, no timestamp.tif"));
	IJ.run(imp, "Label...", "format=00:00:00 starting=0 interval=" + str(interval) + " x=5 y=20 font=18 text=[] range=1-"+str(imp.getNFrames()));
	IJ.run(imp, "AVI... ", "compression=None frame=10 save=[" + os.path.join(sd.getDirectory(), sd.getFileName()) + "]");
	IJ.saveAs(imp, "Tiff", os.path.join(sd.getDirectory(), 
			os.path.splitext(os.path.basename(sd.getFileName()))[0] + " + ROI.tif"));