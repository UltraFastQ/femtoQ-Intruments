# tkinter
from tkinter import messagebox
from multiprocessing import Process
import threading
import time
import numpy as np


class LinearStage:
    def __init__(self, mainf=None):
        self.mainf = mainf
        self.device = None
        self.axes = None
        self.thread = None

    def connect_identification(self, dev_name=None, dev_ip=None, exp_dependencie=False):
        if not dev_name and not dev_ip:
            return
        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        if (dev_name or dev_ip):
            pass
        else:
            return

        if (dev_name and type(dev_name)!=str):
            dev_name = dev_name.get()
        else:
            pass

        if (dev_ip and type(dev_ip)!=str):
            dev_ip = dev_ip.get()
        else:
            pass

        dev_list = ['C-891', 'C-863.11', 'E-816']
        if dev_name not in dev_list:
            messagebox.showinfo(title='Error', message='This device is not in the device list please make sure it is' +
                                                       'compatible with the pipython software. If so add it to the list'
                                                       + 'at line 20 of the Physics_Instrument.py file')
            return

        if dev_name:
            gcs = GCSDevice(dev_name)

            # Case controller C-891
            if dev_name == dev_list[0]:
                devices = gcs.EnumerateUSB(mask=dev_name)
                if devices == []:
                    messagebox.showinfo(title='Error', message='It seems like there is no devices connected to your computer')
                    return
                gcs.ConnectUSB(devices[0])
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.EAX(self.axes, True)

            # Case controller C-863.12
            elif dev_name == dev_list[1]:
                gcs.ConnectUSB(serialnum = '0019550022')
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.SVO(self.axes, 1)
                
                
            # Case controller E-816
            elif dev_name == dev_list[2]:
                
                comPorts = self.find_active_com_ports()
                
                for ii, comPort in enumerate(comPorts):
                    try:
                        gcs.ConnectRS232(comPort,115200)
                        break
                    except:
                        pass
                self.device = gcs
                self.axes = self.device.axes[0]
                self.device.SVO(self.axes, 1)

            self.calibration(dev_name = dev_name)
            messagebox.showinfo(title='Physics Instrument', message='Device {} is connected.'.format(dev_name))
            self.device = gcs

        elif dev_ip:
            messagebox.showinfo(title='Physics Intrument', message='This option is not completed')

        if exp_dependencie:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Physics_Linear_Stage')


    def scanning(self, min_pos=None, max_pos=None, iteration=None,
		         wtime=None, steps=None):
        if not self.device:
            return

        if not max_pos and not min_pos and not iteration:
            return

        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        iteration = iteration.get()
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        wtime = wtime.get()
        steps = steps.get()

        # Getting the max and min possible value of the device
        maxp = self.device.qTMX(self.axes).get(str(self.axes))
        minp = self.device.qTMN(self.axes).get(str(self.axes))

        # This is a fail safe in case you don't know your device ( I should have done a manual for this...)
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return
        nsteps = int(np.abs(max_pos - min_pos)/steps)
        for i in range(iteration):
            self.device.MOV(self.axes, min_pos)
            pitools.waitontarget(self.device)
            time.sleep(wtime/1000)
            pos = min_pos
            for step in range(nsteps):
                pos += steps
                self.device.MOV(self.axes, pos)
                pitools.waitontarget(self.device)
                time.sleep(wtime/1000)
            if self.device.qPOS(self.axes) != max_pos:
                self.device.MOV(self.axes, max_pos)

    def go_2position(self, position=None):
        if not self.device or not position:
            return
        import pipython.pitools as pitools
        position = position.get()
        self.device.MOV(self.axes, position)
        pitools.waitontarget(self.device)

    def increment_move(self, position=None, increment=None,
                       direction = None):
        if not self.device or not position:
            return
        import pipython.pitools as pitools
        position2 = position.get()
        increment = increment.get()
        if direction == 'left':
            increment = -increment
        else:
            pass
        position2 += increment
        position.set(position2)
        self.device.MOV(self.axes, position2)
        pitools.waitontarget(self.device)


    def change_speed(self, factor=None):
        if not self.device or not factor:
            return
        factor = factor+1
        print(factor)
        # The factor is a factor based on the maximum speed ie the minimum is 250 which is 1000/4 (scale is divided by 4
        # there could be more it just need to be changed in both of the program
        # 0 (the minimum) = 250
        # 1 : 500 ...
        self.device.VEL(self.axes, factor*10)
        print(self.empty_var)

    def set_velocity(self, vel=None):
        if not self.device or not vel:
            return
        vel = vel.get()
        self.device.VEL(self.axes, vel)

    def calibration(self, dev_name):
        if not self.device:
            return
        # Pipython :
        from pipython import GCSDevice

        dev_list = ['C-891', 'C-863.11', 'E-816']

        # Controller C-891
        if dev_name == dev_list[0]:
            self.device.FRF()
            i = 0
            while self.device.IsControllerReady() != 1:
                if i == 0:
                    messagebox.showinfo(message='Wait until the orange light is closed')
                    i += 1
            messagebox.showinfo(message='Device is ready')
            self.device.SVO(self.axes, 1)

        # Controller C-863.12
        if dev_name == dev_list[1]:
            self.device.FRF(self.axes)
            i = 0
            while self.device.IsControllerReady() != 1:
                if i == 0:
                    messagebox.showinfo(message='Calibration in progress')
                    i += 1
            messagebox.showinfo(message='Device is ready')
        
        # Controller E-816
        if dev_name == dev_list[2]:
            messagebox.showinfo(message='Device is ready')

    def find_active_com_ports(self):
        import serial.tools.list_ports
        comlist = serial.tools.list_ports.comports()
        connected = []
        for element in comlist:
            connected.append(element.device)
            connected[-1] = int(connected[-1][-1])
        return connected

#class myThread(threading.Thread):
#    def __init__(self, parent, min_pos, max_pos, iteration):
#        self.parent = parent
#        self.min_pos = min_pos
#        self.max_pos = max_pos
#        self.iteration = iteration
#
#    def run(self):
#        self.parent.scanning(self.min_pos, self.max_pos, self.iteration, )

