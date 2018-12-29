# @ImagePlus imp
import math
from ij import IJ, ImageListener;
from ij.gui import Line, NonBlockingGenericDialog, GenericDialog, WaitForUserDialog
from ij.plugin import SubstackMaker

class DrawnMembrane:
	"""class for manually-drawn membranes"""
	
	def __init__(self, roi=None, positionNumber=0):
		self.roi=roi;
		self.positionNumber=positionNumber;

	def setRoi(self, roi):
		"""define roi describing the membrane"""
		if not roi.isArea():
			self.roi=roi;	

	def getRoi(self):
		"""return the roi describing the membrane"""
		return self.roi;

	def setPositionNumber(self, number):
		"""define the interface index described in CB diagrams that this membrane corresponds to"""
		self.positionNumber=int(number);

	def getEuclidean(self):
		"""return the length of the straight line joining start and end points of the membrane"""
		poly = self.roi.getFloatPolygon();
		line = Line(poly.xpoints[0], poly.ypoints[0], poly.xpoints[-1], poly.ypoints[-1]);
		return line.getLength();

	def getPathLength(self):
		"""return the length of the membrane"""
		return self.roi.getLength();

	def getSinuosity(self):
		"""return the sinuosity"""
		return self.getPathLength()/self.getEuclidean() - 1;

	def __str__(self):
		"""return string representation including roi's points, for json saving"""
		poly = self.roi.getFloatPolygon();
		return ("Membrane " + str(self.positionNumber) + ", points = [\n" 
				+ str([(x,y) for x,y in zip(poly.xpoints, poly.ypoints)]) + "\n]");

#	def parse_from_str(self, string):
#		"""from a string representation, populate a DrawnMembrane object"""
#		import re;
#		fmt_str = "Membrane (?P<number>\d+)"

class TimepointsMembranes:
	"""class for holding all the drawn membranes for one timepoint"""

	def __init__(self, time_point_s=0, init_membrane=None):
		self.membranes=[];
		self.time_point_s=time_point_s;
		if init_membrane is not None:
			self.membranes.append(init_membrane);

	def setTimePoint(self, time_point_s):
		"""set the time point in s for this set of membranes"""
		self.time_point_s=float(time_point_s);

	def addMembrane(self, membrane):
		"""add a membrane to the collection, or replace if necessary"""
		new_number = membrane.positionNumber;
		existing_numbers = [mem.positionNumber for mem in self.membranes]
		if not new_number in existing_numbers:
			self.membranes.append(membrane);
		else:
			# overwrite - ask user if they really want to overwrite? 
			self.membranes[existing_numbers.index(new_number)] = membrane;

	def getMembrane(self, number):
		"""return a membrane corresponding to a given interface index defined in CB diagrams"""
		if number in [membrane.positionNumber for membrane in self.membranes]:
			return self.membranes[[membrane.positionNumber for membrane in self.membranes].index(number)];
		else:
			return None;

	def __str__(self):
		"""return string representation including roi's points, for json saving"""
		return ("Time point " + str(self.time_point_s) + " s, membranes: \n " + 	
				str([str(membrane) for membrane in self.membranes]));

class UpdateRoiImageListener(ImageListener):
	"""class to support updating ROI from list upon change of frame"""
	def __init__(self, membrane_timepoints_list):
		self.last_frame = 1;
		self.current_membrane_index = 0;
		self.membrane_timepoints_list = membrane_timepoints_list;
		print("UpdateRoiImageListener started");

	def imageUpdated(self, imp):
		print("image updated");
		frame = imp.getZ();
		roi = imp.getRoi();
		if roi is not None and not roi.isArea():
			self.membrane_timepoints_list[self.last_frame - 1].addMembrane(DrawnMembrane(roi, self.current_membrane_index));
		self.last_frame = frame;
		this_frames_membrane = self.membrane_timepoints_list[frame - 1].getMembrane(self.current_membrane_index);
		if this_frames_membrane is not None:
			imp.setRoi(this_frames_membrane.getRoi());
		else:
			imp.killRoi();

	def imageOpened(self, imp):
		print("UpdateRoiImageListener: image opened");
			
	def imageClosed(self, imp):
		print("UpdateRoiImageListener: image closed");
		imp.removeImageListener(self);

	def getDrawnMembraneTimepointsList(self):
		return self.membrane_timepoints_list;

	def setCurrentMembraneIndex(self, index):
		self.current_membrane_index = index;

	def getCurrentMembraneIndex(self):
		return self.current_membrane_index;

	def resetLastFrame(self):
		self.last_frame = 1;

def main():
	# define here which membrane indices will be used in the analysis, with last index the "control" index
	#membrane_indices = [-1, 0, 1, 3];
	membrane_indices = [-1, 3];

	# for now, work with frontmost open image...
	imp = IJ.getImage();

	# first, pop up a dialog prompting for selection of zero time point, frame interval, and time step for analysis
	time_steps_not_ok = True;
	while time_steps_not_ok:
		dialog = NonBlockingGenericDialog("Determine time parameters...");
		dialog.addNumericField("0 timepoint frame (1-index): ", 1, 0);
		dialog.addNumericField("Acquisition time step (s): ", imp.getCalibration().frameInterval, 2) # assume stored in seconds
		dialog.addNumericField("Time step for analysis (s): ", imp.getCalibration().frameInterval, 2);
		dialog.showDialog();

		if dialog.wasCanceled():
			return;

		zero_f = dialog.getNextNumber();
		acq_t_step = dialog.getNextNumber();
		analysis_t_step = dialog.getNextNumber();
		analysis_frame_step = analysis_t_step/acq_t_step;

		if round(analysis_frame_step) == analysis_frame_step:
			time_steps_not_ok = False;
		else:
			warning_dlg = GenericDialog("Error!");
			warning_dlg.addMessage("Analysis time step must be an integer multiple of acquisition time steps!");
			warning_dlg.setOKLabel("Try again...");

			if warning_dlg.wasCanceled():
				return;

	start_frame = int(((zero_f - 1) % analysis_frame_step) + 1);
	end_frame = int(imp.getNFrames() - (imp.getNFrames() - zero_f) % analysis_frame_step);
	frames = [f + 1 for f in range(start_frame-1, end_frame, int(analysis_frame_step))];
	imp.killRoi();
	analysis_imp = SubstackMaker().makeSubstack(imp, str(start_frame) + "-" + str(end_frame) + "-" + str(int(analysis_frame_step)));
	imp.changes = False;
	imp.close();
	analysis_imp.show();
	drawn_membranes = [TimepointsMembranes(t * analysis_frame_step) for t in frames];
	membranes_listener = UpdateRoiImageListener(drawn_membranes);
	analysis_imp.addImageListener(membranes_listener);

	# now attach roi listener to store all 0th membranes after showing a waitforuserdialog to prompt continuation
	IJ.setTool("freeline");
	for membrane_idx in membrane_indices:
		analysis_imp.killRoi();
		membranes_listener.resetLastFrame();
		membranes_listener.setCurrentMembraneIndex(membrane_idx);		
		analysis_imp.setZ(1);
		continue_dlg = WaitForUserDialog("Continue?", "Click OK once all the " + str(membrane_idx) + " membranes have been drawn");
		continue_dlg.show();
		membranes_listener.imageUpdated(analysis_imp); # ensure that last membrane is added properly...?
		
	print("Finished getting all membranes with indices "  + str(membrane_indices));
	drawn_membranes = membranes_listener.getDrawnMembraneTimepointsList();
	print(str(drawn_membranes[0]));
	print("");
	print(str(drawn_membranes[1]));
	print("");
	print(str(drawn_membranes[2]));
	print("");
	print(str(drawn_membranes[-1]));

	# then do same for each of N other membranes
	# do final calculation and data saving

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main();
		