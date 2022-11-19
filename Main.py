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
from Compass import Compass
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

# begin main code:
class main():
    def __init__(self):
        self.Telem = Telemetry()
        self.SAK = Tools()
        self.VN = VN300()
        self.handshake_with_GC()
        self.timer1 = time.perf_counter()
        self.update_wind()
        self.gpsLon, self.gpsLat = self.update_position()
        self.trueVesselBearing = 0
        self.STARTING_POS = self.gpsLon, self.gpsLat
        self.read_waypoint_csv()
        WAYPOINT1 = self.waypoints[0]
        self.CourseBoi = CoursePlotter(self.STARTING_POS, WAYPOINT1, self.TWA, MAX_PATH_DEVIATION)
        # # self.compass = Compass(0, 0)
        self.desHeading = self.CourseBoi.find_course(self.gpsLon, self.gpsLat, self.trueVesselBearing) # We want to find a course 
        devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLon)
        self.run()
           
    def read_waypoint_csv(self):
        self.waypoints = []
        with open('waypoints.csv') as file_obj:
            reader_obj = csv.reader(file_obj)
            for row in reader_obj:  
                self.waypoints.append(row)        

    def handshake_with_GC(self):
        self.Telem.handshake_with_arduino()

    def update_wind(self):
        self.windSpdApp = self.Telem.send_telem_request(self.Telem.telem.windSpeed)
        self.windAngApp = self.Telem.send_telem_request(self.Telem.telem.apWind)
        # Implement translation to true wind speed and direction
        self.TWA = self.windAngApp
        self.TWS = self.windSpdApp
        print("Wind Speed: " + str(self.TWS))
        print("Wind Angle: " + str(self.TWA))


    def update_bearing(self):
        self.trueVesselBearing = self.SAK.mod360(self.VN.get_bearing())
        print("Vessel bearing: " + str(self.trueVesselBearing))
        """
            delete above values and 
            add functionality to 
            send and receive bearing
            from vectorNav
        """

    def update_position(self):
        x, y = self.VN.get_position()
        """
            delete above values and 
            add functionality to 
            send and receive lat and lon values 
            from vectorNav
        """
        print("Longitude: " + str(x) + ", Lattitude: " + str(y))
        return x, y

    def run(self):
        while True:
            if(time.perf_counter() - self.timer1 > 1.5):
                self.timer1 = time.perf_counter()
                devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(self.STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLon)
                self.desHeading = self.CourseBoi.find_course(self.gpsLon, self.gpsLat, self.trueVesselBearing)
                self.update_wind()
                self.update_bearing()
                self.update_position()
                # if(self.compass.vesselBearing != self.desHeading):

if __name__ == "__main__":
    main()

            
