# @ImagePlus imp
import math
from ij import IJ
from ij.gui import GenericDialog, Roi

x_image_size_pix = 800.0;
y_image_size_pix = 600.0;
m2 = 3.0;
m1 = 5.0;

pixSize3x = round(imp.getCalibration().pixelHeight, 2);

dialog = GenericDialog("Define 5x ROI parameters...");
dialog.addNumericField("ROI X position (software coordinates, pixels): ", 0, 0);
dialog.addNumericField("ROI Y position (software coordinates, pixels): ", 0, 0);
dialog.addNumericField("ROI width (pixels): ", 0, 0);
dialog.addNumericField("ROI height (pixels): ", 0, 0);
dialog.addNumericField("3x ROI X offset pixels: ", 0, 0);
dialog.addNumericField("3x ROI Y offset pixels: ", 0, 0);
dialog.addNumericField("Pan X (um): ", 0, 3);
dialog.addNumericField("Pan Y (um): ", 0, 3);

dialog.showDialog();

x5x = dialog.getNextNumber();
y5x = dialog.getNextNumber();
w5x = dialog.getNextNumber();
h5x = dialog.getNextNumber();
offsetx = dialog.getNextNumber();
offsety = dialog.getNextNumber();
panx = dialog.getNextNumber();
pany = dialog.getNextNumber();

# zoom occurs around the center of the image, but positions are defined wrt the 
# top left - so need to transfom to central origin coords (with x, y in normal directions)
ox = x_image_size_pix/2.0;
oy = y_image_size_pix/2.0;
xprime = x5x - ox - 0.5;
yprime = oy - y5x + 0.5;
pixSize5x = pixSize3x * m1/m2;

w3x = math.ceil((m2/m1) * w5x);
h3x = math.ceil((m2/m1) * h5x);

#yprimeum = yprime * pixSize5x + pany;
#xprimeum = xprime * pixSize5x + panx;

xprime3x = (m2/m1) * xprime;
yprime3x = (m2/m1) * yprime;

x3x = math.ceil(ox + xprime3x - offsetx + 1);
y3x = math.ceil(oy - yprime3x - offsety + 1);
print("X corner: " + str(x3x));
print("Y corner: " + str(y3x));
print("Width = " + str(w3x));
print("Height = " + str(h3x));

roi = Roi(x3x, y3x, w3x, h3x);
imp.setRoi(roi);
IJ.run(imp, "RGB Color", "");
IJ.run("Colors...", "foreground=cyan background=white selection=yellow");
IJ.run("Draw", "stack");

#todo deal with pan and get pixel-to-micron conversion from image metadata