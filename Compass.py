#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: Compass.py
#  Author: Lorenzo Kearns
#
#  Purpose: Program holds compass class which is used to maintain the bearing of the ship and true wind direction
#            in relation to compass north as well as functions to translate from apparent values to true values.
#*******************************************************************************************************************#
class Compass():
    def __init__(self, initialBearing, trueWindInitial):
        self.vesselBearing = initialBearing
        self.windRelNorth = trueWindInitial

    def boat_frame_to_iniertial(self):
        raise NotImplemented
