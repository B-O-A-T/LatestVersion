#Before starting need to pip3 install the following:
    #adafruit_rplidar
    #lidar
import os
from math import cos, sin, pi, floor
from adafruit_rplidar import RPLidar

# Setup the RPLidar
PORT_NAME = '/dev/ttyUSB0'
lidar = RPLidar(None, PORT_NAME)

# used to scale data to fit on the screen
max_distance = 0

#pylint: disable=redefined-outer-name,global-statement
def process_data(data):
    global max_distance
    for angle in range(360):
        distance = data[angle]
        if distance > 0:                  # ignore initially ungathered data points
            max_distance = max([min([5000, distance]), max_distance])
            radians = angle * pi / 180.0
            x = distance * cos(radians)
            y = distance * sin(radians)
            point = (160 + int(x / max_distance * 119), 120 + int(y / max_distance * 119))

#Have the data for each degree of rotation stored
scan_data = [0]*360

try:
    print(lidar.info) #don't really know what this does yet
#iter_scans will start the motor and scanning
    for scan in lidar.iter_scans():
    #iter_scans will result in a list of tuples
    #We want the second and third items in the tuple
    #these are the angle and distance at each angle as floats
        for (_, angle, distance) in scan:
            scan_data[min([359, floor(angle)])] = distance
        process_data(scan_data)

except KeyboardInterrupt: #Press ctrl+c
    print('Stopping.')
lidar.stop()
lidar.disconnect()

#references
# https://learn.adafruit.com/slamtec-rplidar-on-pi?view=all
# https://medium.com/robotics-with-ros/installing-the-rplidar-lidar-sensor-on-the-raspberry-pi-32047cde9588

