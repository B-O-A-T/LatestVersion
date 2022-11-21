#*******************************************************************************************************************#
#  Project: B.O.A.T.
#  File: Main.py
#  Author: Lorenzo Kearns
#
#  Purpose: Running boat code
#*******************************************************************************************************************#
#
#****************************************************************#
# Includes:
from CoursePlotter import CoursePlotter
from utilities import Tools
from SensorTranslator import Telemetry
# from VectorNav300 import VN300
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import numpy as np
import time
import csv
from glob import *
#****************************************************************#

# class sailController():
#     def __init__(self):
#         self.sailAngle = 0.0
#     def winch_out(self):
#         raise NotImplemented
#     def winch_in(self):
#         raise NotImplemented
# class rudderController():
#     raise NotImplemented

class main():
    """
        Main and stuff
    """
    def __init__(self):
        """
            Setup program intialization 
            values and leads into the 
            ultimate program loop
        """
        self.timer1 = time.perf_counter()
        self.trailX = [] # track travelled gps Longitude 
        self.trailY = [] # track travelled gps Lattitude
        # self.read_waypoint_csv()
        # self.print_waypoints()
        self.Telem = Telemetry()
        self.SAK = Tools()
        self.VN = VN300() # a VN300 object, this represent the VN300 and accompanying software methods 
        self.handshake_with_GC()
        self.read_waypoint_csv()
        self.update_wind() 
        self.wait_for_gps()
        self.STARTING_POS = self.gpsLon, self.gpsLat
        self.WAYPOINT1 = self.waypoints[0]
        self.CourseBoi = CoursePlotter(self.STARTING_POS, self.WAYPOINT1, self.TWA, MAX_PATH_DEVIATION)
        self.desHeading = self.CourseBoi.find_course(self.gpsLon, self.gpsLat, self.trueVesselBearing) # We want to find a course 
        devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, self.WAYPOINT1, self.gpsLat, self.gpsLon)
        self.run()
           
    def read_waypoint_csv(self):
        """
            Read in user devined waypoints 
            that have been specified in the
            waypoints.csv file
        """
        self.waypoints = []
        with open('waypoints.csv') as file_obj:
            reader_obj = csv.reader(file_obj)
            for row in reader_obj: 
                # for 
                self.waypoints.append(row)
        """
            Here we want to generate a list of the waypoints we
            will be tracking, use this to print out the data for 
            the waypoint gen test 
        """        

    def print_waypoints(self):
     # Create a Stamen Terrain instance.
        global plot_array_x
        global plot_array_y
        plot_array_x = []
        plot_array_y = []
        stamen_terrain = cimgt.OSM()
        # Create a GeoAxes in the tile's projection.
        ax = plt.axes(projection=stamen_terrain.crs)
        zoomRatio = 0.005
        waypoint_num = 1
        # Limit the extent of the map to a small longitude/latitude range.
        ax.set_extent([-112.388989, -112.382, 34.5150517, 34.5230208])
        # ax.set_extent([-55, -45, 40, 50])
        # Add the Stamen data at zoom level 8.
        scale = np.ceil(-np.sqrt(2)*np.log(np.divide(zoomRatio,350.0))) # empirical solve for scale based on zoom
        scale = (scale<20) and scale or 19 # scale cannot be larger than 19
        ax.add_image(stamen_terrain, int(scale))
        # plot the line the boat would ideally take
        plt.title("Waypoint tracked path")
        # plot_array_y, plot_array_x = map(list,zip(*self.waypoints))

        for i in range(len(self.waypoints)):
            plot_array_x.append(self.waypoints[i][1])
            plot_array_y.append(self.waypoints[i][0]) 

        plot_array_x = np.array(plot_array_x)
        plot_array_y = np.array(plot_array_y)
        print(plot_array_x)
        print(plot_array_y)
        print(len(self.waypoints) -1)
        

        # plt.plot(plot_array_x, plot_array_y, 'r-', marker='o', color='black', markersize=1, transform=ccrs.Geodetic())
        plt.plot(plot_array_x[len(self.waypoints) -1], plot_array_y[len(self.waypoints) -1], marker='x', color='red', markersize=7,
                    alpha=0.7, transform=ccrs.Geodetic())
        geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
        text_transform = offset_copy(geodetic_transform, units='dots', x=-25)
        plt.text(plot_array_x[len(self.waypoints) -1], plot_array_y[len(self.waypoints) -1], u'Final Waypoint',
                    verticalalignment='top', horizontalalignment='left',
                    transform=text_transform,
                    bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))
        # show waypoints
        for i in range(len(self.waypoints) -1):
            plt.plot(plot_array_x[i], plot_array_y[i], marker='x', color='red', markersize=4,
            alpha=0.7, transform=ccrs.Geodetic())
            geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
            text_transform = offset_copy(geodetic_transform, units='dots', x=-25)

            # Add text 25 pixels to the left of the volcano.
            plt.text(plot_array_x[i], plot_array_y[i], u'Waypoint %d'%(waypoint_num),
            verticalalignment='center', horizontalalignment='right',
            transform=text_transform,
            bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))
            waypoint_num += 1
        plt.show()
        plt.gcf().canvas.draw()
        fig = plt.figure()
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().grid(row=1,column=24)
        canvas.draw()

    def handshake_with_GC(self):
        self.Telem.handshake_with_arduino() # idk probably didnt need a whole function in main to do a single external function but I dont really care, if your reading this and dont like it then fix it yourself

    def update_wind(self):
        """
            Ask the Grand Central for some wind 
            data, sets values for wind speed and 
            wind direction that have been collected
            from the anemometer and winf vane respectively 
        """
        self.windSpdApp = self.Telem.send_telem_request(self.Telem.telem.windSpeed)
        self.windAngApp = self.Telem.send_telem_request(self.Telem.telem.apWind)
        # Implement translation to true wind speed and direction
        self.TWA = self.windAngApp # josh and jacob apply that function yall said you made here 
        self.TWS = self.windSpdApp
        # print("Wind Speed: " + str(self.TWS)) # debug
        # print("Wind Angle: " + str(self.TWA))


    def update_bearing(self):
        """
            Send a request to the VN300 to get a 
            reading of the current held bearing
        """
        self.trueVesselBearing = self.SAK.mod360(self.VN.get_bearing())
        # print("Vessel bearing: " + str(self.trueVesselBearing)) # debug
        """
            delete above values and 
            add functionality to 
            send and receive bearing
            from vectorNav
        """

    def update_position(self): 
        """
            Send a reqeust to the VN300 to get a 
            reading of the current lat and lon position '
            variables
        """
        x, y = self.VN.get_position()
        self.gpsLon = x
        self.gpsLat = y
        # print("Longitude: " + str(x) + ", Lattitude: " + str(y)) # use for debug stuff 

    def wait_for_gps(self):
        while(self.gpsLon == 0 & self.gpsLat == 0):
            self.update_position()

    def run(self):
        """
            looping until the invetable fiery implosion that 
            destroys the earth and world as we know it, 
            or until the program crashes :), handles normal 
            opreation of the system
        """
        while True:
            if(time.perf_counter() - self.timer1 > 1.5):
                self.timer1 = time.perf_counter()
                self.update_wind()
                self.update_bearing()
                self.update_position()
                self.trailX.append(self.gpsLng)
                self.trailY.append(self.gpsLat)
                devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, self.WAYPOINT1, self.gpsLat, self.gpsLon)
                self.desHeading = self.CourseBoi.find_course(self.gpsLon, self.gpsLat, self.trueVesselBearing)


                """
                    Conditional shit; probably good to ask if we are currently at out desired sail and rudder angles if not 
                    lets do somethin about that shit
                """

                """
                    Enter stuff about motor controller for rudder here 
                """

                """
                    Enter stuff about motor controller for sail right about here
                """

if __name__ == "__main__":
    main()

            
