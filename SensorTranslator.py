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
        self.windSpeed = 1
        self.apWind = 2
        self.moveRudder = 3;
        self.winchSail = 4;

class Telemetry():
    """
        Sensor Object, which collects and maintains all of the telemetry data transfered
        over serial data
    """
    def __init__(self):
        self.telem = TelemCommands()
        self.grandCentral = serial.Serial('COM5', 115200, timeout=1)

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

    def winch_sail(self, desiredAngle):
        self.grandCentral.write(bytes([self.winchSail]))
        handshakeResponse = self.grandCentral.read_until()
        if(int(handshakeResponse.decode()) == 689):
            self.grandCentral.write(bytes([self.desiredAngle]))