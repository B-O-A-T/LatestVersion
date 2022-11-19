from vnpy import *

class VN300():
    def __init__(self):
            """
                Define initial conditions when class is called
            """
            self.s = VnSensor()
            self.s.connect('COM6', 115200)

    def get_bearing(self):
        ypr = self.s.read_yaw_pitch_roll()
        return ypr.x

    def get_position(self):
        gps = self.s.read_ins_state_lla()
        return gps.position.x, gps.position.y
        print("Position: " + str(gps.position))