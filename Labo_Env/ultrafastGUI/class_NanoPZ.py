'''
@author:
'''

import serial

class NanoPZ:
    '''Class for NanoPZ positionner'''
    def __init__(self, port = None, ctrl_no = 0):
        '''
        Parameters
            port : COM port
            ctrl_no : Controller number (0 to 255)
        '''
        self.port = port
        self.ctrl_no = ctrl_no
        self.error = 0
        self.error_message = ""

    def _piezo_get(self, command):
        get_reply = b''
        try:
            #Try to open a serial connection
            piezo = serial.Serial(port=self.port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout = 1, write_timeout = 1)
        except serial.SerialException:
            self.error = 1
            self.error_message = "Error - Serial port cannot be found or cannot be configured"
            get_reply = b'Port Error\r\n'
        else:
            command_str = str(self.ctrl_no) + command + '?\r\n'
            piezo.write(command_str.encode())
            get_reply = piezo.readline()
            piezo.close()
        return get_reply.decode().rstrip()

    def _piezo_set(self, command):
        set_reply = b''
        try:
            #Try to open a serial connection
            piezo = serial.Serial(port=self.port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout = 1, write_timeout = 1)
        except serial.SerialException:
            self.error = 1
            self.error_message = "Error - Serial port cannot be found or cannot be configured"
            set_reply = b'Port Error\r\n'
        else:
            command_str = str(self.ctrl_no) + command + '\r\n'
            piezo.write(command_str.encode())
            piezo.close()
            set_reply = command_str.encode()
        return set_reply.decode().rstrip()

    def getHardwareID(self):
        command = 'ID'
        return self._piezo_get(command)

    def getHardwareStatus(self):
        command = 'PH'
        return self._piezo_get(command)

    def getControllerStatus(self):
        command = 'TS'
        return self._piezo_get(command)

    def getErrorCode(self):
        command = 'TE'
        return self._piezo_get(command)

    def getCurrentPosition(self):
        command = 'TP'
        return self._piezo_get(command)

    def setPositionRelative(self, parameter):
        command = 'PR' + str(parameter)
        return self._piezo_set(command)

    def setZeroPosition(self):
        command = 'OR'
        return self._piezo_set(command)
    
    def setAbsolutePosition(self, parameter):
        command = 'PR'+str(parameter-float(self.getCurrentPosition()[5:]))
        return self._piezo_set(command)

    def setMotorON(self):
        command = 'MO'
        return self._piezo_set(command)

    def setMotorOFF(self):
        command = 'MF'
        return self._piezo_set(command)

    def StopMotion(self):
        command = 'ST'
        return self._piezo_set(command)
