import sys
import glob
import serial
import struct
import time

class MonoChrom():
    def __init__(self):
        self.Port = None
        self.Arduino = None
        self.TotStep = 0

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
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

        self.Port = result
        print(self.Port)

    def Connect(self):
        self.Arduino = serial.Serial(self.Port[0], 9600)

    def RollDial(self, Nbr_nm):
        Factor = 1 #Experimental values
        NbrStep =  Nbr_nm*Factor
        Modulo = NbrStep%255
        Step_Left = NbrStep
        StepTaken = 255
        self.Arduino.write(b'f')
        while (Step_Left != Modulo):
            print('hello')
            self.Arduino.write(struct.pack('>B', StepTaken))
            Step_Left -= StepTaken
        self.Arduino.write(struct.pack('>B',Step_Left))
        self.TotStep += NbrStep

    def Reset(self):
        NbrStep =  self.TotStep
        Modulo = NbrStep%255
        Step_Left = NbrStep
        StepTaken = 255
        self.Arduino.write(b'r')
        while (Step_Left != Modulo):
            self.Arduino.write(struct.pack('>B', StepTaken))
            Step_Left -= StepTaken
        self.Arduino.write(struct.pack('>B',Step_Left))
        self.TotStep = 0



