from ij import IJ, ImagePlus
inFile = "C:/Users/Doug/Downloads/e3_0007/OIR/e3_0007.oir"
outFile = "C:/Users/Doug/Downloads/e3_0007/OIR/e3_0007_autoTIFF.tif"

def processFile(src_path, dst_path):
	IJ.log("Open OIR file: " + src_path)
	IJ.runPlugIn("_Viewer", src_path)
	IJ.log("Save TIFF file: " + dst_path)
	imp = IJ.getImage()
	IJ.save(imp, dst_path)
	imp.close()
	IJ.log("Done processing " + src_path)

processFile(inFile, outFile)