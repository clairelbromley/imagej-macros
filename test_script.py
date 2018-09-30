# @ImagePlus imp
from ij.gui import Roi, PointRoi, PolygonRoi, GenericDialog, WaitForUserDialog
from ij import IJ, WindowManager
from ij.plugin import ChannelSplitter, Duplicator, Thresholder
from ij.plugin.filter import GaussianBlur, ParticleAnalyzer, Analyzer
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable, Measurements
from ij.process import ImageStatistics

from datetime import datetime

title = imp.getTitle();
IJ.run("Set Measurements...", "centroid bounding stack redirect=None decimal=3");
IJ.run(imp, "Analyze Particles...", "size=500-30000 pixel show=Masks display clear stack");
particles_imp = WindowManager.getImage(("Mask of " + title));
rt = ResultsTable.getResultsTable();
particle_slices = rt.getColumn(rt.getColumnIndex("Slice"));
particle_ys = rt.getColumn(rt.getColumnIndex("Y"));
particle_hs = rt.getColumn(rt.getColumnIndex("Height"));

#print(particle_slices)
idx = 0;
while idx < len(particle_slices):
	instances = [i for i, e in enumerate(particle_slices) if e == particle_slices[idx]];
	if len(instances) > 1:
		keep_row = instances[0];
		for iidx in range(1, len(instances)):
			# based on position and degree of overlap, either (a) replace current row; (b) replace currnet row; (c) jettison. 
			if 
		print("Value = " + str(particle_slices[idx]));
		print("Indices = " + str(instances))
	idx = idx + len(instances);


seen = {}
dupes = []

for idx, x in enumerate(particle_slices):
    if x not in seen:
        seen[x] = 1
    else:
        if seen[x] == 1:
            dupes.append(x)
        seen[x] += 1

print(dupes)

for dupe in dupes:
	# get centroidys
	
	

rt = ResultsTable();
#rm = RoiManager.getInstance();
#print(rm)
rm = RoiManager(False);
pa = ParticleAnalyzer((ParticleAnalyzer.ADD_TO_MANAGER | ParticleAnalyzer.SHOW_MASKS), (Measurements.CENTROID | Measurements.STACK_POSITION), rt, 500, 30000, 0.0, 1.0)
pa.setHideOutputImage(False)
keep_rois = [];
pa.analyze(imp);

IJ.run("Set Measurements...", "centroid redirect=None decimal=3");
frames = imp.getNFrames();	
for fridx in range(0, frames):
	rt.reset();
	imp.setSliceWithoutUpdate(fridx + 1);
	ip = imp.getProcessor();
	if not pa.analyze(imp, ip):
		raise Exception("something went wrong analysing particles!")
	rt.show("centroids");
	rm = RoiManager.getInstance();
	if rm.getCount() > 0:
		rois = rm.getRoisAsArray();
		centroidsx = rt.getColumn(rt.getColumnIndex('X'));
		centroidsy = rt.getColumn(rt.getColumnIndex('Y'));
		print(centroidsx);
		print(centroidsy);
		gd = GenericDialog("Continue?");
		gd.showDialog();
		if gd.wasCanceled():
			raise Exception("Run interupted");
		for roi in rois:
			imp.setRoi(roi);
			stats = ImageStatistics().getStatistics(ip);
			print(stats.xCenterOfMass)
			

#print(keep_rois)
