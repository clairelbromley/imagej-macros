# @ImagePlus imp

import json, os, csv
from ij import IJ
from ij.gui import WaitForUserDialog, PolygonRoi, Roi
from ij.io import OpenDialog

line_width = 1;
default_edges_path = "C:\\Users\\dougk\\Desktop\\Membranes 2019-01-11 15-24-07.json";
od = OpenDialog('Select the edges file from previous analysis...', os.path.dirname(default_edges_path), os.path.basename(default_edges_path))
edges_file_path = od.getPath();
print(edges_file_path);
settings_file_name = "MembraneEvolutionAnalysisSettings.json";
# assume settings file and edges file are in the same directory...
settings_file_path = os.path.join(os.path.dirname(edges_file_path), settings_file_name);

f = open(edges_file_path, 'r');
try:
	edges_dct = json.loads(f.read());
finally:
	f.close();

# check if open image corresponds to selected edge data...
original_image_file = edges_dct[0]['input_image_title'];
if imp.getTitle() is not original_image_file:
	WaitForUserDialog("WARNING!", 
					("Open image title is " + str(imp.getTitle()) + ", whilst edge file was generated on " + 
					str(original_image_file) + ". \nAre you sure you're working with the correct combination of files?")).show();

# avoid re-entering time parameters...
f = open(settings_file_path, 'r');
try:
	settings_dct = json.loads(f.read());
finally:
	f.close();
zero_f = int(settings_dct['zero_timepoint_frame']);
analysis_frame_step = int(settings_dct['analysis_frame_step']);
try:
	membrane_indices = settings_dct['membrane_indices'];
except:
	membrane_indices = [-1, 0, 1, 3];

# identify subset of frames used in previous analysis...
start_frame = int(((zero_f - 1) % analysis_frame_step) + 1);
end_frame = int(imp.getNFrames() - (imp.getNFrames() - zero_f) % analysis_frame_step);
frames_subset = [f + 1 for f in range(start_frame-1, end_frame, int(analysis_frame_step))];

## debug...
#membrane_index = 0;
#timepoint_data = edges_dct[14];
#membranes = timepoint_data['membranes'];
#membrane_indices_available = [membrane['position number'] for membrane in membranes];
#membrane_xy_list = membranes[membrane_indices_available.index(membrane_index)]['roi'];
#roi = PolygonRoi([x for x, y in membrane_xy_list], [y for x, y in membrane_xy_list], Roi.FREELINE);
#roi.setStrokeWidth(line_width);
#imp.setRoi(roi);
#if line_width > 1:	
#	IJ.run(imp, "Line to Area", "");
#	roi = imp.getRoi();
#print(roi.getStatistics().mean);
#imp.killRoi();

# loop through and get image statistics
# note - change line width parameter at the top of code to adjust the width of the line that intensity stats are calculated over...
output = [];
for idx, frame_idx in enumerate(frames_subset):
	if frame_idx > len(edges_dct) - 1:
		break;
#	imp.setSlice(frame_idx);
	imp.setT(frame_idx);
	timepoint_data = edges_dct[idx];
	t = timepoint_data['time_point_s'];
	membranes = timepoint_data['membranes'];
	membrane_indices_available = [membrane['position number'] for membrane in membranes];
	for membrane_index in membrane_indices_available:
		print("Analysing frame " + str(frame_idx) + ", membrane_index = " + str(membrane_index));
		membrane_xy_list = membranes[membrane_indices_available.index(membrane_index)]['roi'];
		roi = PolygonRoi([x for x, y in membrane_xy_list], [y for x, y in membrane_xy_list], Roi.FREELINE);
		imp.setRoi(roi);
		roi.setStrokeWidth(line_width);
		if line_width > 1:	
			IJ.run(imp, "Line to Area", "");
			roi = imp.getRoi();
		stats = roi.getStatistics();
		output.append((t, membrane_index, stats.mean, stats.max, stats.min, stats.median, stats.stdDev));
		imp.killRoi();
print(output);

# save output to csv
csv_path = os.path.join(os.path.dirname(edges_file_path), "intensity_stats.csv");
f = open(csv_path, 'wb');
try:
	writer = csv.writer(f);
	writer.writerow(["Time, s", "Membrane index", "Mean intensity", "Max intensity", "Min intensity", "Median intensity", "Std intensity"]);
	for row in output:
		writer.writerow(list(row));
finally:
	f.close();
		
#	

	