# This script uses the OlympusViewer plugin (https://imagej.net/OlympusImageJPlugin) to open *.oir 
# files, and saves them as TIFFs
# Created by D. J. Kelly
# contact: dougkelly88@gmail.com


from ij import IJ, ImagePlus
from ij.io import DirectoryChooser
from ij.gui import MessageDialog
import os

default_root = "C:/Users/Doug/Downloads/e3_0007"

def processFile(src_path, dst_path):
	IJ.log("Open OIR file: " + src_path)
	IJ.runPlugIn("_Viewer", src_path)
	IJ.log("Save TIFF file: " + dst_path)
	imp = IJ.getImage()
	IJ.save(imp, dst_path)
	imp.close()
	IJ.log("Done processing " + src_path)

def loopOirFiles(root_path, output_root):
	DirectoryChooser.setDefaultDirectory(root_path)
	od = DirectoryChooser("Choose a folder containing OIR files...")
	if od is None:
		return False
	src_root = od.getDirectory()
	if src_root is None:
		return False
	IJ.log("Src ="+src_root)
	files = os.listdir(src_root)
	for f in files:
		filename, extension = os.path.splitext(f)
		if extension==".oir":
			src_path = os.path.join(src_root, f)
			dst_path = os.path.join(output_root, filename+".tif")
			processFile(src_path, dst_path)
	return True
	
def run_script():
	# choose output directory
	DirectoryChooser.setDefaultDirectory(default_root)
	od = DirectoryChooser("Choose a folder to save TIFFs to...")
	if od is None:
		IJ.log("CANCELLED");
		return
	tiff_output_folder = od.getDirectory()
	if tiff_output_folder is None:
		IJ.log("CANCELLED");
		return
		
	# process all oir files in a given directory
	result = loopOirFiles(default_root, tiff_output_folder)
	if result:
		IJ.log("DONE!")
		IJ.showMessage("DONE!")
	else:
		IJ.log("CANCELLED")


if __name__ in ['__builtin__','__main__']:
    run_script()
    