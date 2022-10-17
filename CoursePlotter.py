#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: CoursePlotter.py
#  Author: Lorenzo Kearns
#
#  Purpose: Finalize and set a true heading for the ship, also contain future waypoints
#*******************************************************************************************************************#
from Cartographer import Cartographer
from Wayfinder import WayFinder
from utilities import Tools
import time
from glob import *
import math
from math import *
import numpy

class NoGoZone():
    def __init__(self, adjWindPos, adjWindNeg):
        self.max = adjWindPos
        self.min = adjWindNeg

class SailSides():
    def __init__(self, TWA, origin, SAK):
        self.star = RangeOfPOS(SAK.mod360((TWA + 180) + origin), SAK)
        self.port = RangeOfPOS(SAK.mod360((TWA + 180) - origin), SAK)

class RangeOfPOS():
    def __init__(self, thetaPOS, SAK):
        self.max = SAK.mod360(thetaPOS + 15)
        self.min = SAK.mod360(thetaPOS - 14)
        self.optimal = SAK.mod360(thetaPOS)

class PointOfSailing():
    """
        Defines the ranges for points of sail.
        Allows us to determine the speeds
        and paths which can be taken to optimize speed to the desitnation
    """
    def __init__(self, TWA):
        self.SAK = Tools()
        self.closeHaul = SailSides(TWA, 45, self.SAK)
        self.closeReach = SailSides(TWA, 60, self.SAK)
        self.beamReach = SailSides(TWA, 90, self.SAK)
        self.broadReach = SailSides(TWA, 120, self.SAK)
        self.trainingRun = SailSides(TWA, 150, self.SAK)
        self.Run = SailSides(TWA, 180, self.SAK)
        self.adjust()

    def adjust(self):
        """
            Adjust edge cases for points of sail such as
            close haul
        """
        self.closeHaul.star.min = self.closeHaul.star.optimal
        self.closeHaul.port.max = self.closeHaul.port.optimal
        self.closeHaul.star.max = self.closeHaul.star.max - 10
        self.closeHaul.port.min = self.closeHaul.port.min + 10
        self.closeReach.star.min = self.closeReach.star.min + 5
        self.closeReach.port.max = self.closeReach.port.max - 5

class CoursePlotter():
    """
        Class is callable by Main.py and uses Wayfinder
        and Cartographer classes alongside its own
        fucntions.
    """
    def __init__(self, start, end, TWA, maxDev):
        self.beat_dir = "right"
        self.inJibeManeuver = False
        self.currentlyBeating = False
        self.inTackManeuver = False
        self.currBear = 0
        self.desBear = 0
        self.Way = WayFinder()
        self.Map = Cartographer(80)
        self.SAK = Tools()
        self.POS = PointOfSailing(TWA)
        self.mode = "straight"
        self.final_adjust = False
        self.twa = TWA
        self.directPathOrient = self.SAK.direction_lookup(start[0], start[1], end[0], end[1])
        self.dist = self.SAK.Distance(start[0], start[1], end[0], end[1])
        self.pos = [start[0], start[1]]
        self.end = [end[0], end[1]]
        print(self.dist)
        windPlus = self.SAK.mod360((TWA+180)+45) # adjusted wind plus 45
        windSub = self.SAK.mod360((TWA+180)-45) # adjusted wind minus 45
        self.NoGoRange = NoGoZone(windPlus, windSub)
        print(self.NoGoRange.min, self.NoGoRange.max)
        self.tackComplete = False
        self.boundLakelon, self.boundLakelat = self.Map.listOfLakeEdgesLon, self.Map.listOfLakeEdgesLat
        self.startWayp = start
        self.endWayp = end
        # self.set_path_type()
        self.timer1 = time.perf_counter()
        self.timer2 = time.perf_counter()
        self.jibeCooldown = 0
        self.lastWind = 0
        self.shore = self.Map.get_object_direction()
        self.maxDeviationFromPath = maxDev
        self.deviated = False
        self.tackPOS = self.POS.broadReach.star.optimal
        self.windChanged = False

    def adjustWind(self, wind):
        self.twa = wind
        windPlus = self.SAK.mod360((self.twa+180)+45) # adjusted wind plus 45
        windSub = self.SAK.mod360((self.twa+180)-45) # adjusted wind minus 45
        self.NoGoRange.min = windSub
        self.NoGoRange.max = windPlus
        self.POS = PointOfSailing(self.twa)

    def find_dir_traveling(self, vesselBearing):
        if(vesselBearing < 180 and vesselBearing > 0):
            return EAST
        else:
            return WEST

    def find_course(self,x ,y, currBearing):
        """
            put it all together to call from main and decide how we move
        """
        self.pathDir = self.find_dir_traveling(currBearing)
        if(time.perf_counter() - self.timer2 > 3): #Debug
            self.timer2 = time.perf_counter()
            # print("Star Beam Optimal" + str(self.POS.beamReach.star.optimal))
            # print("Star Beam min" + str(self.POS.beamReach.star.min))
            # print("Star Beam max" + str(self.POS.beamReach.star.max))
            # print("Port Beam Optimal" + self.POS.beamReach.port.optimal)
            # print("Port Beam Optimal" + self.POS.beamReach.port.min)
            # print("Port Beam Optimal" + self.POS.beamReach.port.max)
            # print("Traveling " + str(self.pathDir))
            # print("Deviation from path is: " + str(abs(self.devFromPath)))
        if(not self.inJibeManeuver and not self.inTackManeuver):
            self.should_heading_change(x, y, currBearing)
            self.shore = self.Map.get_object_direction()
            bearing = currBearing
        elif(self.inJibeManeuver):
            # print(self.desBear) # Testing statement
            bearing = self.jibe(currBearing)
        elif(self.inTackManeuver):
            bearing = self.tack(currBearing)
        else:
            bearing = currBearing
        return bearing

    def is_past_beat_max(self, start, end,  lat, lon):
        dist = self.SAK.Distance(start[0], start[1], lat, lon)
        # crossTrack = crossTrackDistance(start, end, lat, lon, dist)
        b13 = self.SAK.deg2rad(self.trueBearing(start[0], start[1], lat, lon))
        b12 = self.SAK.deg2rad(self.trueBearing(start[0], start[1], end[0], end[1]))
        self.devFromPath = 6371000.0*asin(sin(dist/6371000.0)*sin(b13 - b12))
        if (self.maxDeviationFromPath - abs(self.devFromPath) <=0):
            self.deviated = True
        else:
            self.deviated = False
        return self.devFromPath, self.directPathOrient

    def trueBearing(self, lat1, lon1, lat2, lon2):
        lat1 = self.SAK.deg2rad(lat1)
        lon1 = self.SAK.deg2rad(lon1)
        lat2 = self.SAK.deg2rad(lat2)
        lon2 = self.SAK.deg2rad(lon2)
        angle = atan2(sin(lon2 - lon1) * cos(lat2), cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1))
        return self.SAK.rad2deg(angle)

    def jibe(self, currBear):
        """
            Perform a jibe maneuver
        """
        # print("I am Trying to jibe")
        self.jibeCooldown = time.perf_counter()
        if(self.beat_dir == "right"):
            if(not math.isclose(currBear, self.desBear, abs_tol = 1.5)):
                currBear += 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inJibeManeuver = False
                return currBear
        elif(self.beat_dir == "left"):
            if(not math.isclose(currBear, self.desBear, abs_tol = 1.5)):
                currBear -= 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inJibeManeuver = False
                return currBear
        else:
            print("error")

    def tack(self, currBear):
        """
            Perform a tack maneuver
        """
        # print("I am Trying to tack")
        if(self.tackDir == "left"):
            if(not math.isclose(currBear, self.desBear, abs_tol = 1.5)):
                currBear += 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inTackManeuver = False
                return currBear
        elif(self.tackDir == "right"):
            if(not math.isclose(currBear, self.desBear, abs_tol = 1.5)):
                currBear -= 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inTackManeuver = False
                return currBear

    def should_heading_change(self, x, y, bearing):
        """
            Call to cartographer to check if the current path
            is safe, to include more functionality later
        """
        self.Map.update_boat_pos(x,y,bearing)
        self.directPathOrient = self.SAK.direction_lookup(self.pos[0], self.pos[1], self.end[0], self.end[1])
        self.safe = self.Map.check_shoreline()
        if(not self.final_adjust):
            if(self.dist < 100 and not self.in_no_go_range(self.SAK.mod360(self.directPathOrient-10))):
                bearing = self.adjust_path(bearing)
                self.desBear = self.SAK.mod360(self.directPathOrient)
                return bearing
            elif(not self.safe and time.perf_counter()):
                self.shore = self.Map.get_object_direction()
                bearing  = self.adjust_path(bearing)
                # print("I know its not safe")
            elif(self.deviated):
                # print("I am off the beaten path")
                bearing = self.adjust_path(bearing)
            elif(self.twa != self.lastWind):
                # print("The winds howling")
                self.lastWind = self.twa
                bearing = self.adjust_path(bearing)
            return bearing
        else:
            return bearing

    def adjust_path(self, bearing):
        """
            Determine how to adjust bearing based
            on the mode of travel in effect
        """
        # if(time.perf_counter() - self.timer1 > 1):
        # self.timer1 = time.perf_counter()
        self.inJibeManeuver = False
        self.inTackManeuver = False
        if(self.in_no_go_range(self.directPathOrient)):
            # print("beating required")
            bearing = self.beat_adjust(bearing)
        else:
            # print("We Can go straight now")
            bearing = self.straight_adjust(bearing)
        return bearing

    def beat_adjust(self, currBearing):
        """
            determine what direction to beat in.
            unsafe right now, does not include jibe vs
            tack
        """
        if(not self.safe):
            if(self.shore == RIGHT and self.pathDir == EAST):
                self.beat_dir = "left"
                self.desBear = self.SAK.mod360(self.NoGoRange.min - 12)
            elif(self.shore == LEFT and self.pathDir == WEST):
                self.beat_dir = "right"
                self.desBear = self.SAK.mod360(self.NoGoRange.max + 12)
            else:
                self.desBear = currBearing
            self.inJibeManeuver = True
            return self.desBear
        elif(self.deviated):
            if(self.devFromPath > 0):
                self.beat_dir = "left"
                self.desBear = self.SAK.mod360(self.NoGoRange.min - 12)
            elif(self.devFromPath < 0):
                self.beat_dir = "right"
                self.desBear = self.SAK.mod360(self.NoGoRange.max + 12)
            self.inJibeManeuver = True
            self.deviated = False
            return self.desBear
        else:
            if(self.pathDir == EAST):
                self.beat_dir = "right"
                self.desBear = self.SAK.mod360(self.NoGoRange.min - 12)
            elif(self.pathDir == WEST):
                self.beat_dir = "left"
                self.desBear = self.SAK.mod360(self.NoGoRange.max + 12)
            self.inJibeManeuver = True
            return self.desBear

    def straight_adjust(self, currBearing):
        """
            Future implement: Determines how to adjust bearing when a direct path is being followed
            Ideally should return the boat to the original path when object is avoided. could be used
            conditionallt in beat as well in later versions of the code
        """
        if(not self.safe):
            if(self.shore == RIGHT and self.pathDir == EAST):
                self.tackDir = "left"
                self.desBear = self.SAK.mod360(currBearing - 45)
                print("I am trying to go left")
            elif(self.shore == LEFT and self.pathDir == WEST):
                self.tackDir = "right"
                print("I am trying to go right")
                self.desBear = self.SAK.mod360(currBearing + 45)
            else:
                self.desBear = currBearing
            self.inTackManeuver = True
            return self.desBear
        elif(self.deviated):
            self.tackPOS_star, self.tackPOS_port  = self.find_best_bearings()
            if(self.devFromPath > 0):
                self.tackDir = "left"
                self.desBear = self.tackPOS_port
            elif(self.devFromPath < 0):
                self.tackDir = "right"
                self.desBear = self.tackPOS_star
            self.inTackManeuver = True
            self.deviated = False
            return self.desBear
        else:
            self.tackPOS_star, self.tackPOS_port  = self.find_best_bearings()
            if(self.pathDir == EAST):
                self.tackDir = "right"
                self.desBear = self.tackPOS_star
            elif(self.pathDir == WEST):
                self.tackDir = "left"
                self.desBear = self.tackPOS_port
            self.inTackManeuver = True
            return self.desBear

    def find_best_bearings(self):
        tolerance = 60
        if(self.is_between_angles(self.POS.beamReach.star.optimal, self.directPathOrient, 2) or self.is_between_angles(self.POS.beamReach.port.optimal, self.directPathOrient, 2)):
            return self.directPathOrient, self.directPathOrient
        elif(self.is_between_angles(self.POS.broadReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.broadReach.port.optimal, self.directPathOrient, tolerance)):
            # print("Broad reach is a go!")
            return self.POS.broadReach.star.optimal, self.POS.broadReach.port.optimal
        elif(self.is_between_angles(self.POS.closeReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.closeReach.port.optimal, self.directPathOrient, tolerance)):
            # print("closeReach it is")
            return self.POS.closeReach.star.optimal, self.POS.closeReach.port.optimal
        elif(self.is_between_angles(self.POS.broadReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.beamReach.star.optimal, self.directPathOrient, tolerance)):
            # print("Beam broad")
            return self.POS.broadReach.star.optimal, self.POS.beamReach.star.optimal
        elif(self.is_between_angles(self.POS.closeReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.beamReach.star.optimal, self.directPathOrient, tolerance)):
            # print("Beam Close")
            return self.POS.closeReach.star.optimal, self.POS.beamReach.star.optimal
        elif(self.is_between_angles(self.POS.beamReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.trainingRun.star.optimal, self.directPathOrient, tolerance)):
            # print("Beam train Coming")
            return self.POS.beamReach.star.optimal, self.POS.trainingRun.star.optimal
        elif(self.is_between_angles(self.POS.broadReach.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.closeReach.star.optimal, self.directPathOrient, tolerance)):
            # print("Broad close wombo combo")
            return self.POS.broadReach.star.optimal, self.POS.closeReach.star.optimal
        elif(self.is_between_angles(self.POS.broadReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.beamReach.port.optimal, self.directPathOrient, tolerance)):
            # print("Beam broad")
            return self.POS.broadReach.port.optimal, self.POS.beamReach.port.optimal
        elif(self.is_between_angles(self.POS.closeReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.beamReach.port.optimal, self.directPathOrient, tolerance)):
            # print("Beam Close")
            return self.POS.closeReach.port.optimal, self.POS.beamReach.port.optimal
        elif(self.is_between_angles(self.POS.beamReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.trainingRun.port.optimal, self.directPathOrient, tolerance)):
            # print("Beam train Coming")
            return self.POS.beamReach.port.optimal, self.POS.trainingRun.port.optimal
        elif(self.is_between_angles(self.POS.broadReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.closeReach.port.optimal, self.directPathOrient, tolerance)):
            # print("Broad close wombo combo")
            return self.POS.broadReach.port.optimal, self.POS.closeReach.port.optimal
        elif(self.is_between_angles(self.POS.broadReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.trainingRun.star.optimal, self.directPathOrient, tolerance)):
            # print("Broad Training")
            return self.POS.broadReach.port.optimal, self.POS.trainingRun.star.optimal
        elif(self.is_between_angles(self.POS.broadReach.port.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.trainingRun.port.optimal, self.directPathOrient, tolerance)):
            # print("Broad Training")
            return self.POS.broadReach.star.optimal, self.POS.trainingRun.port.optimal
        elif(self.is_between_angles(self.POS.trainingRun.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.trainingRun.port.optimal, self.directPathOrient, tolerance)):
            # print("We making a training run")
            return self.POS.trainingRun.star.optimal, self.POS.trainingRun.port.optimal
        elif(self.is_between_angles(self.POS.Run.star.optimal, self.directPathOrient, tolerance) and self.is_between_angles(self.POS.Run.port.optimal, self.directPathOrient, tolerance)):
            # print("Buckle in boys shes going on a full run!")
            return self.POS.Run.star.optimal, self.POS.Run.port.optimal
        else:
            print("Big Error")
            return 0, 0

    def is_between_angles(self, testAngle, targetAngle, tolerance):
        print("test angle is: " + str(testAngle))
        print("is it between: " + str(targetAngle - tolerance) + "and: " + str(targetAngle + tolerance))
        anglediff = self.SAK.mod360(testAngle - targetAngle + 180 + 360) - 180
        if (anglediff <= tolerance and anglediff >= -tolerance):
            # print("True")
            return True
        else:
            return False

    def set_path_type(self):
        """
            Called only on initialization or great change in wind direction
            Determines what type of path, i.e beating, curved, straight, etc
            is best for the current wind conditions to reach the desired waypoint
        """
        if(self.in_no_go_range(self.directPathOrient)):
            self.mode = "beat"
            self.beat_dir = "right"
            return self.SAK.mod360(self.NoGoRange.max + 12)
        else:
            self.mode = "straight"
            return self.directPathOrient

    def in_no_go_range(self, directPath):
        """
            Check if the desired direction is in the no go zone
            if its not we can take a direct path for now, in the future
            it might be nice to take angular paths to optimize speed
        """
        if(self.twa <= 225 and self.twa > 134):
            if(directPath < self.NoGoRange.max or directPath > self.NoGoRange.min):
                return True
            else:
                return False
        else:
            if(directPath < self.NoGoRange.max and directPath > self.NoGoRange.min):
                return True
            else:
                return False

    def check_dist_to_target(self, posLat, posLon, end):
        self.pos[0], self.pos[1] = posLat, posLon
        self.end[0], self.end[1] = end[0], end[1]
        self.dist = self.SAK.Distance(posLat, posLon, end[0], end[1])
        return self.dist

    def define_speed(self, TWS):
        wa, bsp = self.Way.create_lookup_table(TWS)
        return wa, bsp
