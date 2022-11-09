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
import time
import csv
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
        self.timer1 = time.perf_counter()
        self.CourseBoi = CoursePlotter(STARTING_POS, WAYPOINT1, self.compass.windRelNorth, MAX_PATH_DEVIATION)
        self.compass = Compass(0, 0)
        self.compass.vesselBearing = self.CourseBoi.set_path_type()
        self.boatAngles, self.boatSpeeds = self.CourseBoi.define_speed(WIND_SPEED_KNOTTS)
        self.desHeading = self.compass.vesselBearing
        self.Telem = Telemetry()
        self.desHeading = self.CourseBoi.find_course(self.gpsLng, self.gpsLat, self.compass.vesselBearing)
        devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLng)
           
    def update_wind(self):
        windSpdApp = self.Telem.send_telem_request(Telem.telem.windSpeed)
        windAngApp = self.Telem.send_telem_request(Telem.telem.apWind)
        # Implement translation to true wind speed and direction

    def update_bearing(self):
        raise NotImplemented

    def update_position(self):
        raise NotImplemented

    def run(self):
        while True:
            if(time.perf_counter() - self.timer1 > 10):
                self.timer1 = time.perf_counter()
                devFromPathDist, self.directPath = self.CourseBoi.is_past_beat_max(STARTING_POS, WAYPOINT1, self.gpsLat, self.gpsLng)
                self.desHeading = self.CourseBoi.find_course(self.gpsLng, self.gpsLat, self.compass.vesselBearing)
                # if(self.compass.vesselBearing != self.desHeading):

if __name__ == "__main__":
    main()

            
