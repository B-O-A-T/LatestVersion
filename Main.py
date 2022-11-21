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
from VectorNav300 import VN300
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
        self.Telem = Telemetry()
        self.SAK = Tools()
        self.VN = VN300() # a VN300 object, this represent the VN300 and accompanying software methods 
        self.handshake_with_GC()
        self.read_waypoint_csv()
        self.timer1 = time.perf_counter()
        self.update_wind() 
        self.update_position()
        self.trueVesselBearing = 0
        self.STARTING_POS = self.gpsLon, self.gpsLat
        WAYPOINT1 = self.waypoints[0]
        self.CourseBoi = CoursePlotter(self.STARTING_POS, WAYPOINT1, self.TWA, MAX_PATH_DEVIATION)
        # # self.compass = Compass(0, 0)
        self.desHeading = self.CourseBoi.find_course(self.gpsLon, self.gpsLat, self.trueVesselBearing) # We want to find a course 
        devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLon)
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
                self.waypoints.append(row)
        """
            Here we want to generate a list of the waypoints we
            will be tracking, use this to print out the data for 
            the waypoint gen test 
        """        

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
        # return x, y

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
                devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLon)
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

            
