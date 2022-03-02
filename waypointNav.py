#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: waypointNav.py
#  Author: Lorenzo Kearns
#  Versions:
#   version: 0.1 10/25/2021 - Initial Program Creation
#   version: 1.0 10/26/2021 - Working map of lynx lake with accurate longitude and lattitude overlay
#   version: 2.0 11/01/2021 - Reconfigure of the program without initial startup map, working navigation map which saves longitude
#                  and lattitude of mouse click. Removed excess code features, renamed variables to be more intuitve, cleaned up code and added comments
#   version: 3.0 11/08/2021 - Fixed GUI so you no longer have to set the boundaries
#  Purpose: GUI for selecting waypoints and displaying desired data from boat sensors.
#*******************************************************************************************************************#
#
#
#****************************************************************#
# Includes:
import io
import csv
import time
import serial
import numpy as np
import pandas as pd
import tkinter as tk
from PIL import Image
from tkinter import *
import cartopy.crs as ccrs
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
from descartes import PolygonPatch
from urllib.request import urlopen, Request
from matplotlib.transforms import offset_copy
from tkinter.filedialog import askopenfilename
from shapely.geometry import Point, LineString, Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#****************************************************************#
#
#
arduino = serial.Serial(port='COM10', baudrate=115200, timeout=.1)
#***************************************************#
# Beginning of functions living outside the GUI loop
#****************************************************************#
# Function to create the interactive image for the GUI
#****************************************************************#
def image_spoof(self, tile): # this function pretends not to be a Python script
    url = self._image_url(tile) # get the url of the street map API
    req = Request(url) # start request
    req.add_header('User-agent','Anaconda 3') # add user agent to request
    fh = urlopen(req)
    im_data = io.BytesIO(fh.read()) # get image
    fh.close() # close url
    img = Image.open(im_data) # open image with PIL
    img = img.convert(self.desired_tile_form) # set image format
    return img, self.tileextent(tile), 'lower' # reformat for cartopy
# End of image_spoof
#****************************************************************#
#
#
#****************************************************************#
# Function to create a plot showing user selected waypoints
#****************************************************************#
def plotStuff():
     # Create a Stamen Terrain instance.
    global desired_waypoint
    global boat_origin
    stamen_terrain = cimgt.OSM()
    # Create a GeoAxes in the tile's projection.
    ax = plt.axes(projection=stamen_terrain.crs)
    zoomRatio = 0.005
    waypoint_num = 1
    # Limit the extent of the map to a small longitude/latitude range.
    ax.set_extent([-112.388989, -112.382, 34.5150517, 34.5230208])
    # ax.set_extent([-55, -45, 40, 50])
    scale = np.ceil(-np.sqrt(2)*np.log(np.divide(zoomRatio,350.0))) # empirical solve for scale based on zoom
    scale = (scale<20) and scale or 19 # scale cannot be larger than 19
    ax.add_image(stamen_terrain, int(scale))
    # plot the line the boat would ideally take
    plt.title("Waypoint tracked path")
    plt.plot(desired_waypoint.lon, desired_waypoint.lat, marker='x', color='red', markersize=7,
                 alpha=0.7, transform=ccrs.Geodetic())
    geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    text_transform = offset_copy(geodetic_transform, units='dots', x=-25)
    plt.text(desired_waypoint.lon, desired_waypoint.lat, u'Target Waypoint',
                 verticalalignment='top', horizontalalignment='left',
                 transform=text_transform,
                 bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))

    plt.plot(boat_origin.lon, boat_origin.lat, marker='x', color='red', markersize=7,
                 alpha=0.7, transform=ccrs.Geodetic())
    geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    text_transform = offset_copy(geodetic_transform, units='dots', x=-25)
    plt.text(boat_origin.lon, boat_origin.lat, u'Boat starting position',
                 verticalalignment='top', horizontalalignment='left',
                 transform=text_transform,
                 bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))
    plt.show()
    plt.gcf().canvas.draw()
    fig = plt.figure()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().grid(row=1,column=24)
    canvas.draw()
# End of plotStuff
#****************************************************************#
#
#
#
#****************************************************************#
# Function to create a plot showing user selected waypoints
#****************************************************************#
def plotBoundaries():
    global poly
    global boundaryArrayLat
    global boundaryArrayLon
    global boat_poly
     # Create a Stamen Terrain instance.
    stamen_terrain = cimgt.OSM()
    # Create a GeoAxes in the tile's projection.
    ax = plt.axes(projection=stamen_terrain.crs)
    zoomRatio = 0.005
    waypoint_num = 1
    # Limit the extent of the map to a small longitude/latitude range.
    ax.set_extent([-112.388989, -112.382, 34.5150517, 34.5230208])
    # ax.set_extent([-55, -45, 40, 50])
    scale = np.ceil(-np.sqrt(2)*np.log(np.divide(zoomRatio,350.0))) # empirical solve for scale based on zoom
    scale = (scale<20) and scale or 19 # scale cannot be larger than 19
    ax.add_image(stamen_terrain, int(scale))
    # plot the line the boat would ideally take
    plt.title("Boundaries")
    # plt.plot(boundaryArrayLon, boundaryArrayLat, color='#A2142F', markersize=4,
    # alpha=0.7, transform=ccrs.Geodetic())
    plt.plot(*poly.exterior.xy,transform=ccrs.Geodetic())
    plt.plot(*boat_poly.exterior.xy,transform=ccrs.Geodetic())
    plt.show()
    plt.gcf().canvas.draw()
    fig = plt.figure()
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().grid(row=1,column=24)
    canvas.draw()
# End of plotBoundaries
#****************************************************************#

def create_bound_box():
    global boundaryArrayLat, boundaryArrayLon


class LatLon():
    def __init__(self, lattitude, longitude):
        self.lat = lattitude
        self.lon = longitude

class GCMode():
    def __init__(self):
        self.listen = 0
        self.origin_to_gc = 1
        self.transmit = 2
        self.receive_waypoint = 3
        self.telem_to_gc = 4
#**********************************************************************************************#
# Define the main functionality of the program
#**********************************************************************************************#
def main():
    global lock
    global boat_origin
    global desired_waypoint
    global setWay
    global cnt
    global gc_modes
    global boundOn
    global boundaryArrayLon
    global boundaryArrayLat
    gc_modes = GCMode()
    boat_origin = LatLon(34.515647653125,-112.38510863245823)
    desired_waypoint = LatLon(0.00,0.00)
    cnt = 0
    boundOn = False
    boundaryArrayLon = []
    boundaryArrayLat = []
    setWay = False
    lock = True
    lonOrig = -112.388989 # set the longitidue at the origin
    latOrig = 34.5150517 # set the lattitude at the origin
    extentLat = -0.007983 # set the extent of the lattitude from orgin to edge
    extentLon = 0.006978 # set the extent of the Longitude from orgin to edge
        # Create a tkinter object
    root = tk.Tk()
        #create canvas for the controlCenter
    controlCenter = Canvas(root, width=1920, height=1080)
    controlCenter.pack()
        # process an image for the waypoint selection window
    File = 'newLynxLake.png' # path to image that shall be used
    original = Image.open(File)
    img = ImageTk.PhotoImage(original) # create a Tk image from the file
    waypointTitle = tk.Label(controlCenter, text = "Waypoint Nav Selection").place(x = 180, y = 10)
    controlCenter.create_image(30, 30, image=img, anchor="nw") # add the image to the controlCenter canvas
        # set values for the scaling factor to be used in defining canvas boundaries
    xmLon = extentLon
    ymLat = extentLat
        # set the initial positions in lat and longitude at the origin
    xInitial = lonOrig
    yInitial = latOrig
#********#
# Ill be real, I Just totally gave up on proper function formatting since they are all in the damn loop.
#  At some point I think I can put all this into an object using classes or something,
#   for now avert your eyes future me and pretend there are now functions here
#
    # Determine the origin
    def getorigin(eventorigin):
        tk.messagebox.showinfo("Startup","Not setup yet, spam click till you see the all good message")
        global x0,y0
        x0 = 34
        y0 = 609
        print(x0,y0)
        controlCenter.bind("<Button 1>",getextentx)
    # mouseclick event
    controlCenter.bind("<Button 1>",getorigin)

    # Determine the extent of the figure in the x direction (Longitude)
    def getextentx(eventextentx):
        global xe
        xe = 453
        print(xe)
        controlCenter.bind("<Button 1>",getextenty)

    # Determine the extent of the figure in the y direction (Lattitude)
    def getextenty(eventextenty):
        global ye
        ye = 33
        print(ye)
        tk.messagebox.showinfo("All good!", "The grid is all good. Start Navigating")
        controlCenter.bind("<Button 1>",select_way)

    # print the coords to the console
    def select_way(event):
        global lock
        global boat_origin
        global desired_waypoint
        global setWay
        global boundaryArrayLon
        global boundaryArrayLat
        xDelta = xe-x0
        xm = xmLon/xDelta
        yDelta = ye-y0
        ym = -ymLat/yDelta
        # Perform coordinate transformation to normalize results
        lonWaypoint = (event.x-x0)*(xm)+xInitial
        latWaypoint = (event.y-y0)*(ym)+yInitial
        if(setWay == True):
            desired_waypoint.lat = latWaypoint
            desired_waypoint.lon = lonWaypoint
            print(desired_waypoint.lat)
            print(desired_waypoint.lon)
            setWay = False
            tk.Label(controlCenter, text = "                                                                                                ").place(x = 30, y = 640)
            tk.Label(controlCenter, text = " The waypoint was placed at: Lattitude: "+str(desired_waypoint.lat)+", Longitude: "+str(desired_waypoint.lon)).place(x = 30, y = 640)
            tk.Label(controlCenter, text = "                                                                             ").place(x = 30, y = 620)
        if (boundOn == True):
            boundaryArrayLon.append(lonWaypoint)
            boundaryArrayLat.append(latWaypoint)

    def set_origin_and_waypoint():
        global setWay
        if (setWay == False):
            setWay = True
            tk.Label(controlCenter, text = "Place the desired waypoint of the boat: ").place(x = 30, y = 620)
        elif (setWay == True):
            setWay = False

    def latlon_to_serial():
        global desired_waypoint
        arduino.flush()
        arduino.write(bytes(str(desired_waypoint.lat), 'utf-8'))
        arduino.write(bytes(str(desired_waypoint.lon), 'utf-8'))
        time.sleep(0.05)

    def get_boat_origin():
        global boat_origin
        global gc_modes
        arduino.write(bytes(str(gc_modes.origin_to_gc), 'utf-8'))
        time.sleep(0.05)
        boat_origin.lat = arduino.readline().decode('utf-8').rstrip()
        boat_origin.lon = arduino.readline().decode('utf-8').rstrip()
        arduino.write(bytes(str(curr_comm_mode), 'utf-8'))

    def define_boundaries():
        global boundOn
        boundOn = True
        tk.Label(controlCenter, text = "Begin mapping boundaries: ").place(x = 30, y = 610)

    def stopBoundaries():
        global boundOn
        boundOn = False
        tk.Label(controlCenter, text = "                                                  ").place(x = 30, y = 610)

    def write_to_file():
        global boundaryArrayLon
        global boundaryArrayLat
        boundaryArrayLon = np.array(boundaryArrayLon)
        boundaryArrayLat = np.array(boundaryArrayLat)
        n = boundaryArrayLat.size
        if(n != boundaryArrayLon.size):
            print("!!!There is an ERROR, not equal values for lat and lon!!!")
        # result_file = open('outputBoundaries.csv', 'a')
        lat_lon_array = pd.DataFrame(
            {'Lattitude': boundaryArrayLat,
             'Longitude': boundaryArrayLon
            })
        lat_lon_array.to_csv('newOutputBoundaries2.csv')

    def read_boundaries_from_csv():
        global boundaryArrayLat
        global boundaryArrayLon
        global coordTuple
        temp_container = pd.read_csv('newOutputBoundaries.csv')
        temp_container = np.array(temp_container)
        boundaryArrayLat = temp_container[:,1]
        boundaryArrayLon = temp_container[:,2]
        boundaryArrayLon = np.array(boundaryArrayLon)
        boundaryArrayLat = np.array(boundaryArrayLat)
        coordTuple = np.array((boundaryArrayLon,boundaryArrayLat)).T
        print(coordTuple)
        create_polygon()

    def create_polygon():
        global coordTuple
        global poly
        global boat_poly
        world_exterior = [(-112.388989, 34.5230208), (-112.388989, 34.5150517), (-112.382, 34.5150517), (-112.382, 34.5230208)]
        poly = Polygon(coordTuple)
        # poly_extr = poly.exterior
        boat_dimensions = [(-112.3849, 34.515117), (-112.3849, 34.5151), (-112.384795, 34.51511), (-112.384805, 34.5151)]
        boat_poly = Polygon(boat_dimensions)
        boat_dimensions = [(-112.3849, 34.515117), (-112.3849, 34.5151), (-112.384795, 34.51511), (-112.384805, 34.5151)]
        boat_poly = Polygon(boat_dimensions)
        # print(poly_extr)
        min_rec_dist = 0.000066
        # print(boat_poly.exterior.distance(poly.exterior))
        safety_threshold = boat_poly.exterior.distance(poly.exterior) - min_rec_dist
        if(safety_threshold > 0):
            print("The boat is safe and not too close to the shore")
        else:
            print("Danger the boat is at risk of collision")

    tk.Button(controlCenter, text='Show real Plot', command = plotStuff). place(x = 460, y = 60)
    tk.Button(controlCenter, text='Set Boat Waypoint', command = set_origin_and_waypoint).place(x = 460, y = 30)
    tk.Button(controlCenter, text='Send Waypoint to comms board', command = latlon_to_serial).place(x = 460, y = 90)
    tk.Button(controlCenter, text='Get the origin coords of the boat', command = get_boat_origin).place(x = 460, y = 120)
    tk.Button(controlCenter, text='Define boundaries', command = define_boundaries).place(x = 460, y = 150)
    tk.Button(controlCenter, text='Stop defining boundaries', command = stopBoundaries).place(x = 460, y = 180)
    tk.Button(controlCenter, text='Write boundaries to CSV', command = write_to_file).place(x = 460, y = 210)
    tk.Button(controlCenter, text='Read csv for boundaries', command = read_boundaries_from_csv). place(x = 460, y = 240)
    tk.Button(controlCenter, text='Show boundary Plot', command = plotBoundaries). place(x = 460, y = 270)

        # loop until the code inevitably crashes again because tkinter is ass
    root.mainloop()
# end of the main function
#**********************************************************************************************#
#*#
#*#
#*#
#**********************************************************************************************#
# Set rule to run main program and execute code
#**********************************************************************************************#
if __name__ == '__main__':
    main()
# END OF ACTIVE CODE
#**********************************************************************************************#



#**********************************************************************************************#
# code Graveyard :
#**********************************************************************************************#

    # cimgt.OSM.get_image = image_spoof # reformat web request for street map spoofing
    # map = cimgt.OSM()
    # fig = plt.figure(figsize = (8, 6), dpi = 100)
    # ax1 = plt.axes(projection = map.crs)
    # lakeCenter = [34.52, -112.386]
    # zoomRatio = 0.005
    # extent = [lakeCenter[1]-(zoomRatio*0.6),lakeCenter[1]+(zoomRatio*0.8),lakeCenter[0]-(zoomRatio),lakeCenter[0]+(zoomRatio*0.6)] # adjust to zoom
    # ax1.set_extent(extent) # set extents
    # scale = np.ceil(-np.sqrt(2)*np.log(np.divide(zoomRatio,350.0))) # empirical solve for scale based on zoom
    # scale = (scale<20) and scale or 19 # scale cannot be larger than 19
    # ax1.add_image(map, int(scale)) # add OSM with zoom specification
    # x = [-112.386 , -112.384]
    # y = [34.515, 34.52]
    # ax1.plot(x, y, 'rx-',label='Waypoint 1', linewidth = 3)
    # ax1.legend()
    # plt.show() # show the plot



    # plot_array_x = np.zeros(5)
    # plot_array_y = np.zeros(5)
    # line graphing for 1 waypoint
    # for i in range(5):
    #     # plt.plot(waypoint_long, waypoint_lat, marker='x', color='red', markersize=4,
    #     #          alpha=0.7, transform=ccrs.Geodetic())
    #     plot_array_y[i] = waypoint_lat
    #     plot_array_x[i] = waypoint_long
    #     if (waypoint_long == -112.3856):
    #         waypoint_long += np.random.rand(0.0012)
    #     else:
    #         waypoint_long -= 0.0008
    #     waypoint_lat += 0.0014



    # waypoint_long = -112.3856
    # waypoint_lat = 34.516
    # tack_right = 0
    # multiple waypoint setting
    # for i in range(5):
    #     plt.plot(waypoint_long, waypoint_lat, marker='x', color='red', markersize=4,
    #              alpha=0.7, transform=ccrs.Geodetic())
    #     geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    #     text_transform = offset_copy(geodetic_transform, units='dots', x=-25)
    #
    #     # Add text 25 pixels to the left of the volcano.
    #     plt.text(waypoint_long, waypoint_lat, u'Waypoint %d'%(waypoint_num),
    #              verticalalignment='center', horizontalalignment='right',
    #              transform=text_transform,
    #              bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))
    #     num_offset = np.random.random()*(0.001-0.0005) + 0.0005
    #     if (tack_right == 0):
    #         waypoint_long += num_offset
    #         tack_right = 1
    #     else:
    #         waypoint_long -= num_offset
    #         tack_right = 0
    #     waypoint_lat += np.random.random()*(0.0014-0.0008) + 0.0008
    #     waypoint_num += 1
