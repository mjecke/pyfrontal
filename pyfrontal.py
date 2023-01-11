###############################################################################
# The following is a python script that uses VTK to generate fast
# projections of STL meshes for frontal area calculations.  See README for more
# information.
###############################################################################
import os
import time
import argparse

import vtk
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np


# ------------------ Argument Parsing -----------------------------------------
def valid_file(param):
    base, ext = os.path.splitext(param)
    if ext.lower() not in ('.stl'):
        raise argparse.ArgumentTypeError(
            '\n\nERROR: File must be an STL mesh.\n')
    return param


parser = argparse.ArgumentParser()

parser.add_argument("filename", type=valid_file, help="Filename of STL mesh")
parser.add_argument("-noshow", help="Skip graphic window after render",
                    action="store_true")
parser.add_argument("-nosave", help="Skip PNG outut of render",
                    action="store_true")
parser.add_argument("-x", "-X", help="Sets X as proj. normal axis (default)",
                    action="store_true")
parser.add_argument("-y", "-Y", help="Sets Y as proj. normal axis",
                    action="store_true")
parser.add_argument("-z", "-Z", help="Sets Z as proj normal axis",
                    action="store_true")
parser.add_argument("-fitfactor", help="Factor to help fit view to model",
                    type=float, default=1.0)
parser.add_argument("-res", help="Render Window Resolution (default 1500px)",
                    type=int, default=1500)
parser.add_argument("-ground", type=int, default=-10000,
                    help="Ground height clipping in mm from Z=0")
parser.add_argument("-debug", help="Turns on debug messages",
                    action="store_true")

args = parser.parse_args()

if (args.x + args.y + args.z) > 1:  # ensure only one axis is used
    print("\nERROR: Choose only one projection axis argument.\n")
    quit()

# debug print function enable/disable
if args.debug:
    printd = print  # it just turns printd functions to print statements
else:
    def printd(x, *ex):
        pass  # else ignore them

projaxis = "X"  # default axis to X
if args.x:
    projaxis = "X"
if args.y:
    projaxis = "Y"
if args.z:
    projaxis = "Z"

# Ground height in mm from Z=0
ground = (args.ground)

# fit factor is a scaling to help fit to scale inside view window.
# usually needs to be within 1.0 to 2.0 for cars <-> trucks
fitfactor = (args.fitfactor)

printd("\nDEBUG ON")
printd("---------------------------------------------------------------------")

printd("FITFACTOR = ", fitfactor)
# ------------------ VTK Render Setup -----------------------------------------
max_frame = args.res  # sets max resolution, render windows size

# Create the renderer
ren = vtk.vtkRenderer()

# Create the window
renWin = vtk.vtkRenderWindow()

# Add the renderer to the window
renWin.AddRenderer(ren)

# Define an interactor.
iren = vtk.vtkRenderWindowInteractor()

# Set the window defined above as the window that the interactor
# will work on.
iren.SetRenderWindow(renWin)

# Initialize the object that is used to load the .stl file
stlFileReader = vtk.vtkSTLReader()

# Specify the .stl file's name.
stlFileReader.SetFileName(args.filename)

# Load the .stl file.
stlFileReader.Update()

# Get polydata from the 'stlFileReader' variable as new named 'surfacePolyData'
surfacePolyData = stlFileReader.GetOutput()

triangles_count = surfacePolyData.GetNumberOfCells()

# Clipping plane for ground
plane = vtk.vtkPlane()
plane.SetNormal(0, 0, 1)
plane.SetOrigin(0, 0, ground)

clip = vtk.vtkClipPolyData()
clip.SetClipFunction(plane)
clip.SetInputData(surfacePolyData)
clip.Update()
surfacePolyData = clip.GetOutput(0)

# Get Boundary of resultant data
bounds = surfacePolyData.GetBounds()

x_bounds = bounds[0:2]
y_bounds = bounds[2:4]
z_bounds = bounds[4:6]

printd("Bounds in x = ", x_bounds)
printd("Bounds in y = ", y_bounds)
printd("Bounds in z = ", z_bounds)

intXdim = int(abs(x_bounds[0])+abs(x_bounds[1]))
intYdim = int(abs(y_bounds[0])+abs(y_bounds[1]))
intZdim = int(abs(z_bounds[0])+abs(z_bounds[1]))

printd("model X Dimension = ", intXdim)
printd("model Y Dimension = ", intYdim)
printd("model Z Dimension = ", intZdim)

# Check for model dimensions that aren't going to work.
if (intXdim or intYdim or intZdim) < 100:
    print("Model dimensions small, methods likely innacurate.")
    print("Program meant for vehicle models in mm units.")
    print("Program exiting...")
    quit()

if (intXdim or intYdim or intZdim) > 30000:
    print("Model dimensions very large, methods likely inoperable.")
    print("Program exiting...")
    quit()

if projaxis == "X":
    frame_width = (intYdim)
    frame_height = (intZdim)

if projaxis == "Y":
    frame_width = (intXdim)
    frame_height = (intZdim)

if projaxis == "Z":
    frame_width = (intXdim)
    frame_height = (intYdim)

minscale = min([frame_width, frame_height])
maxscale = max([frame_width, frame_height])

aspect = frame_width/frame_height

printd("ASPECT RATIO = ", aspect)
printd("FRAME WIDTH = ", frame_width)
printd("FRAME HEIGHT = ", frame_height)

# Find center
x_center = (int(np.average(x_bounds)))
y_center = (int(np.average(y_bounds)))
z_center = (int(np.average(z_bounds)))

printd("X CENTER = ", x_center)
printd("Y CENTER = ", y_center)
printd("Z CENTER = ", z_center)

# Initialize the mapper
surfaceMapper = vtk.vtkPolyDataMapper()
surfaceMapper.SetInputData(surfacePolyData)

# Initialize the actor
surfaceActor = vtk.vtkActor()
surfaceActor.SetMapper(surfaceMapper)

# Render projection all white
surfaceActor.GetProperty().SetColor(255, 255, 255)

# Add the actor to the renderer
ren.AddActor(surfaceActor)

# Interactor initialize
iren.Initialize()
camera = ren.GetActiveCamera()
camera.ParallelProjectionOn()

camera.SetParallelScale(max_frame*fitfactor)  # fitfactor used here

camera.SetClippingRange(-100000, 100000)  # really large so no clipping

# Set up view on center of data
if projaxis == "X":
    camera.SetViewUp(0, 0, 1)
    camera.SetPosition((x_center + 1), y_center, z_center)

if projaxis == "Y":
    camera.SetViewUp(0, 0, 1)
    camera.SetPosition(x_center, (y_center + 1), z_center)

if projaxis == "Z":
    camera.SetViewUp(0, 1, 0)
    camera.SetPosition(x_center, y_center, (z_center + 1))


camera.SetFocalPoint(x_center, y_center, z_center)

grabber = vtk.vtkWindowToImageFilter()
grabber.SetInput(renWin)
renWin.SetSize(int(max_frame*aspect), max_frame)
grabber.Update()

if args.nosave is False:  # Save the resulting render to a file for safekeeping
    writer = vtk.vtkPNGWriter()
    writer.SetInputData(grabber.GetOutput())
    writer.SetFileName(os.path.splitext(args.filename)[0] + "_output.png")
    writer.Write()

img = grabber.GetOutput()
rows, cols, _ = img.GetDimensions()
img = vtk_to_numpy(img.GetPointData().GetScalars())
img = img.reshape(cols, rows, -1)

img = (np.dot(img[..., :3], [1/3, 1/3, 1/3])).astype(int)  # rgb to mono

borders = [img[0, :], img[-1, :], img[:, 0], img[:, -1]]
borderCount = 0
for elem in borders:
    borderCount += np.sum(elem)

if borderCount > 0:  # white pixels on border means model got cropped!
    print("\nModel is not fit to render window, results cannot be computed")
    print("accurately.  Change argument -fitfactor to a greater value.")
    print("Program exiting...")
    quit()

# ------------------ Area Calculation -----------------------------------------
# Take the output and do the area calculation
n_white_pixels = np.sum(img == 255)  # sum the white pixels in the render

proj_area = (n_white_pixels*(fitfactor**2)) / (250000)  # math for px/m^2

# Print the details to the command line

print("\nFRONTAL AREA PROJECTION")
print("----------------------------------------------------------------------")
print("Assumes STL in millimeters, area will be calculated in square meters.")
print("Total number of triangles in STL: \t", triangles_count, "\n")
print("Projected Direction is in: \t\t", projaxis, " axis\n")
print("Projected Area: \t\t\t", proj_area, " m^2\n")
print("Time to Compute: \t\t\t", time.process_time(), " seconds")
print("----------------------------------------------------------------------")

# ------------------ Show Window ----------------------------------------------
if args.noshow is False:
    print("FINISHED")
    print("Close VTK window to exit...")
    iren.Start()  # Start the event loop to show the render

else:
    print("FINISHED")
    quit()
