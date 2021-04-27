# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 19:26:38 2016
@author: Smoothie & hejtmy
"""
import threading
import serial
import serial.threaded
import sys
import glob
from enum import Enum

# Important because of rts settings in the serial port
class ArduinoModel(Enum):
    Leonardo = 1
    Uno = 2

class Neuroduino:
    def __init__(self, port = "COM5", baudrate = 9600, timeout = 0.1, model = ArduinoModel.Leonardo, want_threading = False):
        self.arduinoConnection = serial.Serial()
        self.arduinoConnection.port = port
        self.arduinoConnection.timeout = timeout
        self.arduinoConnection.baudrate = baudrate
        self.model = model
        self._threading = want_threading

    # Public API
    def connect(self):
        if self.is_open():
            return True
        connection = self._try_ports()
        if connection:
            self.arduinoConnection = connection
            self._initialise_connection()

    def is_open(self):
        return self.arduinoConnection.isOpen()

    def disconnect(self):
        if self.is_open():
            self._send_message("DISCONNECT")
            if self._threading:
                self._stop_threading()
            self.arduinoConnection.close()

    def reset(self):
        if self.is_open():
            self.disconnect()
            self.connect()

    '''
    Slightly modified readline that converts the byte data to utf-8 format
    '''
    def readline(self, connection = None):
        if connection is None:
            connection = self.arduinoConnection
        if not connection.isOpen():
            return None
        try:
            line = connection.readline()
            return line.decode("utf-8")
        except Exception as ex:
            print(ex)

    # Experimental functions
    def blink(self):
        if self.is_open():
            self._send_message("BLINK")

    def send_pulse_up(self, num = 1):
        if not self.is_open():
            return None
        if(num > 15):
            raise ValueError("Value cannot be larger than 15")
        msg = f'PULSE+{i:04b}'
        self._send_message(msg)

    def send_pulse_down(self):
        if self.is_open():
            self._send_message("PULSE-")

    def photoresistor_start(self):
        if self.is_open():
            self._send_message("PHOTO+")

    def photoresistor_stop(self):
        if self.is_open():
            self._send_message("PHOTO-")

    def arduino_done(self):
        return None

    def sensor_activated(self, line):
        return None

    # PRIVATE CONNECTION PART
    '''
    Firstly the last known port is tried, if there is any.
    If it doesnt connect, the first 10 COM ports are mapped and tested one by one
    Testing includes ability to connect as well as send and receive specific messages, e. _try_connect
    '''
    def _try_ports(self):
        if self.is_open():
            self.disconnect()
        if self.arduinoConnection.port != "":
            connection = self._try_connect(self.arduinoConnection.port)
            if connection:
                return connection
        ports = serial_ports(32)  # returns a list of open ports depending on the platform
        for port in ports:
            try:
                connection = self._try_connect(port)
                if connection:
                    return connection
            except Exception as ex:
                print(f'Port {port} failed, continuing')
        return False

    '''
    Returns either None or functional connection

    Creates a new serial connection and tries to open it.
    If the connection does not open, function returns false
    If the connection opens but its not Arduino with running code(does not respond) it returns none
    If the connection opens and its Arduino on hte other side, the connection is returned
    '''
    def _try_connect(self, port):
        connection = serial.Serial()
        connection.port = port
        connection.rts = True
        connection.dtr = (self.model == ArduinoModel.Leonardo)
        connection.timeout = self.arduinoConnection.timeout
        try:
            connection.open()
        except Exception as ex:
            print("Couldn't connect to device at " + port)
            print(ex)
            return
        if self._test_connection(connection):
            return connection
        else:
            return

    '''
    Returns True/False depending on reception of specific message

    Sends 'WHO' byte message to the serial connection and waits for the response
    If there is ARDUINO by message in the response, function returns TRUE, otherwise False
    '''
    def _test_connection(self, connection):
        self._serial_send_message(connection, 'WHO')
        line = self.readline(connection)
        if "NEURODUINO" in line:
            return True
        else:
            return False

    def _initialise_connection(self):
        if self._threading:
            self._start_threading()
        self._send_prepared()

    '''
    Threading functionality - still occasionally buggy
    '''
    def _start_threading(self):
        self.read_thread = threading.Thread(target = self._check_incoming, daemon = True)
        self.read_thread.start()

    def _stop_threading(self):
        self.read_thread = None

    def _check_incoming(self):
        while self.is_open():
            line = self.readline()
            if line is not None:
                if "DONE" in line:
                    self.arduino_done()
                if "SENSOR" in line:
                    self.sensor_activated(line)

    def _send_prepared(self):
        self._send_message("DONE")

    def _send_message(self, message):
        self._serial_send_message(self.arduinoConnection, message)

    @staticmethod
    def _serial_send_message(connection, message):
        byte_message = (message + "!").encode("utf-8")
        connection.write(byte_message)

def serial_ports(up_to = 256):
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(up_to)]
        print(ports)
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
