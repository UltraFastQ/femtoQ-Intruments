'''
@author:
'''

import serial
import numpy as np

class OSM2:
    '''Class for OSM2 Spectrometer'''
    def __init__(self, port = None):
        '''
        Parameters
            port : COM port
        '''
        self.port = port
        self.error = 0
        self.error_message = ""
            
    def _spectro_command(self, command):
        try:
            #Try to open a serial connection
            spectro = serial.Serial(port=self.port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout = 1, write_timeout = 1)
        except serial.SerialException:
            self.error = 1
            self.error_message = "Error - Serial port cannot be found or cannot be configured"
            command_reply = b'Port Error\r\n'
        else:
            spectro.write(command)
            command_reply = spectro.readlines()
            spectro.close()
        return command_reply.decode()

    def startSingleExposure(self):
        command = b'Start Single\r\n'
        return self._spectro_command(command)

    def getExposureTime(self):
        command = b'Get Exposuretime\r\n'
        return self._spectro_command(command)

    def getCurrentSpectrum(self):
        command = b'Get Spectrum cur\r\n'
        return self._spectro_command(command)

    def getWavelength(self):
        command = b'Get Lambda\r\n'
        return self._spectro_command(command)

    def getMeasureInfo(self):
        command = b'Get Measureinfo\r\n'
        return self._spectro_command(command)

    def getCalibrationInfo(self):
        command = b'Get Calibrationinfo\r\n'
        return self._spectro_command(command)

    def setHeaderON(self):
        command = b'Set Header on\r\n'
        return self._spectro_command(command)

    def setHeaderOFF(self):
        command = b'Set Header off\r\n'
        return self._spectro_command(command)
    
    def setEchoON(self):
        command = b'Set Echo on\r\n'
        return self._spectro_command(command)

    def setEchoOFF(self):
        command = b'Set Echo off\r\n'
        return self._spectro_command(command)

    def setWavelengthON(self):
        command = b'Set Wavelength-values on\r\n'
        return self._spectro_command(command)

    def setWavelengthOFF(self):
        command = b'Set Wavelength-values off\r\n'
        return self._spectro_command(command)

    def setExposureTime(self, parameter):
        command = b'Set Exposuretime ' + str(parameter).encode() + b'\r\n'
        return self._spectro_command(command)

    def setRangeStart(self, parameter):
        command = b'Set Range Start ' + str(parameter).encode() + b'\r\n'
        return self._spectro_command(command)
    
    def setRangeEnd(self, parameter):
        command = b'Set Range End ' + str(parameter).encode() + b'\r\n'
        return self._spectro_command(command)

    def setRangeIncrement(self, parameter):
        command = b'Set Range Increment ' + str(parameter).encode() + b'\r\n'
        return self._spectro_command(command)

    def mAcquireSpectrum(self,low_wl,top_wl,wl_res,exp_time):
        self.setEchoOFF()
        self.setHeaderOFF()
        self.setWavelengthOFF()
        self.setRangeStart(low_wl)
        self.setRangeEnd(top_wl)
        self.setRangeIncrement(wl_res)
        self.setExposureTime(exp_time)
        self.startSingleExposure()
        reply = self.getWavelength()
        wavelength = np.asarray(reply[0:-1], dtype = np.float32)
        reply = self.getCurrentSpectrum()
        intensity = np.asarray(reply[0:-1], dtype = np.float32)
        return wavelength, intensity