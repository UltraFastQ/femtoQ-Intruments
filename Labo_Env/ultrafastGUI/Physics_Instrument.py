"Python Pipython wrapper for the GUI interface"
from tkinter import messagebox
from multiprocessing import Process
import time
import numpy as np
import serial
import SMC100CC
from math import floor


class LinearStage:
    """
    This class is used to wrap the pipython package from Physick Instrument to
    utilize their function and adapt it to a GUI interface. It allows a
    uniformatization of the different pipython devices. In a close futur
    this class will need subclasses that are specific to a given stage. With
    there own calibration and initialisation.

    Attributes:
        mainf : This is a tkinter object that represent the MainFrame if
        it exist when sent it is used to update the experiment window when
        used within the MainFrame.
        device : This is the pipython GCSDevice object that represent the
        Physick Intrument device.
        axes : This is the axis number that you can move you device with.
        It need an update to allow many axis stages that would allow dual
        axis mouvement.
        dev_name : This is a string representing the Device.

    """

    
    
    
    def __init__(self, mainf=None):
        """
        Constructor for the LinearStage class.

        Parameters:
            mainf : MainFrame object to be only passed if you have the
            Mainwindow and you want to update the experiment window.
        """
        self.mainf = mainf
        self.device = None
        self.axes = None
        self.dev_name = None

    def connect_identification(self, dev_name=None, dev_ip=None, exp_dependencie=False):
        """
        This function utilize the pipython package to connect the stage by
        scanning the available device plugged by usb or IP. If the usb mask
        exist among your devices it will connect it.

        Parameters :
            dev_name/dev_ip : This is a mask that will be used to disinguish
            your device from others connected to your computer. It is either
            your device name or the IP that it is linked to.
            exp_dependencie: This is a boolean value that tells the user
            interface if the user wants to update the experiement
            window.
        """
        if not dev_name and not dev_ip:
            return
        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        # Determine the type of input was entered in tkinter entry box
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
        # Looking if the devices has adapted function
        dev_list = ['C-891', 'C-863.11', 'E-816','SMC100']
        if dev_name not in dev_list:
            messagebox.showinfo(title='Error', message='This device is not in the device list please make sure it is' +
                                                       'compatible with the pipython software. If so add it to the list'
                                                       + 'at line 20 of the Physics_Instrument.py file')
            return
        # Follow the right procedure assigned to a specific device
        if dev_name:

            if dev_name==dev_list[3]:
                # Case controller is SMC100CC
                self.dev_name='SMC100'
                self.device=SMC100CC.SMC100(1,'COM5')
                self.initialize()
            else:
                gcs = GCSDevice(dev_name)

                self.dev_name = dev_name
    
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
    
                # Case controller C-863.11
                elif dev_name == dev_list[1]:
                    gcs.ConnectUSB(serialnum = '0195500433')
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

        elif dev_ip:
            messagebox.showinfo(title='Physics Intrument', message='This option is not completed')

        # Verifying if the device needs to be sent to experiment window
        if self.mainf:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Physics_Linear_Stage')



    def initialize(self):
        if self.dev_name=='SMC100':
            if (not self.device):
                return

            self.device.reset_and_configure()
            self.device.home()
        
        else:
            return


    def scanning(self, min_pos=None, max_pos=None, iteration=None,
		         wtime=None, steps=None):
        """
        This is a function to do a simple scan n number of time from a min to
        a maximum position. This is not working well as a function
        because it blocks the gui from interacting sometimes. It can be use as
        a guideline and works well in that regard.

        Parameters:
            min_pos: This is a tkinter DoubleVar that correspond to the min
            position.
            max_pos: This is a tkinter DoubleVar that correspond to the max
            position.
            iteration: This is a tkinter IntVar that correspond to the number
            of iteration of interest.
            wtime: This is a tkinter DoubleVar that correspond to the waiting
            time @ a position 'x'.
            steps: This is a tkinter DoubleVar that correspond to the step
            size that your device should do.
        """
        if not self.device:
            return

        if not max_pos and not min_pos and not iteration:
            return

        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        # Getting variables
        iteration = iteration.get()
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        wtime = wtime.get()
        steps = steps.get()

        # Getting the max and min possible value of the device
        maxp = self.device.qTMX(self.axes).get(str(self.axes))
        minp = self.device.qTMN(self.axes).get(str(self.axes))

        # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return
        # Defines the number of steps needed to do the full range
        nsteps = int(np.abs(max_pos - min_pos)/steps)
        for i in range(iteration):
            self.device.MOV(self.axes, min_pos)
            pitools.waitontarget(self.device)
            # Time given by user is in ms
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
        """
        This function allows the user to move the stage that is connected to
        you computer on the axis taken of self.axis.

        Parameters:
            position: This is the position you want to order your stage to
            go to.
        """
        
        if self.dev_name=='SMC100':
            if (not self.device) or (position is None):
                return
            self.device.move_absolute_mm(position)
        
        else:
            import pipython.pitools as pitools
    
            if (not self.device) or (position is None):
                return
            import pipython.pitools as pitools
    
            try:
                position = position.get()
            except:
                pass
            if self.dev_name == 'E-816':
                # Convert [-250,250] um input position to MOV() units for piezo
                position = (position + 250)/5 # -> Convert to [0,100] range
    
                correctedMax = 15.1608
    
                position = position * correctedMax / 100 # -> Convert to effective values for damaged piezo
    
    
            self.device.MOV(self.axes, position)
            pitools.waitontarget(self.device)

    def get_position(self):
        """
        This function allows the user to get the exact position of the stage
        that is returned with device precision.
        """
        if self.dev_name=='SMC100':
            position=self.device.get_position_mm()
            if (not self.device) or (position is None):
                return
        else:
            position = self.device.qPOS(self.axes)[self.axes]
            if (not self.device) or (position is None):
                return
    
    
            if self.dev_name == 'E-816':
                # Convert qPOS() values to [-250,250] um range for piezo
    
                correctedMax = 15.1608
    
                position = position * 100 / correctedMax # -> Convert to [0,100] range
    
    
                position = position*5 - 250 # -> Convert to [-250,250] range

        return position


    def increment_move(self, position=None, increment=None,
                       direction = None):
        """
        This is a function to move by incrementation from the GUI it is
        based on the actual position and the increment given by the GUI.

        Parameters:
            position: This is the current position of the device.
            increment: This is the increment that is sent everytime you
            click on one of the arrow.
            direction: This is either positive or negative depending on
            the side of the arrow you are clicking.
        """
        if self.dev_name=='SMC100':
            if not self.device or not position:
                return
            if direction == 'left':
                increment = -increment
            self.device.move_relative_mm(increment)


        else:
            if not self.device or not position:
                return
            # The orientation of the device is based on positive and negative of
            # the 891 stage. Maybe definition is different for other stage.
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
        """
        This is a way to change your device speed using the scroll bar.

        Parameters:
            factor: This is the scrollbar postion that discretize the
            speed of a device.
        """
        if not self.device or not factor:
            return
        factor = factor+1
        # The factor is a factor based on the maximum speed ie the minimum is 250 which is 1000/4 (scale is divided by 4
        # there could be more it just need to be changed in both of the program
        # 0 (the minimum) = 250
        # 1 : 500 ...
        self.device.VEL(self.axes, factor*10)

    def set_velocity(self, vel=None):
        """
        This function allows to change the velocity of your device while
        with precision.

        Parameters:
            vel: This is a tkinter DoubleVar that indicate the new speed of
            the device.
        """
        if not self.device or not vel:
            return
        vel = vel.get()

        if self.dev_name =='SMC100':
            if vel<0 or vel>20:
                return
            self.device.set_speed(vel)

        elif self.dev_name == 'E-816':
            pass
        else:
            self.device.VEL(self.axes, vel)


    def calibration(self, dev_name):
        """
        This function allows the user to calibrate the device that was
        connected. It is called right after the connection or can be called
        afterward.

        Parameter:
            dev_name: This is the string of your device to allow the right
            calibration process.
        """
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

        # Controller C-863.11
        if dev_name == dev_list[1]:
            self.device.FRF()
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
        """
        I invite the person that made this function to comment on it.
        """
        import serial.tools.list_ports
        comlist = serial.tools.list_ports.comports()
        connected = []
        for element in comlist:
            connected.append(element.device)
            connected[-1] = int(connected[-1][-1])
        return connected







