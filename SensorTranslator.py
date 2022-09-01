#*******************************************************************************************************************#
#  Project: Prescott Yacht Club - Autonomous Sailing Project
#  File: SensorTranslator.py
#  Author: Lorenzo Kearns
#
#  Purpose: Translate sensor data coming from serial and wrap it into a telemetry object that is readable by all other programs
#*******************************************************************************************************************#
import warnings
import serial
import serial.tools.list_ports
import time

class TelemCommands():
    """
        Object that contains the values for commands to be sent to request
        serial updates for certain sensor values
    """
    def __init__(self):
        self.initHandshake = 0
        self.Lat = 1
        self.Lon = 2
        self.relBearing = 3
        self.windSpeed = 4
        self.apWind = 5

class Telemetry():
    """
        Sensor Object, which collects and maintains all of the telemetry data transfered
        over serial data
    """
    def __init__(self):
        self.telem = TelemCommands()
        self.grandCentral = serial.Serial('COM5', 115200, timeout=1)
        self.handshake_with_arduino()
        self.init_object_telem_variables()

    def init_object_telem_variables(self):
        self.recvGPSLat = self.send_telem_request(self.telem.Lat)
        self.recvGPSLon = self.send_telem_request(self.telem.Lon)
        self.recvVesselBearing = self.send_telem_request(self.telem.relBearing)
        self.recvWindSpeed = self.send_telem_request(self.telem.windSpeed)
        self.recvAparentWindAngle = self.send_telem_request(self.telem.apWind)

    def handshake_with_arduino(self, sleep_time = 1, print_handshake_message = False):
        """
            Make sure connection is established by sending
            and receiving bytes.
        """
        # Close and reopen
        self.grandCentral.close()
        self.grandCentral.open()
        # Chill out while everything gets set
        time.sleep(sleep_time)
        # Set a long timeout to complete handshake
        timeout = self.grandCentral.timeout
        self.grandCentral.timeout = 2
        # Read and discard everything that may be in the input buffer
        _ = self.grandCentral.read_all()
        # Send request to Arduino
        self.grandCentral.write(bytes([self.telem.initHandshake]))
        # Read in what Arduino sent
        handshake_message = self.grandCentral.read_until()
        # Send and receive request again
        self.grandCentral.write(bytes([self.telem.initHandshake]))
        handshake_message = self.grandCentral.read_until()
        # Print the handshake message, if desired
        if print_handshake_message:
            print("Handshake message: " + handshake_message.decode())
        while(True): # Spin until a succesful handshake ir verified
            if(int(handshake_message.decode()) == 689):
                break
        # Reset the timeout
        self.grandCentral.timeout = timeout

    def send_telem_request(self, command):
        """
            Ask grandCentral to send telemetry data
            based on a specified command and return
            the response

        """
        self.grandCentral.write(bytes([command]))
        data = self.grandCentral.read_until()
        data = data.decode()
        return data

# Example call of Telemetry class
BoatTelem = Telemetry()
print(BoatTelem.recvGPSLat)
print(BoatTelem.recvGPSLon)
print(BoatTelem.recvVesselBearing)
print(BoatTelem.recvWindSpeed)
print(BoatTelem.recvAparentWindAngle)

lat = BoatTelem.send_telem_request(BoatTelem.telem.Lat)
lon = BoatTelem.send_telem_request(BoatTelem.telem.Lon)
vesselB = BoatTelem.send_telem_request(BoatTelem.telem.relBearing)
WSPD = BoatTelem.send_telem_request(BoatTelem.telem.windSpeed)
AWA = BoatTelem.send_telem_request(BoatTelem.telem.apWind)
# while True:
