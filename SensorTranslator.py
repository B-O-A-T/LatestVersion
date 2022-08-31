#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: boatSim.py
#  Author: Lorenzo Kearns
#
#  Purpose: Translate sensor data coming from serial and wrap it into a telemetry object that is readable by all other programs
#*******************************************************************************************************************#
import warnings
import serial
import serial.tools.list_ports

class Telemetry():
    """
        Sensor Object, which collects and maintains all of the telemetry data transfered
        over serial data
    """
    def __init__(self):
        self.recvGPSLat = 0
        self.recvGPSLon = 0
        self.joshHasATinyDict = {"GPS Lat": 1}

    def find_my_duino(self):
        """
            scan the ports and look for a viable Arduino or Arduino like device to connect
        """
        arduino_ports = [
            p.device
            for p in serial.tools.list_ports.comports()
            if 'Arduino' in p.description  # may need tweaking to match new arduinos
        ]
        if not arduino_ports:
            raise IOError("No Arduino found")
        if len(arduino_ports) > 1:
            warnings.warn('Multiple Arduinos found - using the first')
        self.grandCentral = serial.Serial(arduino_ports[0], 115200, timeout=1)

    def handshake_with_arduino(self):
