from vnpy import *

"""
    The VN 300 has an absolute shit ton of methods, classes and functions 
    at its disposal, feel free to use more advnaced methods if you have any.
    Currently I have added the bare minimum to have a functional system. 
"""
class VN300():
    def __init__(self):
            """
                An object is a programatical represenation 
                of a ... you gussed it object. it is a collection 
                of software which represents a complex system. 
                Lorem ipsum, Lorem ipsum, Lorem ipsum
            """
            self.s = VnSensor()
            self.s.connect('COM6', 115200)

    def get_bearing(self):
        """
            This does as the program asks,
            it deadass gets the bearing.
            if you have to ask more, then I cant 
            help you 
        """
        ypr = self.s.read_yaw_pitch_roll() 
        return ypr.x

    def get_position(self):
        """
            This gets the position of the boat,
            those values are in lat and lon format 
            as our many system updates have outlined 
        """
        gps = self.s.read_ins_state_lla()
        return gps.position.x, gps.position.y
        # print("Position: " + str(gps.position)) # debug