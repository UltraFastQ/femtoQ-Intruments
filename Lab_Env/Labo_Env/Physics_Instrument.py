# Pipython :
import pipython
from pipython import GCSDevice
from pipython import gcscommands
from pipython import datarectools, pitools
# tkinter
from tkinter import messagebox


class LinearStage:
    def __init__(self, parent):
        self.parent = parent
        self.device = None
        self.axes = None

    def connect_identification(self, dev_name=None, dev_ip=None, exp_dependencie=False):
        if not dev_name and not dev_ip:
            return

        dev_name = dev_name.get()
        dev_ip = dev_ip.get()
        if dev_name:
            gcs = GCSDevice(dev_name)
            devices = gcs.EnumerateUSB(mask=dev_name)
            gcs.ConnectUSB(devices[0])
            messagebox.showinfo(title='Physics Instrument', message='Device {} is connected.'.format(dev_name))
            self.device = gcs
        elif dev_ip:
            messagebox.showinfo(title='Physics Intrument', message='This option is not completed')

        self.axes = self.device.axes[0]

        if exp_dependencie:
            experiments = self.parent.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Physics_Linear_Stage')

    def scanning(self, min_pos=None, max_pos=None, iteration=None):
        if not self.device:
            return

        if not max_pos and not min_pos and not iteration:
            return

        iteration = iteration.get()
        for i in range(iteration):
            self.device.MOV(self.axes, max_pos)
            pitools.waitontarget(self.device)
            self.device.MOV(self.axes, min_pos)
            pitools.waitontarget(self.device)

    def go_2position(self, position=None):
        if not self.device or not position:
            return

        position = position.get()
        self.device.MOV(self.axes, position)
        pitools.waitontarget(self.device)

    def change_speed(self, factor=None):
        if not self.device or not factor:
            return
        factor = factor+1
        # The factor is a factor based on the maximum speed ie the minimum is 250 which is 1000/4 (scale is divided by 4
        # there could be more it just need to be changed in both of the program
        # 0 (the minimum) = 250
        # 1 : 500 ...
        self.device.VEL(self.axes, factor*250)

    def calibration(self):
        if not self.device:
            return

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


