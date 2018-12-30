# @ImagePlus imp
import math, csv, json, os
from datetime import datetime
from ij import IJ, ImageListener;
from ij.gui import Line, NonBlockingGenericDialog, GenericDialog, WaitForUserDialog, Roi
from ij.io import DirectoryChooser
from ij.plugin import SubstackMaker

def encode_membrane(self, z):
    if isinstance(z, DrawnMembrane):
		return {'position number': z.positionNumber, 'roi' : [(x, y) for x, y in zip(z.getFloatPolygon().xpoints, z.getFloatPolygon().ypoints)]};

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
		poly = self.roi.getInterpolatedPolygon(1, True);
		line = Line(poly.xpoints[0], poly.ypoints[0], poly.xpoints[-1], poly.ypoints[-1]);
		return line.getLength();

	def getPathLength(self):
		"""return the length of the membrane - automatically applying 3-point smoothing to account for shaky hands"""
		poly = self.roi.getInterpolatedPolygon(1, True);
		return poly.getLength(True);

	def getSinuosity(self):
		"""return the sinuosity"""
		return self.getPathLength()/self.getEuclidean() - 1;

	#def __str__(self):
	#	"""return string representation including roi's points, for json saving"""
	#	poly = self.roi.getFloatPolygon();
	#	return ("Membrane " + str(self.positionNumber) + ", points = [\n" 
	#			+ str([(x,y) for x,y in zip(poly.xpoints, poly.ypoints)]) + "\n]");
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


def encode_membrane(z):
	if isinstance(z, DrawnMembrane):
		return {'position number': z.positionNumber, 'roi' : [(x, y) for x, y in zip(z.roi.getFloatPolygon().xpoints, z.roi.getFloatPolygon().ypoints)]};
	else:
		try:
			return z.__dict__;
		except:
			type_name = z.__class__.__name__
        	raise TypeError("Object of type " + type_name + " is not JSON serializable");

roi = imp.getRoi();
dm = DrawnMembrane(roi, -1);
print(dm.__dict__);
json_path = os.path.join("C:\\Users\\Doug\\Desktop\\", "test2.json");
f = open(json_path, 'w');
json.dump(dm, f, default=encode_membrane)
f.close()
dms = TimepointsMembranes(time_point_s=0, init_membrane=dm);
dm2 = DrawnMembrane(roi, 3);
dms.addMembrane(dm2);
json_path = os.path.join("C:\\Users\\Doug\\Desktop\\", "test3.json");
f = open(json_path, 'w');
json.dump(dms, f, default=encode_membrane)
f.close();
dmss = [];
for idx in range(3):
	dms.setTimePoint(idx);
	dmss.append(dms);
print(dmss.__class__.__name__);
print(dmss[0].__class__.__name__);
print(dmss[0])
json_path = os.path.join("C:\\Users\\Doug\\Desktop\\", "test4.json");
f = open(json_path, 'w');
json.dump(dmss, f, default=encode_membrane)
f.close();