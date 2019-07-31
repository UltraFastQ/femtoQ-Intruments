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

        dev_name = dev_name.get()
        dev_ip = dev_ip.get()
        dev_list = ['C-891', 'C-863']
        if dev_name not in dev_list:
            messagebox.showinfo(title='Error', message='This device is not in the device list please make sure it is' +
                                                       'compatible with the pipython software. If so add it to the list'
                                                       + 'at line 20 of the Physics_Instrument.py file')
            return

        if dev_name:
            gcs = GCSDevice(dev_name)
            devices = gcs.EnumerateUSB(mask=dev_name)
            if devices == []:
                messagebox.showinfo(title='Error', message='It seems like there is no devices connected to your computer')
                return
            gcs.ConnectUSB(devices[0])
            messagebox.showinfo(title='Physics Instrument', message='Device {} is connected.'.format(dev_name))
            self.device = gcs
        elif dev_ip:
            messagebox.showinfo(title='Physics Intrument', message='This option is not completed')

        self.axes = self.device.axes[0]
        self.device.EAX(self.axes, True)
        if exp_dependencie:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Physics_Linear_Stage')
    

    def scanning(self, min_pos=None, max_pos=None, iteration=None):
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
        # Getting the max and min possible value of the device
        max = self.device.qTMX(self.axes).get(str(self.axes))
        min = self.device.qTMN(self.axes).get(str(self.axes))

        # This is a fail safe in case you don't know your device ( I should have done a manual for this...)
        if not(min_pos >= min and max_pos >= min and min_pos <= max and max_pos <= max):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

        for i in range(iteration):
            self.device.MOV(self.axes, max_pos)
            pitools.waitontarget(self.device)
            self.device.MOV(self.axes, min_pos)
            pitools.waitontarget(self.device)
    
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
        
    def calibration(self):
        if not self.device:
            return
        # Pipython :
        from pipython import GCSDevice

        self.device.FRF()
        i = 0
        while self.device.IsControllerReady() != 1:
            if i == 0:
                messagebox.showinfo(message='Wait until the orange light is closed')
                i += 1
        if self.device.IsControllerReady() == 1:
            messagebox.showinfo(message='Device is ready')
            self.device.SVO(self.axes, 1)
        else:
            messagebox.showinfo(message='Calibration failed')


class myThread(threading.Thread):
    def __init__(self, parent, min_pos, max_pos, iteration):
        self.parent = parent
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.iteration = iteration

    def run(self):
        self.parent.scanning(self.min_pos, self.max_pos, self.iteration)

