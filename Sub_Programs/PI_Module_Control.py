#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pipython import GCSDevice  # Load PI python Libraries
import pipython.pitools as pi     # Provide some sample function to ease our work
from pipython import datarectools # Tools provided by Pi to record data on the module


#class PIModule(pipython): # Class linked to the White_Light_Interferometer Program
#    """This class defines all those point :
#        - The connection method
#        - The Read/Write File
#        """
#    def __init__(self, Method, File_Name, Dev_Name):
#        self.ConMethod = Method
#        self.File_Name = File_Name
#        self.Dev_Name = Dev_Name
#
#    def ConnectionMethod(self, Device):
#
#        with GCSDevice (Device) as gcs:
#            gcs.InterfaceSetupDlg()
#            print ('Connected: {}'.format(gcs.qIDN().strip()))
#
#    def File_location():
#
#
#    def Read():
#
#
#    def Write():





# Initialisation of the PI module
with GCSDevice ('C-891') as gcs:
    #Method 1 : If there is many devices and want to select one
#    devices = EnumerateUSB(mask = 'C-891')
#    for i, device in enumerate(devices):
#        print('{} - {}'.format(i,devices))
#    item = int(input('select devices to connect:'))
#    gcs.ConnectUSBByDescription(devices[item])
#    Method 2 : Connect via this interface ( There is a way to do it with the TCPIP )
    gcs.InterfaceSetupDlg() # Adding a string into this command will allow to recall the registery used on the next use
#    gcs.ConnectUSB ('Serial_Number') #Serial Number of the Module
#    Connected device
    print ('Connected: {}'.format(gcs.qIDN().strip()))

# Data Recorder for the Pi Module
#drec = datarectools.Datarecorder(gcs)


#gcs.SVO ('A',1)            # Turn on servo control of axis "A"
#gcs.MOV ('A',3.142)        # Command axis "A" to position 3.142
#position = gcs.qPOS ('A')  # Query current position of axis "A"


