###################################################################
#                   WhiteLight Interferometer Program             #
#                   Created by : Nicolas Perron                   #
#                   For : Ultrafast and Quantum
#!/usr/bin/python3
# -*- coding: utf-8 -*-

#Importing package:
# Tkinter
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
#Sub_Programs
import Sub_Programs as SP
from Sub_Programs import WL_backend as backend
#Pathlib
from pathlib import Path
#Zurich Instrumente Librairies:
import zhinst.utils as utils
import zhinst.Save_Zi as Save_Zi
# Mathplotlib:
import matplotlib.animation as animation
#Os python package:
import os
#Font Size
LARGE_FONT = ("Arial", 12)
NORM_FONT = ("Arial", 10)
SMALL_FONT = ("Arial", 8)
# Creating the main window with the different backend classes
class White_Light_Inteferometer(tk.Tk):

    def __init__(self, *args, **kwargs):
        # Creating Frame
        tk.Tk.__init__(self, *args, **kwargs)
        # Getting the working directory
        Dir = Path.cwd()
        # Creating the self object for the PI and ZI devices
        self.PI_Data = None
        self.Zi_Data = None
        # Frame Initialisation
        Ima = tk.PhotoImage(file = Dir/'FMQ3.gif')
        tk.Tk.wm_title(self, "White Light Interferometer V1.0")
        tk.Tk.wm_iconphoto(self, '-default' ,Ima)
        # Frame switching function:
        def Switch_Frame(lst, Box, rw, clm):
            Current = Box.get()
            for element in lst:
                lst[element].grid_forget()

            for element in lst:
                if element == Current:
                    lst[element].configure(labelwidget = Box)
                    lst[element].grid(row = rw, column = clm,
                            padx = 2, pady = 2,sticky = 'nsew')
                else: pass


        #Variable for screen dimension & variables
        txtvar = tk.StringVar()
        global width
        global height

        #Needs to be ajustable(modification to come)
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        #Initialisation of different elements
        Mainframe = ttk.Frame(self, padding = (6,6,6,6))
        SubFrame = ttk.Frame(Mainframe, padding = (6,6,6,6))
        ConFrame = ttk.Frame(Mainframe, padding = (6,6,6,6))
        # Graphic Combobox
        GCBox = ttk.Combobox(Mainframe, textvariable = '',
                state = 'readonly')
        GCBox.grid(row = 0, column = 1,sticky = 'nw')
        GCBox['value'] = ('SCOPE','PLOTTER','BOXCAR','PLOTTER CONFIG.')
        self.GraphBox = backend.Graphic( Mainframe, GCBox,
                self.Zi_Data)
        # Configuration Combobox
        CCBox = ttk.Combobox(ConFrame, textvariable = '',
                state = 'readonly')
        CCBox.grid(row = 0, column = 0,sticky = 'nw')
        CCBox['value'] = ('PI Module Connection','ZI Module connection')
        CCBox.current(0)
        # Setting Combobox
        SCBox = ttk.Combobox(SubFrame, textvariable = '',
                state = 'readonly')
        SCBox.grid(row = 0, column = 0,sticky = 'nw')
        SCBox['value'] = ('PI Module Settings','ZI Module Settings')
        SCBox.current(0)
        # Those frame are all based on the classes on the backend
        # File_Interaction Frame
        self.File_Dialog = backend.File_interaction(ConFrame,
                "File interaction")
        # Zurich Instrument Connection Frame
        self.ZiFrame = backend.Zi_Connection_Method(ConFrame,CCBox)
        # Physic Instrument Connection Frame
        self.frame = backend.PI_Connection_Method(ConFrame,
                CCBox)
        # Physic Instrument Settings Frame
        self.PI_Control = backend.PI_control(SubFrame,SCBox)
        # Zurich Instrument Settings Frame
        self.ZI_Control = backend.Zi_settings(SubFrame, SCBox)
        # These two list are used for the Switch Frame method
        # with the combobox initialised before
        Flist1 = {'PI Module Connection': self.frame,
                'ZI Module connection' : self.ZiFrame}
        Flist2 = {'PI Module Settings': self.PI_Control,
                'ZI Module Settings': self.ZI_Control}
        # Binding interaction with the combobox
        CCBox.bind("<<ComboboxSelected>>",
            lambda x : Switch_Frame(Flist1,CCBox,0,0))
        SCBox.bind("<<ComboboxSelected>>",
            lambda x : Switch_Frame(Flist2,SCBox,0,0))
        Switch_Frame(Flist1,CCBox,0,0)
        Switch_Frame(Flist2,SCBox,0,0)
        # This next section is putting the different element in
        # the main window
        #Mainframe configuration
        Mainframe.grid(row = 0, column = 0)
        ConFrame.grid(row = 0, column = 0, sticky = 'nw')
        SubFrame.grid(row = 1, column = 0,columnspan = 2, sticky = 'nsew')
        #GraphBox configuration
        self.GraphBox.grid(row = 0, column = 1, padx = 5, pady = 5)
        #File location/reading configuration
        self.File_Dialog.grid(row = 1, column = 0, padx = 2, pady = 2, sticky = 'w')
        # Binding File_Interaction frame to different methods
        self.File_Dialog.Start.bind('<Button-1>',
                    lambda x : self.Start(self.File_Dialog.DirVar.get()))

        self.File_Dialog.OpBut.bind('<Button-1>',
                    lambda : self.Load_Setting(
                        self.File_Dialog.DirVar, self.PI_Data,
                        self.Zi_Data))

        self.File_Dialog.SvBut.bind('<Button-1>',
                    lambda : self.Save_Setting(
                        File_Dialog.DirVar,
                        File_Dialog.File_InDir, self.PI_Data,
                        self.Zi_Data))

        self.File_Dialog.Stop.bind('<Button-1>',
                    lambda : self.Stop_Measurement(
                        self.PI_Data,
                        self.Zi_Data))
    # This function is starting a full simulation for the white light interferometer
    def Start(self, Dir):
        PI_Data = self.PI_Data
        Zi_Data = self.Zi_Data
        # Verification if all the elements are all there
        Exp_Name = self.File_Dialog.Expcbb_var.get()
        if Exp_Name == 'Etienne':
            Mesure = backend.Measure(Folder = Dir, ZI_DATA = Zi_Data)
            Mesure.Etienne()

        else:
            if Zi_Data == None:
                messagebox.showinfo(icon = 'warning', title = 'Status', message = 'Some parameters aren''t set up')
                return
            if PI_DATA == None:
                messagebox.showinfo(icon = 'warning', title = 'Status', message = 'Some parameters aren''t set up')
                return
            if Zi_Data['DAQ'] == None:
                messagebox.showinfo(icon = 'warning', title = 'Status', message = 'Some parameters aren''t set up')
                return
            # unsubscribing path to receive only the right data
            Zi_Data['DAQ'].unsubscribe('*')
            y = messagebox.askyesno( icon = 'question', title = 'Settings', message = 'Is all your parameters'+
                    'set up for the experiment')
            if y == 'yes':
                x = messagebox.askyesno( icon = 'warning', title = 'Monochromator', message = 'Is the monochromator'+
                        'set to 400 on the dial. If not close the 12V Power source and reset the dial to 400')
                if x == 'yes':
                    messagebox.showinfo( title = 'Experiment', message = 'The experiment will now start.'+
                            ' Do not interfere with the devices.')
                    #Do the mesurement for the whitelight
                    Mesure = backend.Measure(Dir, PI_DATA, Zi_DATA)
                    Mesure.Do(self.File_Dialog.Expcbb_var.get())
                    ### Do Plot for the measurements

    # Create files for saved settings
    def Save_Setting(self, Folder, PI_Data, ZI_Data):

        def Save(Dir, ZI_Data, PI_Data):
            utils.save_settings( ZI_Data['DAQ'],
                    ZI_Data['Device_id'].get(),
                    Dir.get()+os.sep+'_zi_settings.xml')
            f = open(Dir.get()+os.sep+'_pi_settings.txt', 'w+')
            for k in PI_Data.keys():
                f.write( k + '\t:\t' + str(PI_Data[k].get()))
            f.close()

        if PI_Data or ZI_Data is None:
            messabox.showinfo(icon = 'error', title = 'WARNING',
                    message = 'One of the device is not connected')
        elif Dir.get() == '':
            messabox.showinfo(icon = 'error', title = 'WARNING',
                    message = 'Please Choose a directory')
        else:
            Save( Folder, ZI_Data, PI_Data)
            messabox.showinfo( title = 'Information',
                    message = 'Settings as been saved to the'+
                    'desiered folder.')
    # Methods to load all the settings from a old experiment
    def Load_Setting(self, Folder, PI_Data, ZI_Data):

        def Load(Dir, ZI_Data, PI_Data):
            utils.load_settings( ZI_Data['DAQ'],
                    ZI_Data['Device_id'].get(),
                    Dir.get()+os.sep+'_zi_settings.xml')
            f = open(Dir.get()+os.sep+'_pi_settings.txt', 'r')
            for line in f:
                words = line.split()
                for keys in PI_Data.keys():
                    if keys == words(0):
                        PI_Data[keys].set(words(2))
            f.close()

        if PI_Data or ZI_Data is None:
            messabox.showinfo(icon = 'error', title = 'WARNING',
                    message = 'One of the device is not connected')
        elif Dir.get() == '':
            messabox.showinfo(icon = 'error', title = 'WARNING',
                    message = 'Please choose a directory')
        else:
            Load( Folder, ZI_Data, PI_Data)
            messabox.showinfo( title = 'Information',
                    message = 'Settings as been saved to the'+
                    'desiered folder.')
    # Not configured button to stop an expriment
    def Stop_Measurement(self, ):
        print('stop')

    # Animate graph calls a method of the GraphBox classes
    def Animate_Graph(self, time):
        self.GraphBox.Animate_Graph(self.GraphBox.Actual_Graph, self.ZI_Control.Zi_Setting_List, self.ZI_Control.Ready)
        self.after(time, self.Animate_Graph, 100)
# Refresh functions for the information ( Should be modified)
def Refresh(app, Frame, receiver):
    if Frame.connected==False:
        app.after(1000, Refresh, app, Frame, receiver)
    else:
        if Frame == app.frame:
            receiver.Devices = app.frame.Devices_connected
            app.PI_Data = app.PI_Control.Show_device()
        elif Frame == app.ZiFrame:
            receiver.Zi_Setting_List['DAQ'] = app.ZiFrame.DAQ
            receiver.Zi_Setting_List['Device_id'] = app.ZiFrame.device_id
            receiver.Zi_Setting_List['Prop'] = app.ZiFrame.proprieties
            app.Zi_Data = app.ZI_Control.Zi_Setting_List
            app.ZiFrame.First = False
# Lauch the app
app = White_Light_Inteferometer()
# Bind some interaction for the main frame
app.frame.CbmBox.bind("<<ComboboxSelected>>",app.frame.Meth_show)

app.frame.CButton.bind('<Button-1>', lambda x : Refresh(app, app.frame,
    app.PI_Control ))
app.ZiFrame.CButton.bind('<Button-1>', lambda x : Refresh(app, app.ZiFrame, app.ZI_Control))
# Place the window in the center of the screen
app.geometry("+{}+{}".format(int(width/5),int(height/5)))
#NOTE : This line might cause an error in the future
# P.S. : The Future is NOW :(
app.after(1000, app.Animate_Graph, 1000)
app.mainloop()

