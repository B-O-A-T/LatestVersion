#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: Cartographer.py
#  Author: Lorenzo Kearns
#  Versions:
#   version: 0.1 4/18/2022 - Initial Program Creation
#
#  Purpose: Define dynamic map which holds boundaries and use this to determine safe operating angles
#*******************************************************************************************************************#
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry import MultiPoint
from shapely.geometry import MultiLineString
from utilities import Tools
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import os
import time
from shapely.ops import nearest_points
from glob import *

class Cartographer():
    """
        Class is callable by other programs and runs by
        using inner functions included below
    """
    def __init__(self, shoreThresh):
        """
            Define initial conditions when class is called
        """
        self.SAK = Tools() # SAK is shorthand for Swiss Army Knife which the Tools class essentially is
        self.boatWidth = self.SAK.ft_to_latlon(2)
        self.boatLength = self.SAK.ft_to_latlon(7)
        self.safetyThresh = self.SAK.ft_to_latlon(shoreThresh) # defines the distance in feet that is safe
        LakeEdgesTemp = pd.read_csv('OutputBoundaries.csv') # read the definition of the lake from a csv
        LakeEdgesTemp = np.array(LakeEdgesTemp) # convert csv values into a numpy array
        self.LakeEdges = self.create_polygon_from_csv(LakeEdgesTemp) # create a polygon object that represents the lake
        self.listOfLakeEdgesLon, self.listOfLakeEdgesLat = self.create_polygon_from_csv(LakeEdgesTemp, get_list =  True)
        self.update_boat_pos(34.515501, -112.384901, 0)
        self.timer1 = time.perf_counter()
        self.shoreDir = BEHIND


    def create_polygon_from_csv(self, temp_container, get_list = False):
            """
                Generate a new polygon object based on the given points
                passed into the function, can be used for any size and
                input need, i.e. works for rocks, boats, land etc
            """
            self.bound = []
            boundaryArrayLat = temp_container[:,1]
            boundaryArrayLon = temp_container[:,2]
            if (get_list == True):
                return boundaryArrayLon, boundaryArrayLat
            self.boundaryArrayLon = np.array(boundaryArrayLon)
            self.boundaryArrayLat = np.array(boundaryArrayLat)
            coordTuple = np.array((self.boundaryArrayLon,self.boundaryArrayLat)).T
            return Polygon(coordTuple)

    def update_boat_pos(self, x, y, trueHeading):
        """
            pass the current position of the boat
            and create a polygon object to
            represent it
        """
        boat_coords =  [
                  self.SAK.rotate(x, y - self.boatLength/2, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x - self.boatWidth/8, y - self.boatLength/2.1, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x - self.boatWidth/4, y - self.boatLength/3.42, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x - self.boatWidth/2.5, y, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x - self.boatWidth/2.9, y + self.boatLength/4.60  , self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x, y + self.boatLength/2, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x + self.boatWidth/2.9, y + self.boatLength/4.60  , self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x + self.boatWidth/2.5, y, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x + self.boatWidth/4, y - self.boatLength/3.42, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x + self.boatWidth/8, y - self.boatLength/2.1, self.SAK.mod360(trueHeading), x, y),
                  self.SAK.rotate(x, y - self.boatLength/2, self.SAK.mod360(trueHeading), x, y)]
        boatObj = Polygon(boat_coords)
        self.boatPos = boatObj

    def check_shoreline(self):
        """
            Check how close the boat is to,
            the shoreline
        """
        distShore = self.boatPos.exterior.distance(self.LakeEdges.exterior)
        self.centerX, self.centerY = self.boatPos.centroid.x, self.boatPos.centroid.y
        # print(distShore)
        if(distShore - self.safetyThresh < 0):
            # print("Warning, shore collision imminent!")
            p1, p2 = nearest_points(self.boatPos.exterior, self.LakeEdges.exterior)
            if(p2.x > self.centerX):
                self.shoreDir = RIGHT
            elif(p2.x < self.centerX):
                self.shoreDir = LEFT
            elif(p2.y > self.centerY):
                self.shoreDir = FORWARD
            return False
        else:
            return True

    def get_object_direction(self):
        return self.shoreDir

    def check_collison(self):
        """
            Basis for CoursePlotters is_collision()
            function, Needs adjustment either here or in CoursePlotter
            Checks if the boat polygon has collided with the lake polygon
            by seeing if distance is equal to zero
        """
        distShore = self.boatPos.exterior.distance(self.LakeEdges.exterior)
        if (distShore - self.safetyThresh == 0):
            return True
        else:
            return False
