import sys
import glob
import serial
import struct

class MonoChrom():
    def __init__():
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
        Factor = 12 #Experimental value
        NbrStep =  Nbr_nm*Factor
        self.Arduino.write(struct.pack('>B', NbrStep))
        self.TotStep += NbrStep

    def Reset(self):
        NbrStep = 0-self.TotStep
        self.Arduino.write(struct.pack('>B', NbrStep))



if __name__ == '__main__':

