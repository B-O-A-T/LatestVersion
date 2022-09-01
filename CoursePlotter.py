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

class NoGoZone():
    def __init__(self, adjWindPos, adjWindNeg):
        self.max = adjWindPos
        self.min = adjWindNeg

class CoursePlotter():
    """
        Class is callable by Main.py and uses Wayfinder
        and Cartographer classes alongside its own
        fucntions.
    """
    def __init__(self, start, end, TWA):
        self.beat_dir = "right"
        self.inJibeManeuver = False
        self.currentlyBeating = False
        self.inTackManeuver = False
        self.currBear = 0
        self.desBear = 0
        self.Way = WayFinder()
        self.Map = Cartographer(50)
        self.SAK = Tools()
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


    def find_course(self,x ,y, currBearing):
        """
            put it all together to call from main and decide how we move
        """
        # self.desBear = desBearing
        if(not self.inJibeManeuver and not self.inTackManeuver):
            bearing = self.is_safe(x, y, currBearing)
        elif(self.inJibeManeuver):
            # print(self.desBear) # Testing statement
            bearing = self.jibe(currBearing)
        elif(self.inTackManeuver):
            bearing = tack(currBearing)
        else:
            bearing = currBearing
        return bearing

    def jibe(self, currBear):
        """
            Perform a jibe maneuver
        """
        self.jibeCooldown = time.perf_counter()
        if(self.beat_dir == "right"):
            if(self.SAK.mod360(currBear) - self.desBear >= 3):
                # print(abs(currBear - self.desBear))
                # print(currBear, self.desBear)
                currBear += 1
                # print(currBear)
                return currBear
            else:
                self.currentlyBeating = False
                self.inJibeManeuver = False
                return currBear
        elif(self.beat_dir == "left"):
            if(abs(currBear - self.desBear) >= 0.5):
                currBear -= 1
                # print(currBear, self.desBear)
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
        if(self.beat_dir == "right"):
            if(self.SAK.mod360(currBear) - self.desBear >= 0.5):
                currBear -= 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inTackManeuver = False
                return currBear
        elif(self.beat_dir == "left"):
            if(abs(currBear - self.desBear) >= 0.5):
                currBear += 1
                return currBear
            else:
                self.currentlyBeating = False
                self.inTackManeuver = False
                return currBear

    def is_safe(self, x, y, bearing):
        """
            Call to cartographer to check if the current path
            is safe, to include more functionality later
        """
        self.Map.update_boat_pos(x,y,bearing)
        self.directPathOrient = self.SAK.direction_lookup(self.pos[0], self.pos[1], self.end[0], self.end[1])
        if(time.perf_counter() - self.timer2 > 2):
            self.timer2 = time.perf_counter()
            print(self.directPathOrient)
            print(self.dist)
        if(not self.final_adjust):
            if(self.dist < 100 and not self.in_no_go_range(self.SAK.mod360(self.directPathOrient-10))):
                self.beat_adjust()
                self.desBear = self.SAK.mod360(self.directPathOrient)
                return bearing
            if(not self.Map.check_shoreline() and time.perf_counter() - self.jibeCooldown > 5):
                bearing = self.adjust_path(bearing)
            return bearing
        else:
            return bearing

    def adjust_path(self, bearing):
        """
            Determine how to adjust bearing based
            on the mode of travel in effect
        """
        if(time.perf_counter() - self.timer1 > 1):
            self.timer1 = time.perf_counter()
            if(self.mode == "straight"):
                self.straight_adjust()
            elif(self.mode == "beat"):
                bearing = self.beat_adjust()
                return bearing
        return bearing

    def straight_adjust(self):
        """
            Future implement: Determines how to adjust bearing when a direct path is being followed
            Ideally should return the boat to the original path when object is avoided. could be used
            conditionallt in beat as well in later versions of the code
        """
        raise NotImplemented

    def determine_maneuver(self, dirChange, newHead):
        """
            Determine whether the best choice of changing the direction
            is with a jibe or a tack, later might be better to name this
            something like tack_or_jibe for profesional showings
        """
        if (dirChange == "left"):
            testHead = self.SAK.mod360(newHead - 30)
            if(not self.in_no_go_range(testHead)):
                self.inJibeManeuver = True
        elif (dirChange == "right"):
            testHead = self.SAK.mod360(newHead + 30)
            if(not self.in_no_go_range(testHead)):
                self.inJibeManeuver = True
        else:
            self.inTackManeuver = True

    def beat_adjust(self):
        """
            determine what direction to beat in.
            unsafe right now, does not include jibe vs
            tack
        """
        if(self.beat_dir == "right"):
            self.beat_dir = "left"
            headingChange = self.SAK.mod360(self.NoGoRange.min - 12)
            self.desBear = self.SAK.mod360(self.NoGoRange.min - 12)
            self.determine_maneuver(self.beat_dir, headingChange)
            return headingChange
        elif(self.beat_dir == "left"):
            self.beat_dir = "right"
            headingChange = self.SAK.mod360(self.NoGoRange.max + 12)
            self.desBear = self.SAK.mod360(self.NoGoRange.max + 12)
            self.determine_maneuver(self.beat_dir, headingChange)
            return headingChange

    def is_collison(self):
        """
            *** Simulation specific, remove in mission code ***
            item check if the boat has collided with the shore,
            future implement: boatSim will stop and print
            error message noting an edge case has occured
            This implementation should say what the conditions
            where at the crash to determine what logic needs to be fixed
        """
        return self.Map.check_collison()

    def set_path_type(self):
        """
            Called only on initialization or great change in wind direction
            Determines what type of path, i.e beating, curved, straight, etc
            is best for the current wind conditions to reach the desired waypoint
        """
        # print(self.directPathOrient) # testing statement
        if(self.in_no_go_range(self.directPathOrient)):
            print("beating required")
            self.mode = "beat"
            self.beat_dir = "right"
            return self.SAK.mod360(self.NoGoRange.max + 12)
        else:
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

    def find_shoreline(self):
        """
            Future implement: should include the ability to check ahead
            of the boat some distance and see if a collision would occur
            if a path was taken, needs other functions likely.
            End goal is to test certain possible movements such as jibes
            and potential courses to see if the heading needs additional adjustment
        """
        raise NotImplemented

    def check_dist_to_target(self, posLat, posLon, end):
        self.pos[0], self.pos[1] = posLat, posLon
        self.end[0], self.end[1] = end[0], end[1]
        self.dist = self.SAK.Distance(posLat, posLon, end[0], end[1])
        return self.dist

    def define_speed(self, TWS):
        wa, bsp = self.Way.create_lookup_table(TWS)
        return wa, bsp


# """
#     Main for testing program as standalone while
#     sim is being finished
# """
# def main():
#     CourseBoi = CoursePlotter()
# #
# if __name__ == '__main__':
#     main()
