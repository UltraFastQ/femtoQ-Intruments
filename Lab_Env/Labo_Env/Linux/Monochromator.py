import glob
import struct
import time
from tkinter import messagebox
import serial


class MonoChrom:
    def __init__(self, parent=None):
        self.Port = None
        self.arduino = None
        self.tot_step = 0
        self.side = ''
        self.done = True
        self.current_position = 800  #Current position in nanometer
        self.parent = parent

    def serial_ports(self):
        import sys
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

    def connect(self, exp_dependencie=False):
        if not self.Port:
            return
        self.arduino = serial.Serial(self.Port[0], 9600)
        if exp_dependencie:
            experiments = self.parent.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Spectrometer')

    def roll_dial(self, Nbr_nm):
        if not self.arduino or not self.done:
            return
        # Number of nanometer as to be a even index for the motor
        if (self.side == '') or (self.side == 'r'):
            self.correction('f')
            time.sleep(1)
        self.side = 'f'
        self.done = False
        Factor = 2  # Experimental values
        nbr_step = Nbr_nm*Factor
        nbr_step = round(nbr_step)
        modulo = nbr_step%255
        step_left = nbr_step
        step_2take = 255
        self.arduino.write(b'f')
        while step_left != modulo:
            self.arduino.write(struct.pack('>B', step_2take))
            step_left -= step_2take
        self.arduino.write(struct.pack('>B', step_left))
        self.tot_step += nbr_step
        self.done = True

    def reset(self):
        if not self.arduino or not self.done:
            return
        if (self.side == '') or (self.side == 'f'):
            self.correction('r')
            time.sleep(1)
        self.side = 'r'
        self.done = False
        nbr_step = self.tot_step
        nbr_step = round(nbr_step)
        modulo = nbr_step % 255
        step_left = nbr_step
        step_2take = 255
        if self.tot_step == 0:
            self.done = True
            return
        self.arduino.write(b'r')
        while step_left != modulo:
            self.arduino.write(struct.pack('>B', step_2take))
            step_left -= step_2take
        self.arduino.write(struct.pack('>B', step_left))
        self.tot_step = 0
        self.done = True

    def correction(self, side):
        if not self.arduino:
            return
        correction = 6  # Correction for the motor flip
        nbr_step = correction
        modulo = nbr_step % 255
        step_left = nbr_step
        step_2take = 255
        self.arduino.write(b'C')
        time.sleep(0.1)
        if side == 'r':
            self.arduino.write(b'r')
        elif side == 'f':
            self.arduino.write(b'f')

        while step_left != modulo:
            self.arduino.write(struct.pack('>B', step_2take))
            step_left -= step_2take
        self.arduino.write(struct.pack('>B', step_left))

    def calibrate(self, spectro, variable):
        if not spectro:
            messagebox.showinfo(title='Error', message='There is no spectrometer connected.')
            return
        if not self.arduino:
            messagebox.showinfo(title='Error', message='The monochromator is not connected.')

        response = messagebox.askyesno(title='Visibility', message='Is the spectrum visible by the spectro?')
        if response == 'yes':
            pass
        elif response == 'no':
            side = messagebox.askyesno(title='Side', message='Is the dial under 400?')
            if side == 'yes':
                self.roll_dial(200)
            elif side == 'no':
                self.roll_dial(-200)

        intensities = spectro.intensities()
        wavelengths = spectro.wavelengths()
        max_intensity = max(intensities)
        positions = [i for i, j in enumerate(intensities) if j == max_intensity]
        self.current_position = wavelengths[positions[0]]
        while not (self.current_position < 800+0.5 and self.current_position > 800-0.5):
            dif_nm = 800 - self.current_position
            self.roll_dial(dif_nm)
            intensities = spectro.intensities()
            wavelengths = spectro.wavelengths()
            max_intensity = max(intensities)
            positions = [i for i, j in enumerate(intensities) if j == max_intensity]
            self.current_position = wavelengths[positions[0]]

        self.tot_step = 0
        variable.set(self.current_position)