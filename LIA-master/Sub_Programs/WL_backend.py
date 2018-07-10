###################################################################
#           WhiteLight Interferometer Program Backend             #
#           Created by : Nicolas Perron                           #
#           For : Ulrafast and Quantum Laboratory                 #
#!/usr/bin/python3
# -*- coding: utf-8 -*-
###################################################################
#Package :
#   tkinter :
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
# Pipython :
import pipython
from pipython import GCSDevice
from pipython import gcscommands
from pipython import datarectools, pitools
# Matplotlib :
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
# Pathlib :
from pathlib import Path
from pathlib import PurePath
#Zurich Instruments
import zhinst.utils as utils
import zhinst.ziPython as ziPython
#####
class PI_Connection_Method(ttk.Labelframe):
    def __init__(self, parent, name):
        ttk.Labelframe.__init__(self, parent)
        ####
        ttk.Labelframe.configure(self, labelwidget = name)
        ####
        self.connected = False
        self.varUSB = tk.IntVar()
        self.varRS = tk.IntVar()
        self.varIP1 = tk.IntVar()
        self.varIP2 = tk.IntVar()
        self.Devices_connected = {}
        self.Container = ttk.Frame(self)
        self.Container.grid(row = 2, column = 0,rowspan = 2,
                columnspan = 2)
        self.InFrame = ttk.Frame(self)
        self.InFrame.grid(row = 6,column =0)
        self.INList = {}
        ####
        USBVar = tk.StringVar()
        IPVar = tk.StringVar()
        DevNameLabel = ttk.Label(self.Container, text =
                "Device Name")
        KeyLoglabel = ttk.Label(self.Container, text =
                "Login Key")
        DevName = ttk.Entry(self.Container, width = 20)
        KeyLog = ttk.Entry(self.Container, width = 20)
        RS_232 = ttk.Checkbutton(self.Container, text = "RS-232",
                command = lambda:self.Input_show(self.INList,1), variable = self.varRS)
        USButton = ttk.Checkbutton(self.Container, text = "USB",
                command = lambda:self.Input_show(self.INList,0), variable = self.varUSB)
        TCP_IP_Button1 = ttk.Checkbutton(self.Container, text
                = "TCT/IP : adress", command = lambda:self.Input_show(self.INList,2),
                variable = self.varIP1)
        TCP_IP_Button2 = ttk.Checkbutton(self.Container, text
                = "TCP/IP: Description", command = lambda:self.Input_show(self.INList,3),
                variable = self.varIP2)
        USBLabel = ttk.Label(self.Container, text = "USB")
        TCPIPLabel = ttk.Label(self.Container, text = "IP adress")
        EnumUSB = ttk.Entry(self.Container, textvariable = USBVar)
        EnumTCPIP = ttk.Entry(self.Container, textvariable = IPVar)

        SNLabel = ttk.Label(self.InFrame, text = 'Serial number: ')
        SNInput = ttk.Entry(self.InFrame, width = 20)

        RS_232Lb1 = ttk.Label(self.InFrame, text = 'COM port: ')
        RS_232In1 = ttk.Entry(self.InFrame, width = 20)
        RS_232Lb2 = ttk.Label(self.InFrame, text = 'Baudrate: ')
        RS_232In2 = ttk.Entry(self.InFrame, width = 20)

        IP2Label = ttk.Label(self.InFrame, text = 'Description: ')
        IP2Input = ttk.Entry(self.InFrame, width = 20)

        IP1Lb1 = ttk.Label(self.InFrame, text = 'IP address: ')
        IP1In1 = ttk.Entry(self.InFrame, width = 20)
        IP1Lb2 = ttk.Label(self.InFrame, text = 'IP port: ')
        IP1In2 = ttk.Entry(self.InFrame, width = 20)

        USBLst = [SNLabel,SNInput]
        RS_232Lst = [RS_232Lb1,RS_232In1,RS_232Lb2,RS_232In2]
        IP1Lst = [IP2Label,IP2Input]
        IP2Lst = [IP1Lb1,IP1In1,IP1Lb2,IP1In2]


        n = 0
        for T in (USBLst,RS_232Lst,IP1Lst,IP2Lst):
            self.INList[n] = T
            n+=1

        ####
        self.txtDialog = "This method allows you to connect a single devices via the embeded graphical interface from GCS DLL. The first fiel is requiered. The second allows you to recall data and settings from this key."
        self.Dialog = [DevNameLabel,KeyLoglabel,DevName,KeyLog]
        self.Interface = [RS_232,USButton,TCP_IP_Button1,
                TCP_IP_Button2]
        self.DevIdentification = [USBLabel,TCPIPLabel,
                EnumUSB, EnumTCPIP]
        self.DaisyChain = [RS_232,USButton,TCP_IP_Button1,
                TCP_IP_Button2]
        self.txtInterface = "This method allows you to connect a single devices via characteristics of the device. Here is a quick decription of every characteristics: \nCOM port : Number of the COM port devices is connected to. \nBaudrate : Connexion speed of the device/transfer rate of the data. \nIP adress: IP adress associated with the device. \nIP port : IP port the device is connected to. \nDescription: Description of the device you want to connect."
        self.txtDevIdentification = "This method allows you to connect a single device via a USB/IP scanning method. Inputs needs to either be a part of the name of the device you are looking for or a part of its IP adress."
        self.txtDaisyChain = "This method allows you to connect multiple devices via an interface. When connected each devices will receive a different ID to be controlled in the program."
        self.Description = {}
        self.Method = {}
        self.CButton = tk.Button(self, text = "Connect Device(s)",
                command = lambda : self.Read_Connection())
        ####
        i = 0
        for T in (self.txtDialog,self.txtInterface
                ,self.txtDevIdentification,self.txtDaisyChain):
            text = T
            self.Description[i] = text
            i += 1

        j = 0
        for M in (self.Dialog,self.Interface,self.DevIdentification,
               self.DaisyChain):
            self.Method[j] = M
            j += 1

        ####
        self.TextBox = tk.Text(self, wrap = 'word', width = 50,
                height = 8)
        self.TextBox.grid(row = 1, column = 0, padx = 5, pady = 2)


        ####
        self.CbmBox = ttk.Combobox(self, textvariable = "",
                state = "readonly")
        self.CbmBox['values'] = ('Dialog','Interface'
                ,'Identification','Daisy chain')
        self.CbmBox.current(2)
        self.CbmBox.grid(row = 0, column = 0, sticky = "nw",
                padx = 6, pady = 2)
        self.CbmBox.bind("<<ComboboxSelected>>",
                self.Meth_show("w.e value"))
        ####
        self.CButton.grid(row = 8, column = 0, columnspan = 2
                ,sticky ="we", padx = 2, pady = 2)


    def Input_show(self,Lst,value):
        place = Lst[value]
        rw = 0
        clm = 0
        self.Reset(value,Lst)
        for show in place:
            show.grid( row = rw , column = clm , padx = 5,
                    pady = 5, sticky = "w")
            if clm == 0:
                clm += 1
            else:
                clm = 0
                rw += 1
        j = 0
        for M in (self.varUSB,self.varRS,self.varIP1,self.varIP2):
            if j == value:
                j+=1
            else:
                M.set(0)
                j += 1

    def Meth_show(self,value):

        a = self.CbmBox.current()
        self.TextBox.configure(state = 'normal')
        self.TextBox.delete('1.0', tk.END)
        self.TextBox.insert('1.0', chars =
                self.Description[a])
        self.TextBox.configure(state = 'disable')
        place = self.Method[a]
        rw = 2
        clm = 0
        self.Container.grid(row =2, column = 0,
                columnspan = 2, rowspan = 4)
        self.Reset(a,self.Method)
        for show in place:
            show.grid( row = rw , column = clm , padx = 2,
                    pady = 2, sticky = "w")
            if clm == 0:
                clm += 1
            else:
                clm = 0
                rw += 1

    def Reset(self,value,lst):
        i = 0
        for place in lst:
            if value != i:
                for erease in lst[i]:
                    erease.grid_forget()
            i += 1


    def Read_Connection(self):
        print("Connections has been read")
        value = self.CbmBox.current()
        Entry = {}
        State = {}
        j = 0
        for M in self.Method[value]:
            if type(M) is tk.ttk.Entry:
                if M.get() != '':
                    Entry[j] =  M.get()
                print(Entry)
                j += 1
            elif type(M) is tk.ttk.Checkbutton:
                for S in M.state():
                    if S == 'selected':
                        State[j] = M.cget("text")
                        print(State)
                        j += 1
        if bool(Entry):
            if value == 0:
                print("Call Dialog 1 or 2 args")
                self.Connect_device(value,Entry)
            elif value == 2:
                if len(Entry) == 1:
                    print("Call Identification USB or IP")
                    self.Connect_device(value,Entry)
                else: print("Error too many input")
        elif bool(State):
            if len(State) == 1:
                print("Connection has to be established")
                self.Connect_device(value,State)
            else: print("Error message")
        else: print("No Input")

    def Connect_device(self,value,read):
        print("Devices Connecting")

        def Dialog_connect(M_read):

            print("Dialog")

            gcs = GCSDevice(M_read[0])
            if len(M_read) == 1:
                gcs.InterfaceSetupDlg()
            else: gcs.InterfaceSetupDlg(M_read[1])
            messagebox.showinfo(message ='Device: {}\n connected'.format(gcs.qIDN().strip()) ,title = 'Connection Succesfull')
            self.Devices_connected[M_read[0]] = gcs

        def Interface_connect(M_read):
            print("Interface")
            print("Not ready yet")

        def Identification_connect(M_read):
            if list(M_read.keys())[0] == 0:
                gcs = GCSDevice('C-891')
                devices = gcs.EnumerateUSB(mask = M_read[0])
                for i, device in enumerate(devices):
                    print('{} - {}'.format(i, device))
                item = int(input('Select device to connect: '))
                gcs.ConnectUSB(devices[item])
                messagebox.showinfo(message ='Device: {}\nconnected'.format(gcs.qIDN().strip()) , title = 'Connection Succesfull')
                self.Devices_connected[M_read[0]] = gcs
                self.connected = True
                gcs.SVO('1',0)

            elif list(M_read.keys())[0] == 1:

                gcs = GCSDevice(M_read[0])
                devices = gcs.EnumerateTCPIPDevices(mask = M_read[0])
                for i, device in enumerate(devices):
                    print('{} - {}'.format(i, device))
                item = int(input('Select device to connect:'))
                gcs.ConnectTCPIPByDescription(devices[item])
                messagebox.showinfo(message ='Device: {}\n connected'.format(gcs.qIDN().strip()) ,title = 'Connection Succesfull')
                self.Devices_connected[M_read[0]] = gcs

        def Daisy_connect(M_read):
            print("Daisy Chain")
            print("Not ready yet")

        Option = {0 : Dialog_connect,
                1: Interface_connect,
                2: Identification_connect,
                3: Daisy_connect}
        Option[value](read)
###########
class Zi_Connection_Method(ttk.Labelframe):
    def __init__(self, parent, name):
        ttk.Labelframe.__init__(self, parent)
        ####
        ttk.Labelframe.configure(self, labelwidget = name)
        self.connected = False
        self.DAQ = ()
        self.device = ''
        self.proprieties = {}

        def Call_device(TxtVariable):
            Called_id = TxtVariable.get()
            # Make it variables
            api_level = 6
            dev_type = 'UHF'
            (daq , dev , prop) = utils.create_api_session(
                    Called_id, api_level, dev_type)
            if not utils.api_server_version_check(daq):
                messagebox.showinfo(icon = 'info',title='DAQ Version',
                        message = 'ziDataServer not up to date')
            else :
                messagebox.showinfo(icon = 'info',title='DAQ Version',
                        message = 'ziDataServer is up to date')
            if self.DAQ != ():
                self.connected = True
                self.DAQ = daq
                self.device_id = dev
                self.proprieties = prop
                messagebox.showinfo( message = 'Zurich Instrument'+
                'device is connected', title = 'Information')



        DevVar = tk.StringVar()
        DevVar.set('dev2318')
        DevL = tk.Label(self, text ='Zurich Instrumente Device:\n Default : dev2318 ')
        DevBox = tk.Entry(self, width = 10, textvariable = DevVar)
        self.CButton = ttk.Button(self, text ='Find Connected Device',
                command = lambda : Call_device(DevVar))
        DevL.grid(row = 0, column = 0, sticky = 'nw', padx = 2,
                pady = 2)
        DevBox.grid(row = 0, column = 1, sticky = 'nw', padx = 2,
                pady = 2)
        self.CButton.grid(row = 1, column = 0, sticky = 'n',
                columnspan = 2, padx = 2, pady = 2)

###########
class Graphic(tk.Canvas):
    def __init__(self,parent,width,height):

        tk.Canvas.__init__(self,parent)
        tk.Canvas.configure(self, width = width, height = height)
        tk.Canvas.configure(self, background = "yellow")

class File_interaction(ttk.Labelframe):
    def __init__(self, parent, text):
        self.File_InDir = []
        ttk.Labelframe.__init__(self, parent)
        ttk.Labelframe.configure(self, text = text)
        self.Stop = tk.Button(self, text = 'Stop')
        DirLabel = tk.Label(self, text = "File Directiory:")
        self.DirVar = tk.StringVar()
        DirField = ttk.Entry(self, textvariable = self.DirVar,
                width = 20)
        DirBut = ttk.Button(self, text = "Choose Directory",
                command = lambda :
                self.Dir_Interaction(self.DirVar,self.File_InDir))
        self.OpBut = ttk.Button(self, text = "Load Settings")
        self.SvBut = ttk.Button(self, text = "Save Settings")
        self.Start = ttk.Button(self, text = 'Start')
        DirLabel.grid( row = 0, column = 0, sticky = 'nw', padx = 2,
                pady = 2)
        DirField.grid( row = 1, column = 0, sticky = 'ns', padx = 2,
                pady = 2)
        DirBut.grid(row = 0, column = 1, rowspan = 2, sticky = "ns",
                padx = 2, pady = 2)
        self.OpBut.grid(row = 2, column = 0, columnspan = 1,
                sticky = 'ew', padx = 2, pady = 2)
        self.SvBut.grid(row = 2, column = 1, columnspan = 1,
                sticky = 'ew', padx = 2, pady = 2)
        self.Start.grid(row = 6, column = 0, columnspan = 1,
                sticky = 'ew', padx = 2, pady = 2)
        self.Stop.grid(row = 6, column = 1, columnspan = 1,
                sticky = 'ew', padx = 2, pady = 2)

    def Dir_Interaction(self,Var,List):
        Anw =  messagebox.askyesnocancel(message = 'Do you want to load a previous session', icon = 'question')
        if Anw == True:
            Q = messagebox.showinfo(title = 'CHOOSE FOLDER',
                    icon = 'info', message = 'In the next window choose the folder containing the old experiment')

            if Q == 'ok':
                self.Write_Folder(Var)

        elif Anw == False:
            FCreated = False
            NFWindow = tk.Tk()
            NFWindow.wm_title('Folder Pop-up')
            NFWindow.wm_geometry('275x135+500+500')
            Q = ttk.Label(NFWindow,
                    text = 'Name of the new folder:', font =('Arial',12) )
            QA = tk.StringVar()
            QE = ttk.Entry(NFWindow,textvariable = QA,
                    width = 12)
            QB = ttk.Button(NFWindow, text = 'Enter',
                    command = lambda  :
                    self.Write_Folder(Var,QE.get(),NFWindow))
            Info = ttk.Label(NFWindow, text = 'When you have entered the new name\nclick enter. You will then be asked to\nchoose the directory where you want\nto put the new folder.')
            Q.pack(padx = 2, pady = 2)
            QE.pack(padx = 2, pady = 2)
            QB.pack(padx = 2, pady = 2)
            Info.pack(padx =2, pady =2)
        else: pass

    def Write_Folder(self,Var,NFolder = '',Popup = None):
        def Create_Folder(Folder):
            p = Path(Folder)
            p.mkdir()

        if Popup != None:
            Popup.destroy()

        parent = filedialog.askdirectory()

        if NFolder != '':
            Folder = Path(parent) / NFolder
            Create_Folder(Folder)
            parent = Folder
            Var.set(Folder)
        else: Var.set(parent)


        self.File_InDir = [ item for item in parent.iterdir() if
                parent.is_file()]


class PI_control(ttk.Labelframe):
    def __init__(self, parent, text):
        ttk.Labelframe.__init__(self, parent)
        ttk.Labelframe.configure(self, labelwidget = text)
        ####
        self.Devices = {'Test':0}
        self.No_dev = tk.Label(self,
                text = "There is no devices connected")
        if not self.Devices:
            self.No_dev.grid(row = 0, column = 0, sticky = "nesw")
        else:
            self.No_dev.grid_forget()
            self.Show_device()
    #Take the devices connected in the other window
    ####
    def Show_device(self):
        i = 0
        rw = 0
        clm = 0
        PI_Data = None
        self.Reset(self.No_dev)
        Deva = self.Devices
        for dev in Deva:
            Labelframe = ttk.Labelframe(self,
                    text = dev)
            Labelframe.grid(row = rw, column = clm,
                    padx = 2, pady = 2)
            item = Deva[dev]
            PI_Data = self.Create_commands(Labelframe,item)
            i += 1
            clm += 1
            if i > 1:
                rw += 1
                clm = 0
        return PI_Data

    def Create_commands(self,parent,Device):
        if Device != 0:
            Axe1 = Device.axes[0]
            if Device.HasEAX() is True:
                Device.EAX(Axe1,True)
                self.Calibration(Device, Axe1)
            else:print('heeeelo')
        NbrIte = tk.IntVar()
        NbrIte.set(1)
        MPos = tk.DoubleVar()
        mPos = tk.DoubleVar()
        if Device != 0:
            MPos.set(Device.qTMX(Axe1))
            mPos.set(Device.qTMN(Axe1))
        LNbrIte = tk.Label(parent, text = 'Nomber of iteration')
        LMPos = tk.Label(parent, text = "Max: Position")
        LmPos = tk.Label(parent, text = "Min: Position")
        NbrIteE = tk.Entry(parent, width = 8,
                textvariable = NbrIte)
        MPosE = ttk.Entry(parent, width = 8, textvariable = MPos)
        mPosE = ttk.Entry(parent, width = 8, textvariable = mPos)
        NbrSmp = tk.DoubleVar()
        ETA = tk.DoubleVar()
        LNbrSmp = tk.Label(parent, text = "Number of Sample")
        LETA = tk.Label(parent, text = "Time for a measurement")
        NbrSmpE = ttk.Entry(parent, width = 8, textvariable = NbrSmp)
        ETAE = ttk.Entry(parent, width = 8, textvariable = ETA)
        SpScaleVar = {1:'Precise',2:'Medium',3:'Fast',4:'U-Fast'}
        SpScale = tk.Scale(parent, orient='horizontal', from_=1,
                to = 4, command = lambda x:
                self.See_val(SpScale,SpScaleVar),
                label = 'Device Velocity: ', variable = SpScaleVar,
                showvalue = False, length = 150)
        Strt = ttk.Button(parent, text = 'Start', command =
                lambda : self.Do_Mesure(MPos,mPos,SpScale,NbrIte,
                    NbrSmp,ETA,Device,Axe1))
        Cal = ttk.Button(parent,text = 'Calibration',
                command = lambda : self.Calibration(Device,Axe1))
        LMPos.grid(row = 0, column = 0, sticky = "w",
                padx = 2, pady = 2)
        LmPos.grid(row = 2, column = 0, sticky = "w",
                padx = 2, pady = 2)
        MPosE.grid(row = 1, column = 0, sticky = "w",
                padx = 2, pady = 2)
        mPosE.grid(row = 3, column = 0, sticky = "w",
                padx = 2, pady = 2)
        LNbrSmp.grid(row = 0, column = 1, sticky = "w",
                padx = 2, pady = 2)
        LETA.grid(row = 2, column = 1, sticky = "w",
                padx = 2, pady = 2)
        NbrSmpE.grid(row = 1, column = 1, sticky = "w",
                padx = 2, pady = 2)
        ETAE.grid(row = 3, column = 1, sticky = "w",
                padx = 2, pady = 2)
        Cal.grid(row = 5, column = 0, columnspan = 2,
                sticky = "we", padx = 2, pady = 2)
        SpScale.grid(row = 0, column = 2, padx = 2, pady = 2,
                sticky = 'w')
        Strt.grid(row = 5, column = 2, padx = 2, pady = 2,
                sticky ='ew')
        LNbrIte.grid(row = 1, column = 2, padx = 2, pady = 2,
                sticky = 'w')
        NbrIteE.grid(row = 2, column = 2, padx = 2, pady = 2,
                sticky = 'w')
        Speed = 250*int(SpScale.get()+1)
        try: Axe1
        except UnboundLocalError:
            Axe1 = ''
        else: pass

        List_PI = {'MaxPos': MPos,
                'MinPos': mPos,
                'Velocity': Speed,
                'NbrSample': NbrSmp,
                'NbrIteration': NbrIte,
                'Time': ETA,
                'Device_id': Device,
                'Axes': Axe1 }

        return List_PI


    def See_val(self,Objet,Var):
        Objet.configure(label = 'Device Velocity: {}'.format(Var[int(Objet.get())]))

    def Actu_POS(self,Dev,Axe,Max,Min):
        Dev.MOV(Axe,Max)
        pitools.waitontarget(Device)
        Dev.MOV(Axe,Min)
        pitools.waitontarget(Device)


    def Actu_Sp(self,Dev,Axe,Speed):
        Dev.VEL(Axe,Speed)


    def Calibration(self,Dev,Axe):
        Dev.FRF()
        i = 0
        while Dev.IsControllerReady() != 1:
            if i == 0:
                messagebox.showinfo(message = 'Wait until the orange light is closed')
                i +=1
        if Dev.IsControllerReady() == 1:
            messagebox.showinfo(message = 'Device is ready')
            Dev.SVO(Axe, 1)
        else:
            messagebox.showinfo(message = 'Calibration failed')

    def Do_Mesure(self,Max,Min,Vel,Ite,Sample,T,Device,Axe):
        MaxPos = int(Max.get())
        MinPos = int(Min.get())
        VelSet = 250*(int(Vel.get())+1)
        T.set(((MaxPos-MinPos)/VelSet))
        self.Actu_Sp(Device,Axe,VelSet)
        i = 0
        while i < Ite.get():
            self.Actu_POS(Device,Axe,MaxPos,MinPos)
        messagebox.showinfo('Device : Finished ')


    def Reset(self,Device):
        Device.grid_forget()


class Zi_settings(ttk.Labelframe):
    def __init__(self, parent, text, DAQ = None, Device = None,
            Prop = None):

        ttk.Labelframe.__init__(self, parent)
        ttk.Labelframe.configure(self, labelwidget = text)
        self.Zi_Setting_List = {}
        List_Opt = []

        Demod_Var = tk.IntVar()
        L_Demod = tk.Label(self, text = 'Demodulator: ')
        D_Port_SpinB = tk.Spinbox(self, from_ = 0, to = 7 , width = 2,
                textvariable = Demod_Var)

        Output_Var = tk.IntVar()
        Output_Channel = tk.Label(self, text = 'Output channel: ')
        O_Port_SpinB = tk.Spinbox(self, from_ = 0, to = 3 , width = 2,
                textvariable = Output_Var)

        Output_Rate_Var = tk.DoubleVar()
        Output_Rate = tk.Entry(self, width = 4,
                textvariable = Output_Rate_Var)
        L_Output_Rate = tk.Label(self, text = 'Data Output Rate'+
                '[Smp/s]: ')

        Input_Var = tk.IntVar()
        I_Port_SpinB = tk.Spinbox(self, from_ = 0, to = 1 , width = 2,
                textvariable = Input_Var)
        L_Input_Channel = tk.Label(self, text = 'Input channel: ')

        OSC_Var = tk.IntVar()
        OSC_SpinB = tk.Spinbox(self, from_ = 0, to = 1 , width = 2,
                textvariable = OSC_Var)
        L_Oscillator = tk.Label(self, text = 'Oscillator: ')

        OSC_F_Var = tk.IntVar()
        OSC_F_SpinB = tk.Entry(self, width = 4,
                textvariable = OSC_F_Var)
        L_OSC_F = tk.Label(self, text = 'Oscillator frequency'+
                ' [Hz]: ')

        Gain_Var = tk.DoubleVar()
        E_Gain = tk.Entry(self, width = 4, textvariable = Gain_Var)
        L_Gain = tk.Label(self, text = 'Input Gain: ')

        Phi_Var = tk.DoubleVar()
        E_Phi = tk.Entry(self, width = 4, textvariable = Phi_Var)
        L_Phi = tk.Label(self, text = 'Phase shitf [deg]: ')

        Trig_Val = tk.DoubleVar()
        Trig_state = tk.StringVar()
        Trig = ttk.Checkbutton(self, text = 'Trigger',
                variable = Trig_state, onvalue = 'Enabled',
                offvalue = 'Disabled')

        L_Trig = tk.Label(self, text = 'Trigger Frequency [Hz]: ')
        Trig_Entry = tk.Entry(self, width = 4,textvariable = Trig_Val,
                state = 'disable')
        T_Port_SpinB = tk.Spinbox(self, from_ = 0, to = 1 , width = 2)

        Ohm50_state = tk.StringVar()
        Ohm50 = ttk.Checkbutton(self, text = '50 Ohm',
                variable = Ohm50_state, onvalue = 'Enabled',
                offvalue = 'Disabled')

        AC_state = tk.StringVar()
        AC = ttk.Checkbutton(self, text = 'AC',
                variable = AC_state, onvalue = 'Enabled',
                offvalue = 'Disabled')

        Harm_Var = tk.IntVar()
        Harm = tk.Spinbox(self, from_ = 0 , to = 10, width = 2,
                textvariable = Harm_Var)
        L_Harm = tk.Label(self, text = 'Selected Harmonic: ')

        Input_Scale_Var = tk.DoubleVar()
        Input_Scale = tk.Entry(self,  width = 4,
                textvariable = Input_Scale_Var)
        L_Input_Scale= tk.Label(self, text = 'Input Scaling [X V'+
                '/V]: ')

        Out_Scale_Var = tk.DoubleVar()
        Out_Scale = tk.Entry(self,  width = 4,
                textvariable = Input_Scale_Var)
        L_Out_Scale= tk.Label(self, text = 'Output Scaling [X V'+
                '/V]: ')

        Out_Preoffset_Var = tk.DoubleVar()
        Out_Preoffset = tk.Entry(self,  width = 4,
                textvariable = Out_Preoffset_Var)
        L_Out_Preoffset= tk.Label(self,text = 'Output Preoffset [V]:')

        Out_Offset_Var = tk.DoubleVar()
        Offset = tk.Entry(self,  width = 4,
                textvariable = Out_Offset_Var)
        L_Out_Offset= tk.Label(self, text = 'Output Offset [V]: ')

        Order_Var = tk.IntVar()
        Order_SpinB = tk.Spinbox(self, from_ = 0 , to = 10, width = 2,
                textvariable = Harm_Var)
        L_Order = tk.Label(self, text = 'Low-Pass Filer Order: ')

        DB_Var = tk.DoubleVar()
        DB = tk.Entry(self,  width = 4,
                textvariable = Out_Offset_Var)
        L_DB = tk.Label(self, text = 'BW 3 dB: ')


        Item_List = [ L_Demod, D_Port_SpinB , AC , Ohm50,
                L_Input_Channel, I_Port_SpinB,
                Output_Channel, O_Port_SpinB,
                L_Output_Rate, Output_Rate,
                L_Harm, Harm, L_Gain, E_Gain,
                L_Input_Scale, Input_Scale,
                L_Oscillator, OSC_SpinB, L_OSC_F, OSC_F_SpinB,
                L_Phi, E_Phi, L_Out_Preoffset, Out_Preoffset,
                L_Out_Offset, Offset, L_Out_Scale, Out_Scale,
                L_Order, Order_SpinB, L_DB, DB,
                Trig, T_Port_SpinB, L_Trig, Trig_Entry]
        rw = 0
        clm = 0
        for item in Item_List:
            item.grid( row = rw, column = clm, padx = 2, pady = 2,
                    sticky = 'w')
            if clm == 3 :
                clm = 0
                rw += 1
            else : clm += 1

        self.Zi_Setting_List = { 'DAQ': DAQ,
                'Device_id': Device,
                'Proprieties': Prop,
                'Demodulator': Demod_Var,
                'Output_Rate': Output_Rate_Var,
                'Output': Output_Var,
                'Input': Input_Var,
                'Oscillator': OSC_Var,
                'Osc. Freq': OSC_F_Var,
                'Input Gain': Gain_Var,
                'Phase': Phi_Var,
                'Trigger': Trig_Val,
                'Trigger state': Trig_state,
                '50 Ohm': Ohm50_state,
                'AC': AC_state,
                'Harmonics': Harm_Var,
                'Input_Scale': Input_Scale_Var,
                'Out_Scale': Out_Scale_Var,
                'Out_Preoffset': Out_Preoffset_Var,
                'Out_Offset': Out_Offset_Var,
                'LowPassOrder': Order_Var,
                'LowPassDBValue': DB_Var}


        Config_Button = ttk.Button(self, text ='Configure Demodulator'
                +' X', command = lambda : self.Dev_Config_Init(
                    self.Zi_Setting_List))
        Config_Button.grid(row = rw + 1, column = 0, columnspan = 2,
                sticky = 'w', padx = 2, pady = 2)

    def Dev_Config_Init(self, DATA):
        messagebox.showinfo(message = 'If the trigger button in <ON>'+
                ' the oscillator will be automatically disabled for'+
                ' for this demodulator.', icon = 'info', title =
                'Information')
        out_mixer_channel = utils.default_output_mixer_channel(DATA['Proprieties'])
        #First desactivate all input,scopes,Demodulator
        Reset_settings = [
                ['/%s/demods/*/enable' % DATA['Device_id'].get(),0],
                ['/%s/demods/*/trigger' % DATA['Device_id'].get(),0],
                ['/%s/sigout/*/enables/*' % DATA['Device_id'].get(),0],
                ['/%s/scopes/*/enable' % DATA['Device_id'].get(),0]
                ]
        DATA['DAQ'].set(Reset_settings)
        DATA['DAQ'].sync()

        Input_setting = [
                ['/%s/sigins/%d/ac' % (DATA['Device_id'].get(),DATA['Input'].get()), DATA['AC'].get() == 'Enable' ],
                ['/%s/sigins/%d/imp50' % (DATA['Device_id'].get(),DATA['Input'].get()), DATA['50 Ohm'].get() == 'Enable' ],
                ['/%s/sigins/%d/scaling' % (DATA['Device_id'].get(),DATA['Input'].get()), DATA['Input Scale'].get() ],
                ['/%s/demods/%d/enable' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), 1],
                ['/%s/demods/%d/phaseshift' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['Phase'].get()],
                ['/%s/demods/%d/rate' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['Output_Rate'].get()],
                ['/%s/demods/%d/adcselect' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['Input'].get()],
                ['/%s/demods/%d/order' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['LowPassOrder'].get()],
                ['/%s/demods/%d/timeconstant' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), utils(DATA['LowPassDBValue'],
                    DATA['LowPassOrder'].get())],
                ['/%s/demods/%d/oscselect' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['Oscillator'].get()],
                ['/%s/demods/%d/harmonic' % (DATA['Device_id'].get(),DATA['Demodulator'].get()), DATA['Harmonics'].get()],
                ['/%s/oscs/%d/freq' % (DATA['Device_id'].get(),DATA['Oscillator'].get()), DATA['Osc. Freq'].get()],
                ['/%s/sigout/%d/on' % (DATA['Device_id'].get(),DATA['Output'].get()), 1],
                ['/%s/sigout/%d/enables/%d' % (DATA['Device_id'].get(),DATA['Output'].get(),out_mixer_channel), 1],
                ]




















