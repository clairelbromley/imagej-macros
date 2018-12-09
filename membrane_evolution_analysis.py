# @ImagePlus imp
import math
from ij.gui import Line

class DrawnMembrane:
	"""class for manually-drawn membranes"""
	
	def __init__(self, roi=None, positionNumber=0):
		self.roi=roi;
		self.positionNumber=positionNumber;

	def setRoi(self, roi):
		"""define roi describing the membrane"""
		if not roi.isArea():
			self.roi=roi;	

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
		return "Membrane " + str(self.positionNumber) + ", points = [\n" + 
				str([(x,y) for x,y in zip(poly.xpoints, poly.ypoints)]) + "\n]";

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
		existing_numbers = [membrane.number for membrane in self.membranes]
		if not new_number in existing_numbers:
			self.membranes.append(membrane);
		else:
			# overwrite - ask user if they really want to overwrite? 
			self.membranes[existing_number.index(new_number)] = membrane;

	def getMembrane(self, number):
		"""return a membrane corresponding to a given interface index defined in CB diagrams"""
		return self.membranes[[membrane.number for membrane in self.membranes].index(number)];

	def __str__(self):
		"""return string representation including roi's points, for json saving"""
		return "Time point " + str(self.time_point_s) + " s, membranes: \n " + 	
				str([str(membrane) for membrane in self.membranes]);


def main():
	# first, pop up a dialog prompting for selection of zero time point, frame interval, and time step for analysis
	dialog = GenericDialog("Determine time parameters...");
	dialog.addNumericField("0 timepoint frame (1-index): ", 1, 0);
	dialog.addNumericField("Acquisition time step (s): ", imp.getCalibration().frameInterval, 2) # assume stored in seconds
	dialog.addNumericField("Time step for analysis (s): ", 1.0, 2);

	if dialog.wasCanceled():
		return;

	zf = dialog.getNextNumber();
	acq_t_step = dialog.getNextNumber();
	analysis_t_step = dialog.getNextNumber();

	# HOW TO GENERATE FRAME INDEX SEQUENCE!!!!???
	ff_time = (zf * acq_t_step) - math.floor((zf * acq_t_step)/analysis_t_step) * analysis_t_step;
	target_frame_times = [t in range(ff_time, imp.getNFrames()*acq_t_step, analysis_t_step);
	
	# then start at 0th frame-possible frames before zero, show image and attach roi listener to store all 0th membranes after shoing a waitforuserdialog to prompt continuation
	# then do same for each of N other membranes
	# do final calculation and data saving

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main();
		