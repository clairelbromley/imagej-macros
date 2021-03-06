import math, csv, json, os
from datetime import datetime
from ij import IJ, ImageListener;
from ij.gui import Line, NonBlockingGenericDialog, GenericDialog, WaitForUserDialog
from ij.io import DirectoryChooser
from ij.plugin import SubstackMaker

class MembraneEvolutionAnalysisSettings:
	"""class to hold settings and allow persistence between instances"""
	
	settings_file_name = "MembraneEvolutionAnalysisSettings.json"

	def __init__(self, output_path="", zero_timepoint_frame=1, analysis_frame_step=1, membrane_indices=[-1,0,1,3]):
		self.output_path = output_path;
		self.zero_timepoint_frame =zero_timepoint_frame;
		self.analysis_frame_step = analysis_frame_step;
		self.membrane_indices = membrane_indices;
		self.__isMembraneEvolutionAnalysisSettings__ = True;

	def save_settings(self, settings_path=None):
		"""save settings to arbitrary location"""
		if settings_path is None:
			settings_path = os.path.join(self.output_path, self.settings_file_name);
		try:
			f = open(settings_path, "wb+");
			json.dump(self.__dict__, f);
		finally:
			f.close();	

	def persistSettings(self):
		"""save settings to appdata folder (or equivalent)"""
		settings_path = self.getPersistenceFilePath();
		self.save_settings(settings_path=settings_path)	;

	def loadPersistedSettings(self):
		"""load settings from appdata folder (or equivalent)"""
		settings_path = self.getPersistenceFilePath();
		err_str = "Settings file loaded successfully";
		if os.path.isfile(settings_path):
			try:
				f = open(settings_path, 'r');
				dct = json.loads(f.read());
				if "__isMembraneEvolutionAnalysisSettings__" in dct:
					self.output_path = dct["output_path"];
					self.analysis_frame_step = int(dct["analysis_frame_step"]);	
					self.zero_timepoint_frame = int(dct["zero_timepoint_frame"]);
				else:
					err_str = "Previous settings file doesn't contain properly configured settings! If this problem persists, contact the developer. Using default settings...";
			except Exception as e:
				print("Warning: error loading previous settings...");
				raise e;
		else:
			err_str = "Previous settings file doesn't exist. Using default settings...";
		print(err_str);

	def getPersistenceFilePath(self):
		if not IJ.isMacintosh() and not IJ.isLinux():
			# windows
			settings_path = os.path.join(os.getenv('APPDATA'), self.settings_file_name);
		else:
			settings_path = os.path.join(os.path.expanduser("~"), "Library", self.settings_file_name);
		return settings_path;
		
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

	def __str__(self):
		"""return string representation including roi's points"""
		poly = self.roi.getFloatPolygon();
		return ("Membrane " + str(self.positionNumber) + ", points = [\n" 
				+ str([(x,y) for x,y in zip(poly.xpoints, poly.ypoints)]) + "\n]");
				
class TimepointsMembranes:
	"""class for holding all the drawn membranes for one timepoint"""

	def __init__(self, input_image_title=None, time_point_s=0, init_membrane=None):
		self.membranes = [];
		self.input_image_title = input_image_title;
		self.time_point_s = time_point_s;
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
		"""return string representation including roi's points"""
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

def encode_membrane(obj):
	"""specify encoding of drawn membranes to JSON"""
	if isinstance(obj, DrawnMembrane):
		if obj.roi is not None:
			return {'position number': obj.positionNumber, 'roi' : [(x, y) for x, y in zip(obj.roi.getFloatPolygon().xpoints, obj.roi.getFloatPolygon().ypoints)]};
		else:
			return {'position number': obj.positionNumber, 'roi': None};
	else:
		try:
			return obj.__dict__;
		except:
			raise TypeError("Object of type " + obj.__class__.__name__ + " is not JSON serializable");

def main():
	# define here which membrane indices will be used in the analysis, with last index the "control" index
	membrane_indices = [-1, 0, 1, 3];

	# for now, work with frontmost open image...
	imp = IJ.getImage();
	im_title = imp.getTitle();
	settings = MembraneEvolutionAnalysisSettings(membrane_indices=membrane_indices);
	settings.loadPersistedSettings();

	timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H-%M-%S');
	DirectoryChooser.setDefaultDirectory((settings.output_path));
	dc = DirectoryChooser('Select the root folder for saving output');
	output_root = dc.getDirectory();
	if output_root is None:
		raise IOError('no output path chosen');
	settings.output_path = output_root;
	
	# get calibration
	cal = imp.getCalibration();
	if cal.getTimeUnit()=="sec":
		cal.setTimeUnit('s');

	# pop up a dialog prompting for selection of zero time point, frame interval, and time step for analysis
	time_steps_not_ok = True;
	while time_steps_not_ok:
		dialog = NonBlockingGenericDialog("Determine time parameters...");
		dialog.addNumericField("0 timepoint frame (1-index): ", settings.zero_timepoint_frame, 0);
		dialog.addNumericField("Acquisition time step (s): ", cal.frameInterval, 2) # assume stored in seconds
		dialog.addNumericField("Time step for analysis (s): ", cal.frameInterval * settings.analysis_frame_step, 2);
		dialog.showDialog();

		if dialog.wasCanceled():
			return;

		zero_f = dialog.getNextNumber();
		acq_t_step = dialog.getNextNumber();
		analysis_t_step = dialog.getNextNumber();
		if acq_t_step!=0 and analysis_t_step!=0:
			analysis_frame_step = analysis_t_step/acq_t_step;

			if round(analysis_frame_step) == analysis_frame_step:
				time_steps_not_ok = False;
				settings.zero_timepoint_frame = zero_f;
				settings.analysis_frame_step = analysis_frame_step;
		if time_steps_not_ok:
			warning_dlg = GenericDialog("Error!");
			warning_dlg.addMessage("Analysis time step must be an integer multiple of acquisition time steps, and neither should be zero!!");
			warning_dlg.setOKLabel("Try again...");
			warning_dlg.showDialog();

			if warning_dlg.wasCanceled():
				return;

	start_frame = int(((zero_f - 1) % analysis_frame_step) + 1);
	end_frame = int(imp.getNFrames() - (imp.getNFrames() - zero_f) % analysis_frame_step);
	frames = [f + 1 for f in range(start_frame-1, end_frame, int(analysis_frame_step))];
	print("frames = " + str(frames));
	imp.killRoi();
	analysis_imp = SubstackMaker().makeSubstack(imp, str(start_frame) + "-" + str(end_frame) + "-" + str(int(analysis_frame_step)));
	imp.changes = False;
	imp.close();
	analysis_imp.show();
	drawn_membranes = [TimepointsMembranes(input_image_title=im_title, time_point_s=(t - 1) * acq_t_step) for t in frames];
	membranes_listener = UpdateRoiImageListener(drawn_membranes);
	analysis_imp.addImageListener(membranes_listener);

	# now attach roi listener to store all 0th membranes after showing a waitforuserdialog to prompt continuation
	IJ.setTool("freeline");
	for membrane_idx in membrane_indices:
#		if membrane_idx>50:
#			IJ.setTool("line");
		analysis_imp.killRoi();
		membranes_listener.resetLastFrame();
		membranes_listener.setCurrentMembraneIndex(membrane_idx);		
		analysis_imp.setZ(1);
		continue_dlg = WaitForUserDialog("Continue?", "Click OK once all the " + str(membrane_idx) + "-index membranes have been drawn");
		continue_dlg.show();
		membranes_listener.imageUpdated(analysis_imp);
		drawn_membranes = membranes_listener.getDrawnMembraneTimepointsList();
		json_path = os.path.join(output_root, "Membranes " + timestamp + ".json");
		f = open(json_path, 'w+');
		try:
			json.dump(drawn_membranes, f, default=encode_membrane);
		finally:
			f.close();
		# save csv containing mebrane measurements for current membrane index
		csv_path = os.path.join(output_root, ("Membrane measurements " + timestamp + ".csv"));
		if membrane_idx==membrane_indices[0]:
			try:
				f = open(csv_path, 'wb');
				writer = csv.writer(f);
				writer.writerow(["Membrane index", 
								("Time point, " + cal.getTimeUnit()), 
								("Membrane length, " + cal.getUnit()), 
								("Euclidean length, " + cal.getUnit()), 
								"Membrane sinuoisty"]);
			finally:
				f.close();
		try:
			f = open(csv_path, 'ab')
			writer = csv.writer(f);
			for mems in drawn_membranes:
				mem = mems.getMembrane(membrane_idx);
				if mem is not None:
					writer.writerow([membrane_idx, 
									mems.time_point_s,
									mem.getPathLength() * cal.pixelWidth, 
									mem.getEuclidean() * cal.pixelWidth, 
									mem.getSinuosity()]);
		finally:
			f.close();
		
	settings.persistSettings();
	settings.save_settings();
	print("Finished getting all membranes with indices "  + str(membrane_indices));
	analysis_imp.close();

# It's best practice to create a function that contains the code that is executed when running the script.
# This enables us to stop the script by just calling return.
if __name__ in ['__builtin__','__main__']:
    main();
		