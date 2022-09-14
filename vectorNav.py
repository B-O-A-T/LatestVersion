from vnpy import *

s = VnSensor()
s.connect('COM6', 115200)
s.read_model_number()
s.read_yaw_pitch_roll()
