import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from multiprocessing import Process
# Import of classes
import Zurich_Instrument
import Graphic
import Experiment_file
import Monochromator
import Spectrometer
import Physics_Instrument
import threading


# Main Frame creation
class MainFrame(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # Variable that are spreaded throughout the program
        self.Zurich = Zurich_Instrument.Zurich(self)
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        # List of all de frame
        self.Frame = [HomePage(self), ZurichFrame(self), Mono_Physics(self, mainf=self), SpectroFrame(self, mainf=self)]
        self.Frame.append(Experiment(self, mainf=self))
        self.Frame[0].grid(row=0, column=0, sticky='nsew')
        # Mini Image and Mainframe title
        directory = Path.cwd()
        image = tk.PhotoImage(master=self, file=directory / 'FMQ3.gif')
        tk.Tk.wm_title(self, "femtoQPy")
        tk.Tk.wm_iconphoto(self, '-default', image)
        # Menubar creation
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='File', underline=0, menu=filemenu)
        filemenu.add_command(label='Exit', underline=1, command=lambda: self.quit())
        winmenu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Window', underline=0, menu=winmenu)
        winmenu.add_command(label='Home', underline=0, command=lambda: self.frame_switch(self.Frame[0]))
        winmenu.add_command(label='Zurich', underline=0, command=lambda: self.frame_switch(self.Frame[1]))
        winmenu.add_command(label='Mono+PhysL', underline=0, command=lambda: self.frame_switch(self.Frame[2]))
        winmenu.add_command(label='Spectro.', underline=0, command=lambda: self.frame_switch(self.Frame[3]))
        winmenu.add_command(label='Experiment', underline=0, command=lambda: self.frame_switch(self.Frame[4]))
        graphmenu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label='Graph', underline=0, menu=graphmenu)
        graphmenu.add_command(label='Black theme', underline=0,
                              command=lambda:Graphic.black_theme_graph())
        graphmenu.add_command(label='Default theme', underline=0,
                              command=lambda:Graphic.default_theme_graph())
        self.config(menu=menubar)

        # Here is the line to have a closing procedure that close all
        # connections to devices
        self.protocol('WM_DELETE_WINDOW', self.closing_procedure)
        # Grid scaling
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def frame_switch(self, new):
        for frame in self.Frame:
            frame.grid_forget()
        new.grid(column=0, row=0, sticky='nsew')

    def closing_procedure(self):
        if self.Frame[1]:
            # Do something to close the zurich
            pass
        if self.Frame[2].Linstage.device:
            self.Frame[2].Linstage.device.CloseConnection()
        if self.Frame[2].Mono.arduino:
            # Do something to close serial connection
            pass
        if self.Frame[3].Spectro.spectro:
            # Do something to close connection with spectrometer
            pass

        self.destroy()

# Initial Frame *Put some cozy stuff here*
class HomePage(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(bg='blue', width=100, height=100)
        welcomelabel = tk.Label(self, text='WELCOME', font=24)
        welcomelabel.grid(row=0, column=0, sticky='nsew')
        # Mini Image and Mainframe title
	# Merci à Laurent d'avoir trouver le bug ici :D
        directory = Path.cwd()
        image = tk.PhotoImage(master=self, file=directory / 'FemtoQ_logo_white-bg.png')
        panel = tk.Label(self, image=image)
        panel.image = image
        panel.grid(row=1, column=0, sticky='nsew')
        for i in range(1):
            for j in range(2):
                self.grid_columnconfigure(i, weight=1)
                self.grid_rowconfigure(j, weight=1)


# Frame dispositions for the Zurich Instruments
class ZurichFrame(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config(bg='red', width=100, height=100)
        for i in range(10):
            for j in range(7):
                self.grid_columnconfigure(i, weight=1)
                self.grid_rowconfigure(j, weight=1)
        self.after(1000, self.parent.Zurich.measure_guide)

        def connectionframe():
            # Connection Frame
            connectframe = ttk.Labelframe(self, text='Connect')
            connectframe.grid(row=0, column=0, sticky='nsew')
            connectlbl = tk.Label(connectframe, text='Connect Device')
            connect_var = tk.StringVar()
            connect_var.set('dev2318')
            connect_e = tk.Entry(connectframe, textvariable=connect_var, width=8)
            connectbutton = tk.Button(connectframe, text='Connect',
                                      command=lambda: self.parent.Zurich.connect_device(connect_var.get(),
                                                                                        exp_dependencie=True))
            connectlbl.grid(row=0, column=0, padx=2, pady=2, sticky='nsew')
            connect_e.grid(row=0, column=1, padx=2, pady=2, sticky='nsew')
            connectbutton.grid(row=1, column=0, columnspan=2, padx=2, pady=2, sticky='nsew')

        def inputframe():
            # Input Frame
            inputframe = ttk.Labelframe(self, text='Input')
            # Config Input 1
            input1label = tk.Label(inputframe, text='Input 1')
            input1range = tk.Label(inputframe, text='Range')
            input1range_var = tk.DoubleVar()
            input1range_var.set(1)
            input1rangevalue = tk.Entry(inputframe, textvariable=input1range_var, width=4)
            input1autorange = tk.Button(inputframe, text='ici', width=2, height=1)
            input1scaling = tk.Label(inputframe, text='Scale')
            input1scaleratio_var = tk.DoubleVar()
            input1scaleratio_var.set(1)
            input1scaleratio = tk.Entry(inputframe, textvariable=input1scaleratio_var, width=4)
            input1scaleunit_var = tk.StringVar()
            input1scaleunit_var.set('V')
            input1scaleunit = tk.Entry(inputframe, textvariable=input1scaleunit_var, width=2)
            input1ac = tk.Label(inputframe, text='AC')
            input1ac_var = tk.StringVar()
            input1ac_var.set('Disabled')
            input1acbutton = tk.Checkbutton(inputframe, variable=input1ac_var, onvalue='Enabled', offvalue='Disabled')
            input150 = tk.Label(inputframe, text='50 Ohm')
            input150_var = tk.StringVar()
            input150_var.set('Disabled')
            input150button = tk.Checkbutton(inputframe, variable=input150_var, onvalue='Enabled', offvalue='Disabled')
            inputframe.grid(row=1, column=0, sticky='nsew', rowspan=2)
            input1label.grid(row=0, column=0, columnspan=2, sticky='nsew')
            input1range.grid(row=1, column=0, columnspan=2, sticky='nsew')
            input1rangevalue.grid(row=1, column=2, columnspan=2, sticky='nsew')
            input1autorange.grid(row=1, column=4, sticky='nsew')
            input1scaling.grid(row=2, column=0, columnspan=2, sticky='nsew')
            input1scaleratio.grid(row=2, column=2, columnspan=2, sticky='nsew')
            input1scaleunit.grid(row=2, column=4, sticky='nsew')
            input1ac.grid(row=3, column=0, sticky='nsew')
            input1acbutton.grid(row=3, column=1, sticky='nsew')
            input150.grid(row=3, column=2, sticky='nsew')
            input150button.grid(row=3, column=3, sticky='nsew')
            # Separator
            s = ttk.Separator(inputframe, orient='horizontal')
            s.grid(row=4, column=0, columnspan=4, sticky='nsew', pady=4)
            # config input 2
            input2label = tk.Label(inputframe, text='Input 2')
            input2range = tk.Label(inputframe, text='Range')
            input2range_var = tk.DoubleVar()
            input2range_var.set(1)
            input2rangevalue = tk.Entry(inputframe, textvariable=input2range_var, width=4)
            input2autorange = tk.Button(inputframe, text='ici', width=2, height=1)
            input2scaling = tk.Label(inputframe, text='Scale')
            input2scaleratio_var = tk.DoubleVar()
            input2scaleratio_var.set(1)
            input2scaleratio = tk.Entry(inputframe, textvariable=input2scaleratio_var, width=4)
            input2scaleunit_var = tk.StringVar()
            input2scaleunit_var.set('V')
            input2scaleunit = tk.Entry(inputframe, textvariable=input2scaleunit_var, width=2)
            input2ac = tk.Label(inputframe, text='ac')
            input2ac_var = tk.StringVar()
            input2ac_var.set('Disabled')
            input2acbutton = tk.Checkbutton(inputframe, variable=input2ac_var, onvalue='Enabled', offvalue='Disabled')
            input250 = tk.Label(inputframe, text='50 ohm')
            input250_var = tk.StringVar()
            input250_var.set('Disabled')
            input250button = tk.Checkbutton(inputframe, variable=input250_var, onvalue='Enabled', offvalue='Disabled')
            input2label.grid(row=5, column=0, columnspan=2, sticky='nsew')
            input2range.grid(row=6, column=0, columnspan=2, sticky='nsew')
            input2rangevalue.grid(row=6, column=2, columnspan=2, sticky='nsew')
            input2autorange.grid(row=6, column=4, sticky='nsew')
            input2scaling.grid(row=7, column=0, columnspan=2, sticky='nsew')
            input2scaleratio.grid(row=7, column=2, columnspan=2, sticky='nsew')
            input2scaleunit.grid(row=7, column=4, sticky='nsew')
            input2ac.grid(row=8, column=0, sticky='nsew')
            input2acbutton.grid(row=8, column=1, sticky='nsew')
            input250.grid(row=8, column=2, sticky='nsew')
            input250button.grid(row=8, column=3, sticky='nsew')

            entry_dict = {'input1_range': [input1rangevalue, input1range_var, 'double', '/sigins/0/range'],
                          'input1_scale': [input1scaleratio, [input1scaleratio_var, input1scaleunit_var], 'tension',
                                           '/sigins/0/scaling'],
                          'input1_scale_unit': [input1scaleunit, [input1scaleratio_var, input1scaleunit_var], 'tension',
                                                '/sigins/0/scaling'],
                          'input2_range': [input2rangevalue, input2range_var, 'double', '/sigins/1/range'],
                          'input2_scale': [input2scaleratio, [input2scaleratio_var, input2scaleunit_var], 'tension',
                                           '/sigins/1/scaling'],
                          'input2_scale_unit': [input2scaleunit, [input2scaleratio_var, input2scaleunit_var], 'tension',
                                                '/sigins/1/scaling']
                          }
            self.create_bind(dict_=entry_dict, type_='entry')
            check_dict = {'input1_ac': [input1acbutton, input1ac_var, 'T_F', '/sigins/0/ac'],
                          'input1_50': [input150button, input150_var, 'T_F', '/sigins/0/imp50'],
                          'input2_ac': [input2acbutton, input2ac_var, 'T_F', '/sigins/1/ac'],
                          'input2_50': [input250button, input250_var, 'T_F', '/sigins/1/imp50']
                          }
            self.create_bind(dict_=check_dict, type_='check')
            button_dict = {'input1_autorange': [input1autorange, '/sigins/0/autorange'],
                           'input2_autorange': [input2autorange, '/sigins/1/autorange']
                           }
            self.create_bind(dict_=button_dict, type_='button')

        def outputframe():

            # Output Frame
            outputframe = ttk.Labelframe(self, text='Output')
            output1label = tk.Label(outputframe, text='Output 2')
            output1range = tk.Label(outputframe, text='Range')
            output1range_var = tk.DoubleVar()
            output1range_var.set(1)
            output1rangevalue = tk.Entry(outputframe, textvariable=output1range_var, width=6)
            output1autorange = tk.Button(outputframe, text='ici', width=2, height=1)
            output1offset = tk.Label(outputframe, text='Offset(V)')
            output1offset_var = tk.DoubleVar()
            output1offset_var.set(0)
            output1offset_entry = tk.Entry(outputframe, textvariable=output1offset_var, width=6)
            output1on_var = tk.StringVar()
            output1on_var.set('Disabled')
            output1on = tk.Label(outputframe, text='On')
            output1onbutton = tk.Checkbutton(outputframe, variable=output1on_var, onvalue='Enabled',
                                             offvalue='Disabled')
            output150 = tk.Label(outputframe, text='50 Ohm')
            output150_var = tk.StringVar()
            output150_var.set('Disabled')
            output150button = tk.Checkbutton(outputframe, variable=output150_var, onvalue='Enabled',
                                             offvalue='Disabled')
            outputframe.grid(row=1, column=1, sticky='nsew', rowspan=2)
            output1label.grid(row=0, column=0, sticky='nsew')
            output1range.grid(row=2, column=0, sticky='nsew')
            output1rangevalue.grid(row=2, column=1, columnspan=2, sticky='nsew')
            output1autorange.grid(row=2, column=3, sticky='nsew')
            output1offset.grid(row=3, column=0, sticky='nsew')
            output1offset_entry.grid(row=3, column=1, columnspan=2, sticky='nsew')
            output1on.grid(row=1, column=0, sticky='nsew')
            output1onbutton.grid(row=1, column=1, sticky='nsew')
            output150.grid(row=1, column=2, sticky='nsew')
            output150button.grid(row=1, column=3, sticky='nsew')
            # Separator between the two
            s = ttk.Separator(outputframe, orient='horizontal')
            s.grid(row=4, column=0, columnspan=4, sticky='nsew', pady=4)
            # config output 2
            output2label = tk.Label(outputframe, text='Output 2')
            output2range = tk.Label(outputframe, text='Range')
            output2range_var = tk.DoubleVar()
            output2range_var.set(1)
            output2rangevalue = tk.Entry(outputframe, textvariable=output2range_var, width=6)
            output2autorange = tk.Button(outputframe, text='ici', width=2, height=1)
            output2offset = tk.Label(outputframe, text='Offset(V)')
            output2offset_var = tk.DoubleVar()
            output2offset_var.set(0)
            output2offset_entry = tk.Entry(outputframe, textvariable=output2offset_var, width=6)
            output2on = tk.Label(outputframe, text='On')
            output2on_var = tk.StringVar()
            output2on_var.set('Disabled')
            output2onbutton = tk.Checkbutton(outputframe, variable=output2on_var, onvalue='Enabled',
                                             offvalue='Disabled')
            output250 = tk.Label(outputframe, text='50 Ohm')
            output250_var = tk.StringVar()
            output250_var.set('Disabled')
            output250button = tk.Checkbutton(outputframe, variable=output250_var, onvalue='Enabled',
                                             offvalue='Disabled')
            output2label.grid(row=5, column=0, sticky='nsew')
            output2range.grid(row=7, column=0, sticky='nsew')
            output2rangevalue.grid(row=7, column=1, columnspan=2, sticky='nsew')
            output2autorange.grid(row=7, column=3, sticky='nsew')
            output2offset.grid(row=8, column=0, sticky='nsew')
            output2offset_entry.grid(row=8, column=1, columnspan=2, sticky='nsew')
            output2on.grid(row=6, column=0, sticky='nsew')
            output2onbutton.grid(row=6, column=1, sticky='nsew')
            output250.grid(row=6, column=2, sticky='nsew')
            output250button.grid(row=6, column=3, sticky='nsew')

            entry_dict = {'output1_range': [output1rangevalue, output1range_var, 'double', '/sigouts/0/range'],
                          'output1_offset': [output1offset_entry, output1offset_var, 'double', '/sigouts/0/offset'],
                          'output2_range': [output2rangevalue, output2range_var, 'double', '/sigouts/1/range'],
                          'output2_offset': [output2offset_entry, output2offset_var, 'double', '/sigouts/1/offset']
                          }
            self.create_bind(dict_=entry_dict, type_='entry')
            check_dict = {'output1_enable': [output1onbutton, output1on_var, 'T_F', ['output', '/sigouts/0/on', ['/sigouts/0/enables', '/sigouts/0/amplitudes']]],
                          'output1_50': [output150button, output150_var, 'T_F', '/sigouts/0/imp50'],
                          'output2_enable': [output2onbutton, output2on_var, 'T_F', ['output', '/sigouts/1/on', ['/sigouts/1/enables', '/sigouts/1/amplitudes']]],
                          'output2_50': [output250button, output250_var, 'T_F', '/sigouts/1/imp50']
                          }
            self.create_bind(dict_=check_dict, type_='check')
            button_dict = {'output1_autorange': [output1autorange, '/sigouts/0/autorange'],
                           'output2_autorange': [output2autorange, '/sigouts/1/autorange']
                           }
            self.create_bind(dict_=button_dict, type_='button')

        def demodulatorframe():

            # Demodulator
            demoframe = ttk.Labelframe(self, text='Demodulator')
            demoframe.grid(row=3, column=0, rowspan=4, columnspan=2, sticky='nsew')

            # Demodulator numbering
            demo1 = tk.Label(demoframe, text='#1')
            demo1.grid(row=2, column=0, sticky='nsew')
            demo2 = tk.Label(demoframe, text='#2')
            demo2.grid(row=3, column=0, sticky='nsew')
            demo3 = tk.Label(demoframe, text='#3')
            demo3.grid(row=4, column=0, sticky='nsew')
            demo4 = tk.Label(demoframe, text='#4')
            demo4.grid(row=5, column=0, sticky='nsew')
            demo5 = tk.Label(demoframe, text='#5')
            demo5.grid(row=6, column=0, sticky='nsew')
            demo6 = tk.Label(demoframe, text='#6')
            demo6.grid(row=7, column=0, sticky='nsew')
            demo7 = tk.Label(demoframe, text='#7')
            demo7.grid(row=8, column=0, sticky='nsew')
            demo8 = tk.Label(demoframe, text='#8')
            demo8.grid(row=9, column=0, sticky='nsew')
            # Demodulator input choices
            value_input = ('Sig In 1', 'Sig In 2', 'Trig. 1', 'Trig. 2', 'Aux Out 1', 'Aux Out 2', 'Aux Out 3',
                           'Aux Out 4', 'Aux In 1', 'Aux In 2')
            # Signal input label and input
            s1 = ttk.Separator(demoframe, orient='vertical')
            s1.grid(row=0, column=1, rowspan=20, sticky='nsew', padx=2)
            demoinput = tk.Label(demoframe, text='Input')
            demoinput.grid(row=1, column=2, sticky='nw')
            demosignal = tk.Label(demoframe, text='Signal')
            demosignal.grid(row=0, column=2, sticky='nw')
            demo1choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo1choice['value'] = value_input
            demo1choice.set('Sig In 1')
            demo1choice.grid(row=2, column=2, sticky='nsew', pady=2)
            demo2choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo2choice['value'] = value_input
            demo2choice.set('Sig In 1')
            demo2choice.grid(row=3, column=2, sticky='nsew', pady=2)
            demo3choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo3choice['value'] = value_input
            demo3choice.set('Sig In 1')
            demo3choice.grid(row=4, column=2, sticky='nsew', pady=2)
            demo4choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo4choice['value'] = value_input
            demo4choice.set('Trig. 1')
            demo4choice.grid(row=5, column=2, sticky='nsew', pady=2)
            demo5choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo5choice['value'] = value_input
            demo5choice.set('Sig In 1')
            demo5choice.grid(row=6, column=2, sticky='nsew', pady=2)
            demo6choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo6choice['value'] = value_input
            demo6choice.set('Sig In 1')
            demo6choice.grid(row=7, column=2, sticky='nsew', pady=2)
            demo7choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo7choice['value'] = value_input
            demo7choice.set('Sig In 1')
            demo7choice.grid(row=8, column=2, sticky='nsew', pady=2)
            demo8choice = ttk.Combobox(demoframe, textvariable='', width=8, state='readonly')
            demo8choice['value'] = value_input
            demo8choice.set('Trig. 2')
            demo8choice.grid(row=9, column=2, sticky='nsew', pady=2)

            # Demodulator Mode for every mode
            value_mode = ('Manual')

            # Reference and Mode
            s2 = ttk.Separator(demoframe, orient='vertical')
            s2.grid(row=0, column=3, rowspan=20, sticky='nsew', padx=2)
            demoref = tk.Label(demoframe, text='Reference')
            demoref.grid(row=0, column=4, sticky='nsew')
            demomode = tk.Label(demoframe, text='Mode')
            demomode.grid(row=1, column=4, sticky='nw')
            demo1mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo1mode['values'] = value_mode
            demo1mode.current(0)
            demo1mode.grid(row=2, column=4, sticky='nsew', pady=2)
            demo2mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo2mode['values'] = value_mode
            demo2mode.current(0)
            demo2mode.grid(row=3, column=4, sticky='nsew', pady=2)
            demo3mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo3mode['values'] = value_mode
            demo3mode.current(0)
            demo3mode.grid(row=4, column=4, sticky='nsew', pady=2)
            demo4mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo4mode['values'] = ('Manual', 'ExtRef', 'ExtRef LowBW', 'ExtRef HiBW')
            demo4mode.current(0)
            demo4mode.grid(row=5, column=4, sticky='nsew', pady=2)
            demo5mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo5mode['values'] = value_mode
            demo5mode.current(0)
            demo5mode.grid(row=6, column=4, sticky='nsew', pady=2)
            demo6mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo6mode['values'] = value_mode
            demo6mode.current(0)
            demo6mode.grid(row=7, column=4, sticky='nsew', pady=2)
            demo7mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo7mode['values'] = value_mode
            demo7mode.current(0)
            demo7mode.grid(row=8, column=4, sticky='nsew', pady=2)
            demo8mode = ttk.Combobox(demoframe, textvariable='', width=6, state='readonly')
            demo8mode['values'] = ('Manual', 'ExtRef', 'ExtRef LowBW', 'ExtRef HiBW')
            demo8mode.current(0)
            demo8mode.grid(row=9, column=4, sticky='nsew', pady=2)

            # Frequencies and others
            s3 = ttk.Separator(demoframe, orient='vertical')
            s3.grid(row=0, column=5, rowspan=20, padx=2, sticky='nsew')
            demofreq = tk.Label(demoframe, text='Frequence')
            demofreq.grid(row=0, column=6, columnspan=3, sticky='nsew')
            demoosc = tk.Label(demoframe, text='Osc.')
            demoosc.grid(row=1, column=6, sticky='nsew')
            demoharm = tk.Label(demoframe, text='Harm.')
            demoharm.grid(row=1, column=7, sticky='nsew')
            demophase = tk.Label(demoframe, text='Phase')
            demophase.grid(row=1, column=8, sticky='nsew')
            demo1osc_var = tk.IntVar()
            demo1osc = tk.Spinbox(demoframe, textvariable=demo1osc_var, width=2, from_=0, to=1)
            demo1osc.grid(row=2, column=6, sticky='nsew')
            demo2osc_var = tk.IntVar()
            demo2osc = tk.Spinbox(demoframe, textvariable=demo2osc_var, width=2, from_=0, to=1)
            demo2osc.grid(row=3, column=6, sticky='nsew')
            demo3osc_var = tk.IntVar()
            demo3osc = tk.Spinbox(demoframe, textvariable=demo3osc_var, width=2, from_=0, to=1)
            demo3osc.grid(row=4, column=6, sticky='nsew')
            demo4osc_var = tk.IntVar()
            demo4osc = tk.Spinbox(demoframe, textvariable=demo4osc_var, width=2, from_=0, to=1)
            demo4osc.grid(row=5, column=6, sticky='nsew')
            demo5osc_var = tk.IntVar()
            demo5osc = tk.Spinbox(demoframe, textvariable=demo5osc_var, width=2, from_=0, to=1)
            demo5osc.grid(row=6, column=6, sticky='nsew')
            demo6osc_var = tk.IntVar()
            demo6osc = tk.Spinbox(demoframe, textvariable=demo6osc_var, width=2, from_=0, to=1)
            demo6osc.grid(row=7, column=6, sticky='nsew')
            demo7osc_var = tk.IntVar()
            demo7osc = tk.Spinbox(demoframe, textvariable=demo7osc_var, width=2, from_=0, to=1)
            demo7osc.grid(row=8, column=6, sticky='nsew')
            demo8osc_var = tk.IntVar()
            demo8osc = tk.Spinbox(demoframe, textvariable=demo8osc_var, width=2, from_=0, to=1)
            demo8osc.grid(row=9, column=6, sticky='nsew')
            demo1harm_var = tk.IntVar()
            demo1harm = tk.Spinbox(demoframe, textvariable=demo1harm_var, width=2, from_=1, to=8)
            demo1harm.grid(row=2, column=7, sticky='nsew')
            demo2harm_var = tk.IntVar()
            demo2harm = tk.Spinbox(demoframe, textvariable=demo2harm_var, width=2, from_=1, to=8)
            demo2harm.grid(row=3, column=7, sticky='nsew')
            demo3harm_var = tk.IntVar()
            demo3harm = tk.Spinbox(demoframe, textvariable=demo3harm_var, width=2, from_=1, to=8)
            demo3harm.grid(row=4, column=7, sticky='nsew')
            demo4harm_var = tk.IntVar()
            demo4harm = tk.Spinbox(demoframe, textvariable=demo4harm_var, width=2, from_=1, to=8)
            demo4harm.grid(row=5, column=7, sticky='nsew')
            demo5harm_var = tk.IntVar()
            demo5harm = tk.Spinbox(demoframe, textvariable=demo5harm_var, width=2, from_=1, to=8)
            demo5harm.grid(row=6, column=7, sticky='nsew')
            demo6harm_var = tk.IntVar()
            demo6harm = tk.Spinbox(demoframe, textvariable=demo6harm_var, width=2, from_=1, to=8)
            demo6harm.grid(row=7, column=7, sticky='nsew')
            demo7harm_var = tk.IntVar()
            demo7harm = tk.Spinbox(demoframe, textvariable=demo7harm_var, width=2, from_=1, to=8)
            demo7harm.grid(row=8, column=7, sticky='nsew')
            demo8harm_var = tk.IntVar()
            demo8harm = tk.Spinbox(demoframe, textvariable=demo8harm_var, width=2, from_=1, to=8)
            demo8harm.grid(row=9, column=7, sticky='nsew')
            demo1phase_var = tk.DoubleVar()
            demo1phase = tk.Entry(demoframe, textvariable=demo1phase_var, width=6)
            demo1phase.grid(row=2, column=8, sticky='nsew')
            demo2phase_var = tk.DoubleVar()
            demo2phase = tk.Entry(demoframe, textvariable=demo2phase_var, width=6)
            demo2phase.grid(row=3, column=8, sticky='nsew')
            demo3phase_var = tk.DoubleVar()
            demo3phase = tk.Entry(demoframe, textvariable=demo3phase_var, width=6)
            demo3phase.grid(row=4, column=8, sticky='nsew')
            demo4phase_var = tk.DoubleVar()
            demo4phase = tk.Entry(demoframe, textvariable=demo4phase_var, width=6)
            demo4phase.grid(row=5, column=8, sticky='nsew')
            demo5phase_var = tk.DoubleVar()
            demo5phase = tk.Entry(demoframe, textvariable=demo5phase_var, width=6)
            demo5phase.grid(row=6, column=8, sticky='nsew')
            demo6phase_var = tk.DoubleVar()
            demo6phase = tk.Entry(demoframe, textvariable=demo6phase_var, width=6)
            demo6phase.grid(row=7, column=8, sticky='nsew')
            demo7phase_var = tk.DoubleVar()
            demo7phase = tk.Entry(demoframe, textvariable=demo7phase_var, width=6)
            demo7phase.grid(row=8, column=8, sticky='nsew')
            demo8phase_var = tk.DoubleVar()
            demo8phase = tk.Entry(demoframe, textvariable=demo8phase_var, width=6)
            demo8phase.grid(row=9, column=8, sticky='nsew')

            # Low-Pass Filters
            s4 = ttk.Separator(demoframe, orient='vertical')
            s4.grid(row=0, column=9, sticky='nsew', rowspan=10, padx=2)
            lowpassfilter = tk.Label(demoframe, text='Low-Pass Filters')
            lowpassfilter.grid(row=0, column=10, columnspan=3, sticky='nw')
            demoorderl = tk.Label(demoframe, text='Order')
            demoorderl.grid(row=1, column=10, sticky='nsew')
            demobw3db = tk.Label(demoframe, text='BW 3 dB')
            demobw3db.grid(row=1, column=11, sticky='nsew')
            sincl = tk.Label(demoframe, text='Sinc')
            sincl.grid(row=1, column=12, sticky='nsew')
            demo1order_var = tk.IntVar()
            demo1order = tk.Spinbox(demoframe, textvariable=demo1order_var, width=2, from_=1, to=8)
            demo1order.grid(row=2, column=10)
            demo2order_var = tk.IntVar()
            demo2order = tk.Spinbox(demoframe, textvariable=demo2order_var, width=2, from_=1, to=8)
            demo2order.grid(row=3, column=10)
            demo3order_var = tk.IntVar()
            demo3order = tk.Spinbox(demoframe, textvariable=demo3order_var, width=2, from_=1, to=8)
            demo3order.grid(row=4, column=10)
            demo4order_var = tk.IntVar()
            demo4order = tk.Spinbox(demoframe, textvariable=demo4order_var, width=2, from_=1, to=8)
            demo4order.grid(row=5, column=10)
            demo5order_var = tk.IntVar()
            demo5order = tk.Spinbox(demoframe, textvariable=demo5order_var, width=2, from_=1, to=8)
            demo5order.grid(row=6, column=10)
            demo6order_var = tk.IntVar()
            demo6order = tk.Spinbox(demoframe, textvariable=demo6order_var, width=2, from_=1, to=8)
            demo6order.grid(row=7, column=10)
            demo7order_var = tk.IntVar()
            demo7order = tk.Spinbox(demoframe, textvariable=demo7order_var, width=2, from_=1, to=8)
            demo7order.grid(row=8, column=10)
            demo8order_var = tk.IntVar()
            demo8order = tk.Spinbox(demoframe, textvariable=demo8order_var, width=2, from_=1, to=8)
            demo8order.grid(row=9, column=10)
            demo1bw3db_var = tk.DoubleVar()
            demo1bw3db_var.set(100)
            demo1bw3dbe = tk.Entry(demoframe, textvariable=demo1bw3db_var, width=5)
            demo1bw3dbe.grid(row=2, column=11, sticky='nsew')
            demo2bw3db_var = tk.DoubleVar()
            demo2bw3db_var.set(100)
            demo2bw3dbe = tk.Entry(demoframe, textvariable=demo2bw3db_var, width=5)
            demo2bw3dbe.grid(row=3, column=11, sticky='nsew')
            demo3bw3db_var = tk.DoubleVar()
            demo3bw3db_var.set(100)
            demo3bw3dbe = tk.Entry(demoframe, textvariable=demo3bw3db_var, width=5)
            demo3bw3dbe.grid(row=4, column=11, sticky='nsew')
            demo4bw3db_var = tk.DoubleVar()
            demo4bw3db_var.set(100)
            demo4bw3dbe = tk.Entry(demoframe, textvariable=demo4bw3db_var, width=5)
            demo4bw3dbe.grid(row=5, column=11, sticky='nsew')
            demo5bw3db_var = tk.DoubleVar()
            demo5bw3db_var.set(100)
            demo5bw3dbe = tk.Entry(demoframe, textvariable=demo5bw3db_var, width=5)
            demo5bw3dbe.grid(row=6, column=11, sticky='nsew')
            demo6bw3db_var = tk.DoubleVar()
            demo6bw3db_var.set(100)
            demo6bw3dbe = tk.Entry(demoframe, textvariable=demo6bw3db_var, width=5)
            demo6bw3dbe.grid(row=7, column=11, sticky='nsew')
            demo7bw3db_var = tk.DoubleVar()
            demo7bw3db_var.set(100)
            demo7bw3dbe = tk.Entry(demoframe, textvariable=demo7bw3db_var, width=5)
            demo7bw3dbe.grid(row=8, column=11, sticky='nsew')
            demo8bw3db_var = tk.DoubleVar()
            demo8bw3db_var.set(100)
            demo8bw3dbe = tk.Entry(demoframe, textvariable=demo8bw3db_var, width=5)
            demo8bw3dbe.grid(row=9, column=11, sticky='nsew')
            demo1sinc_var = tk.StringVar()
            demo1sinc_var.set('Disabled')
            demo1sinc = tk.Checkbutton(demoframe, variable=demo1sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo1sinc.grid(row=2, column=12, sticky='nsew')
            demo2sinc_var = tk.StringVar()
            demo2sinc_var.set('Disabled')
            demo2sinc = tk.Checkbutton(demoframe, variable=demo2sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo2sinc.grid(row=3, column=12, sticky='nsew')
            demo3sinc_var = tk.StringVar()
            demo3sinc_var.set('Disabled')
            demo3sinc = tk.Checkbutton(demoframe, variable=demo3sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo3sinc.grid(row=4, column=12, sticky='nsew')
            demo4sinc_var = tk.StringVar()
            demo4sinc_var.set('Disabled')
            demo4sinc = tk.Checkbutton(demoframe, variable=demo4sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo4sinc.grid(row=5, column=12, sticky='nsew')
            demo5sinc_var = tk.StringVar()
            demo5sinc_var.set('Disabled')
            demo5sinc = tk.Checkbutton(demoframe, variable=demo5sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo5sinc.grid(row=6, column=12, sticky='nsew')
            demo6sinc_var = tk.StringVar()
            demo6sinc_var.set('Disabled')
            demo6sinc = tk.Checkbutton(demoframe, variable=demo6sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo6sinc.grid(row=7, column=12, sticky='nsew')
            demo7sinc_var = tk.StringVar()
            demo7sinc_var.set('Disabled')
            demo7sinc = tk.Checkbutton(demoframe, variable=demo7sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo7sinc.grid(row=8, column=12, sticky='nsew')
            demo8sinc_var = tk.StringVar()
            demo8sinc_var.set('Disabled')
            demo8sinc = tk.Checkbutton(demoframe, variable=demo8sinc_var, onvalue='Enabled', offvalue='Disabled')
            demo8sinc.grid(row=9, column=12, sticky='nsew')

            # Data transfert
            s5 = ttk.Separator(demoframe, orient='vertical')
            s5.grid(row=0, column=13, sticky='nsew', padx=2, rowspan=10)
            datatransfer = tk.Label(demoframe, text='Data Transfer')
            datatransfer.grid(row=0, column=14, columnspan=2)
            demoon = tk.Label(demoframe, text='En')
            demoon.grid(row=1, column=14, sticky='nsew')
            demodata = tk.Label(demoframe, text='Rate (Sa/s)')
            demodata.grid(row=1, column=15, sticky='nsew')
            demo1on_var = tk.StringVar()
            demo1on_var.set('Disabled')
            demo1on = tk.Checkbutton(demoframe, variable=demo1on_var, onvalue='Enabled', offvalue='Disabled')
            demo1on.grid(row=2, column=14, sticky='nsew')
            demo2on_var = tk.StringVar()
            demo2on_var.set('Disabled')
            demo2on = tk.Checkbutton(demoframe, variable=demo2on_var, onvalue='Enabled', offvalue='Disabled')
            demo2on.grid(row=3, column=14, sticky='nsew')
            demo3on_var = tk.StringVar()
            demo3on_var.set('Disabled')
            demo3on = tk.Checkbutton(demoframe, variable=demo3on_var, onvalue='Enabled', offvalue='Disabled')
            demo3on.grid(row=4, column=14, sticky='nsew')
            demo4on_var = tk.StringVar()
            demo4on_var.set('Disabled')
            demo4on = tk.Checkbutton(demoframe, variable=demo4on_var, onvalue='Enabled', offvalue='Disabled')
            demo4on.grid(row=5, column=14, sticky='nsew')
            demo5on_var = tk.StringVar()
            demo5on_var.set('Disabled')
            demo5on = tk.Checkbutton(demoframe, variable=demo5on_var, onvalue='Enabled', offvalue='Disabled')
            demo5on.grid(row=6, column=14, sticky='nsew')
            demo6on_var = tk.StringVar()
            demo6on_var.set('Disabled')
            demo6on = tk.Checkbutton(demoframe, variable=demo6on_var, onvalue='Enabled', offvalue='Disabled')
            demo6on.grid(row=7, column=14, sticky='nsew')
            demo7on_var = tk.StringVar()
            demo7on_var.set('Disabled')
            demo7on = tk.Checkbutton(demoframe, variable=demo7on_var, onvalue='Enabled', offvalue='Disabled')
            demo7on.grid(row=8, column=14, sticky='nsew')
            demo8on_var = tk.StringVar()
            demo8on_var.set('Disabled')
            demo8on = tk.Checkbutton(demoframe, variable=demo8on_var, onvalue='Enabled', offvalue='Disabled')
            demo8on.grid(row=9, column=14, sticky='nsew')
            demo1datae_var = tk.StringVar()
            demo1datae_var.set('1.717k')
            demo1datae = tk.Entry(demoframe, textvariable=demo1datae_var, width=6)
            demo1datae.grid(row=2, column=15, sticky='nsew')
            demo2datae_var = tk.StringVar()
            demo2datae_var.set('1.717k')
            demo2datae = tk.Entry(demoframe, textvariable=demo2datae_var, width=6)
            demo2datae.grid(row=3, column=15, sticky='nsew')
            demo3datae_var = tk.StringVar()
            demo3datae_var.set('1.717k')
            demo3datae = tk.Entry(demoframe, textvariable=demo3datae_var, width=6)
            demo3datae.grid(row=4, column=15, sticky='nsew')
            demo4datae_var = tk.StringVar()
            demo4datae_var.set('1.717k')
            demo4datae = tk.Entry(demoframe, textvariable=demo4datae_var, width=6)
            demo4datae.grid(row=5, column=15, sticky='nsew')
            demo5datae_var = tk.StringVar()
            demo5datae_var.set('1.717k')
            demo5datae = tk.Entry(demoframe, textvariable=demo5datae_var, width=6)
            demo5datae.grid(row=6, column=15, sticky='nsew')
            demo6datae_var = tk.StringVar()
            demo6datae_var.set('1.717k')
            demo6datae = tk.Entry(demoframe, textvariable=demo6datae_var, width=6)
            demo6datae.grid(row=7, column=15, sticky='nsew')
            demo7datae_var = tk.StringVar()
            demo7datae_var.set('1.717k')
            demo7datae = tk.Entry(demoframe, textvariable=demo7datae_var, width=6)
            demo7datae.grid(row=8, column=15, sticky='nsew')
            demo8datae_var = tk.StringVar()
            demo8datae_var.set('1.717k')
            demo8datae = tk.Entry(demoframe, textvariable=demo8datae_var, width=6)
            demo8datae.grid(row=9, column=15, sticky='nsew')

            spin_dict = {}
            combo_dict = {}
            entry_dict = {}
            check_dict = {}
            # Input and Mode
            choice_list = [demo1choice, demo2choice, demo3choice, demo4choice, demo5choice, demo6choice, demo7choice,
                           demo8choice]
            for i in range(1, 9):
                combo_dict['demo{}_input'.format(i)] = [choice_list[i-1], 'combobox',
                                                        '/demods/{}/adcselect'.format(i-1)]
            mode_list = [demo4mode, demo8mode]
            for i in range(1, 2):
                combo_dict['demo{}_mode'.format(i)] = [mode_list[i-1], 'combobox_external', '/extrefs/{}'.format(i-1)]

            # Tools for the frequencie of each demodulator
            osc_list = [[demo1osc, demo1osc_var], [demo2osc, demo2osc_var], [demo3osc, demo3osc_var],
                        [demo4osc, demo4osc_var], [demo5osc, demo5osc_var], [demo6osc, demo6osc_var],
                        [demo7osc, demo7osc_var], [demo8osc, demo8osc_var]]
            for i in range(1, 9):
                spin_dict['demo{}_osc'.format(i)] = [osc_list[i-1], 'int', '/demods/{}/oscselect'.format(i-1)]

            harm_list = [[demo1harm, demo1harm_var], [demo2harm, demo2harm_var], [demo3harm, demo3harm_var],
                        [demo4harm, demo4harm_var], [demo5harm, demo5harm_var], [demo6harm, demo6harm_var],
                        [demo7harm, demo7harm_var], [demo8harm, demo8harm_var]]
            for i in range(1, 9):
                spin_dict['demo{}_harm'.format(i)] = [harm_list[i-1], 'int', '/demods/{}/harmonic'.format(i-1)]
            phase_list = [[demo1phase, demo1phase_var], [demo2phase, demo2phase_var], [demo3phase, demo3phase_var],
                        [demo4phase, demo4phase_var], [demo5phase, demo5phase_var], [demo6phase, demo6phase_var],
                        [demo7phase, demo7phase_var], [demo8phase, demo8phase_var]]
            for i in range(1, 9):
                entry_dict['demo{}_phase'.format(i)] = [phase_list[i-1][0], phase_list[i-1][1], 'double',
                                                        '/demods/{}/phaseshift'.format(i-1)]
            order_list = [[demo1order, demo1order_var], [demo2order, demo2order_var], [demo3order, demo3order_var],
                          [demo4order, demo4order_var], [demo5order, demo5order_var], [demo6order, demo6order_var],
                          [demo7order, demo7order_var], [demo8order, demo8order_var]]
            for i in range(1, 9):
                spin_dict['demo{}_order'.format(i)] = [order_list[i-1], 'int', '/demods/{}/order'.format(i-1)]
            bw3db_list = [[demo1bw3dbe, [demo1bw3db_var, demo1order_var]], [demo2bw3dbe, [demo2bw3db_var, demo2order_var]],
                          [demo3bw3dbe, [demo3bw3db_var, demo3order_var]], [demo4bw3dbe, [demo4bw3db_var, demo4order_var]],
                          [demo5bw3dbe, [demo5bw3db_var, demo5order_var]], [demo6bw3dbe, [demo6bw3db_var, demo6order_var]],
                          [demo7bw3dbe, [demo7bw3db_var, demo7order_var]], [demo8bw3dbe, [demo8bw3db_var, demo8order_var]]]
            for i in range(1, 9):
                entry_dict['demo{}_bw3db'.format(i)] = [bw3db_list[i-1][0], bw3db_list[i-1][1], 'double_bw2tc',
                                                        '/demods/{}/timeconstant'.format(i-1)]
            sinc_list = [[demo1sinc, demo1sinc_var], [demo2sinc, demo2sinc_var], [demo3sinc, demo3sinc_var],
                         [demo4sinc, demo4sinc_var], [demo5sinc, demo5sinc_var], [demo6sinc, demo6sinc_var],
                         [demo7sinc, demo7sinc_var], [demo8sinc, demo8sinc_var]]
            for i in range(1, 9):
                check_dict['demo{}_sinc'.format(i)] = [sinc_list[i-1][0], sinc_list[i-1][1], 'T_F',
                                                       '/demods/{}/sinc'.format(i-1)]
            on_list = [[demo1on, demo1on_var], [demo2on, demo2on_var], [demo3on, demo3on_var],
                         [demo4on, demo4on_var], [demo5on, demo5on_var], [demo6on, demo6on_var],
                         [demo7on, demo7on_var], [demo8on, demo8on_var]]
            for i in range(1, 9):
                check_dict['demo{}_on'.format(i)] = [on_list[i-1][0], on_list[i-1][1], 'T_F',
                                                     '/demods/{}/enable'.format(i-1)]
            datae_list = [[demo1datae, demo1datae_var], [demo2datae, demo2datae_var], [demo3datae, demo3datae_var],
                          [demo4datae, demo4datae_var], [demo5datae, demo5datae_var], [demo6datae, demo6datae_var],
                          [demo7datae, demo7datae_var], [demo8datae, demo8datae_var]]
            for i in range(1, 9):
                entry_dict['demo{}_datae'.format(i)] = [datae_list[i-1][0], datae_list[i-1][1], 'double_str2db',
                                                        '/demods/{}/rate'.format(i-1)]

            self.create_bind(dict_=spin_dict, type_='spin')
            self.create_bind(dict_=combo_dict, type_='combo')
            self.create_bind(dict_=entry_dict, type_='entry')
            self.create_bind(dict_=check_dict, type_='check')

        def oscframe():
            # Boxcar
            osc_frame = ttk.Labelframe(self, text='Oscillator')
            osc_frame.grid(row=0, column=1, sticky='nsew')
            osc_1 = tk.Label(osc_frame, text='#1')
            osc_2 = tk.Label(osc_frame, text='#2')
            osc_1.grid(row=0, column=0, sticky='nw')
            osc_2.grid(row=1, column=0, sticky='nw')
            osc1_evar = tk.StringVar()
            osc1_evar.set('100k')
            osc1_e = tk.Entry(osc_frame, textvariable=osc1_evar, width=8)
            osc1_e.grid(row=0, column=1, sticky='nsew')
            osc2_evar = tk.StringVar()
            osc2_evar.set('100k')
            osc2_e = tk.Entry(osc_frame, textvariable=osc2_evar, width=8)
            osc2_e.grid(row=1, column=1, sticky='nsew')
            entry_dict = {'osc1': [osc1_e, osc1_evar, 'double_str2db', '/oscs/0/freq'],
                          'osc2': [osc2_e, osc2_evar, 'double_str2db', '/oscs/0/freq']}
            self.create_bind(dict_=entry_dict, type_='entry')

        def graphicframe():

            def frame_switch(list_, new):
                for frame in list_:
                    list_[frame].grid_forget()
                list_[new].grid(column=0, row=0, sticky='nsew')

            class Scope:

                def __init__(self, parent_g, parent_o, parent_):
                    self.graph = GraphFrame(parent_g, axis=['Time', 'Voltage'], class_=Zurich_Instrument.Scope,
                                            frame_class=parent_)
                    self.option = ScopeOptionFrame(parent_o, self.graph, frame_class=parent_)

            class BoxCar:

                def __init__(self, parent_g, parent_o, parent_):
                    self.graph = GraphFrame(parent_g, axis=['Time', 'Voltage'], class_=Zurich_Instrument.Boxcar,
                                            frame_class=parent_)
                    self.option = BoxOptionFrame(parent_o, self.graph, frame_class=parent_)

            class Plotter:

                def __init__(self, parent_g, parent_o, parent_):
                    self.graph = GraphFrame(parent_g, axis=['Time', 'Voltage'], class_=Zurich_Instrument.Plotter,
                                            frame_class=parent_)
                    self.option = PlotterOptionFrame(parent_o, self.graph, frame_class=parent_)

            class GraphFrame(tk.Frame):

                def __init__(self, parent=None, axis=None, class_=None, frame_class=None):
                    size = [7, 4]
                    tk.Frame.__init__(self, parent)
                    self.grid_columnconfigure(0, weight=1)
                    self.grid_rowconfigure(0, weight=1)
                    self.Graph = Graphic.GraphicFrame(self, axis_name=axis, figsize=size)
                    self.bind('<Configure>', self.Graph.change_dimensions)
                    self.class_ = class_(line=self.Graph.Line, axes=self.Graph.axes, fig=self.Graph.Fig,
                                         zurich=frame_class.parent.Zurich)

            class ScopeOptionFrame(tk.Frame):
                # For now I can only use the first channel and the first scope. It is to be done to work with both
                def __init__(self, parent, assigned_graph, frame_class):
                    def off_on(state):
                        if not frame_class.parent.Zurich.info:
                            messagebox.showinfo(title='Error', message='There is no device connected')
                            state.set('disable')
                            return
                        state = state.get()
                        if state == 'enable':
                            frame_class.parent.Zurich.add_subscribed('/scopes/',
                                                                     assigned_graph.class_, assigned_graph.Graph)
                        elif state == 'disable':
                            frame_class.parent.Zurich.unsubscribed_path('/scopes/')

                    tk.Frame.__init__(self, parent)
                    graph = assigned_graph
                    run_var = tk.StringVar()
                    run_var.set('disable')
                    run = tk.Checkbutton(self, text='Enable', command=lambda: graph.class_.enable_scope(0, run_var),
                                         onvalue='enable', offvalue='disable', variable=run_var)
                    run.grid(row=0, column=0)
                    show_var = tk.StringVar()
                    show_var.set('disable')
                    show = tk.Checkbutton(self, text='Display', onvalue='enable', offvalue='disable', variable=show_var)
                    show.config(command=lambda: off_on(show_var))
                    show.grid(row=1, column=0, sticky='nsew')
                    s1 = ttk.Separator(self, orient='vertical')
                    s1.grid(row=0, column=1, rowspan=5, sticky='nsew', padx=2)
                    control_label = tk.Label(self, text='Control')
                    control_label.grid(row=0, column=2, columnspan=3, sticky='nsew')
                    mode_label = tk.Label(self, text='Mode')
                    mode_label.grid(row=1, column=2, sticky='nw')
                    mode_combo = ttk.Combobox(self, width=12, state='readonly', textvariable='')
                    mode_combo['value'] = ('Time Domain', 'Freq. Domaine')
                    mode_combo.current(0)
                    mode_combo.grid(row=1, column=3, sticky='nsew')
                    sample_label = tk.Label(self, text='Sampling Rate')
                    sample_label.grid(row=2, column=2, sticky='nw')
                    sample_combo = ttk.Combobox(self, width=12, state='readonly', textvariable='')
                    sample_combo['value'] = ('1.80 GHz', '900 MHz', ' 450 MHz', '225 MHz', '113 MHz', '56.2 MHz',
                                             '28.1 MHz', '14.0 MHz', '7.03 MHz', '3.50 MHz', '1.75 MHz', '880 kHz',
                                             '440 kHz', '220 kHz', '110 kHz', '54.9 kHz', '27.5kHz')
                    sample_combo.current(0)
                    sample_combo.grid(row=2, column=3, sticky='nsew')

                    lenght_label = tk.Label(self, text='Length (pts)')
                    lenght_label.grid(row=3, column=2, sticky='nw')
                    lenght_entry_var = tk.IntVar()
                    lenght_entry_var.set(6000)
                    lenght_entry = tk.Entry(self, width=12, textvariable=lenght_entry_var)
                    lenght_entry.grid(row=3, column=3, sticky='nsew')
                    sig_input = tk.Label(self, text='Scope Sig')
                    sig_input.grid(row=4, column=2, sticky='nw')
                    cinput_sig = ttk.Combobox(self, textvariable='', width=8, state='readonly')
                    cinput_sig['value'] = ('Input 1', 'Input 2', 'Trig. 1', 'Trig. 2')
                    cinput_sig.current(0)
                    cinput_sig.grid(row=4, column=3, columnspan=2, sticky='nsew')
                    # This is only for a given scope. Work need to be done to add the second scope
                    combo_dict = {'Mode': [mode_combo, 'combobox', '/scopes/0/'],
                                  'rate': [sample_combo, 'combobox', '/scopes/0/Time'],
                                  'input': [cinput_sig, 'combobox', '/scopes/0/channels/0/inputselect']}
                    entry_dict = {'length': [lenght_entry, lenght_entry_var, 'int', '/scopes/0/length']}
                    frame_class.create_bind(dict_=combo_dict, type_='combo')
                    frame_class.create_bind(dict_=entry_dict, type_='entry')

                    s2 = ttk.Separator(self, orient='vertical')
                    s2.grid(row=0, column=5, rowspan=4, sticky='nsew', padx=2)
                    trigger_label = tk.Label(self, text='Trigger')
                    trigger_label.grid(row=0, column=6, columnspan=2, sticky='nsew')
                    trig_var = tk.StringVar()
                    trig_var.set('disable')
                    trig_enable = tk.Checkbutton(self, text='Enable', variable=trig_var, onvalue='enable',
                                                 offvalue='disable')
                    trig_enable.grid(row=0, column=8, sticky='nsew')
                    tin_label = tk.Label(self, text='Signal')
                    tin_label.grid(row=1, column=6, sticky='nw')
                    tin_sig = ttk.Combobox(self, textvariable='', width=8, state='readonly')
                    tin_sig['value'] = ('Input 1', 'Input 2', 'Trig. 1', 'Trig. 2')
                    tin_sig.current(0)
                    tin_sig.grid(row=1, column=7, columnspan=2, sticky='nsew')
                    slope_label = tk.Label(self, text='Slope')
                    slope_label.grid(row=2, column=6, sticky='nw')
                    slope_sig = ttk.Combobox(self, textvariable='', width=8, state='readonly')
                    slope_sig['value'] = ('None', 'Rise', 'Rise', 'Both')
                    slope_sig.current(1)
                    slope_sig.grid(row=2, column=7, columnspan=2, sticky='nsew')
                    trig_enable.config(command=lambda: assigned_graph.class_.enable_trigger(scope=0, trigger=tin_sig,
                                                                                            variable_=trig_var))
                    combo_dict = {'trigsig': [tin_sig, 'combobox', '/scopes/0/trigchannel'],
                                  'slope': [slope_sig, 'combobox', '/scopes/0/trigslope']}
                    frame_class.create_bind(dict_=combo_dict, type_='combo')

                    # We need to add things related to the FFT analyser
                    s3 = ttk.Separator(self, orient='vertical')
                    s3.grid(row=0, column=9, rowspan=4, sticky='nsew', padx=2)
                    advanced_label = tk.Label(self, text='Advanced')
                    advanced_label.grid(row=0, column=10, columnspan=3, sticky='nsew')
                    fft_label = tk.Label(self, text='FFT Window')
                    fft_label.grid(row=1, column=10, sticky='nw')
                    fft_combo = ttk.Combobox(self, textvariable='', width=8, state='disable')
                    fft_combo['value'] = ('Rectangular', 'Hann', 'Hamming', 'Black. Harris', 'Exponential', 'Cosine',
                                          'Cosine Squared')
                    fft_combo.current(1)
                    fft_combo.grid(row=1, column=11, sticky='nsew')
                    spec_density_var = tk.StringVar()
                    spec_density_var.set('disable')
                    spec_density = tk.Checkbutton(self, text='Spec. Density', onvalue='enable', offvalue='disable'
                                                  , state='disable', variable=spec_density_var)
                    spec_density.grid(row=2, column=10, sticky='nsew')
                    power_var = tk.StringVar()
                    power_var.set('disable')
                    power = tk.Checkbutton(self, text='Power', onvalue='enable', offvalue='disable', state='disable',
                                           variable=power_var)
                    power.grid(row=2, column=11, sticky='nsew')
                    persi_var = tk.StringVar()
                    persi_var.set('disable')
                    persi = tk.Checkbutton(self, text='Persistance', onvalue='enable', offvalue='disable',
                                           variable=persi_var)
                    persi.grid(row=3, column=10, sticky='nsew')
                    bw_var = tk.StringVar()
                    bw_var.set('disable')
                    bw = tk.Checkbutton(self, text='BW Limit', onvalue='enable', offvalue='disable',
                                        variable=bw_var)
                    bw.grid(row=3, column=11, sticky='nsew')

                    s4 = ttk.Separator(self, orient='vertical')
                    s4.grid(row=0, column=13, rowspan=4, sticky='nsew', padx=2)
                    math_label = tk.Label(self, text='Math')
                    math_label.grid(row=0, column=14, columnspan=3, sticky='nsew')
                    label = tk.Label(self, text='to be')
                    label.grid(row=1, column=14)

            class BoxOptionFrame(tk.Frame):

                def __init__(self, parent, assigned_graph, frame_class):
                    def off_on(state):
                        if not frame_class.parent.Zurich.info:
                            messagebox.showinfo(title='Error', message='There is no device connected')
                            state.set('disable')
                            return
                        state = state.get()
                        if state == 'enable':
                            frame_class.parent.Zurich.add_subscribed('/boxcars/',
                                                                     assigned_graph.class_, assigned_graph.Graph)
                        elif state == 'disable':
                            frame_class.parent.Zurich.unsubscribed_path(assigned_graph.class_.path)

                    tk.Frame.__init__(self, parent)
                    graph = assigned_graph
                    run_var = tk.StringVar()
                    run_var.set('disable')
                    run = tk.Checkbutton(self, text='Enable', onvalue='enable', offvalue='disable', variable=run_var)
                    run.grid(row=0, column=0)
                    show_var = tk.StringVar()
                    show_var.set('disable')
                    show = tk.Checkbutton(self, text='Display', onvalue='enable', offvalue='disable', variable=show_var)
                    show.config(command=lambda: off_on(show_var))
                    show.grid(row=1, column=0, sticky='nsew')
                    s1 = ttk.Separator(self, orient='vertical')
                    s1.grid(row=0, column=1, rowspan=4, sticky='nsew', padx=2)
                    pwa_label = tk.Label(self, text='PWA')
                    pwa_label.grid(row=0, column=2, columnspan=3, sticky='nsew')
                    input_label = tk.Label(self, text='Input')
                    input_label.grid(row=1, column=2, sticky='nw')
                    pwa_combo = ttk.Combobox(self, textvariable='', width=8, state='readonly')
                    value_input = ('Sig In 1', 'Sig In 2', 'Trig. 1', 'Trig. 2', 'Aux Out 1', 'Aux Out 2', 'Aux Out 3',
                                   'Aux Out 4', 'Aux In 1', 'Aux In 2')
                    pwa_combo['value'] = value_input
                    pwa_combo.current(0)
                    pwa_combo.grid(row=1, column=3, sticky='nsew')
                    mode_label = tk.Label(self, text='Mode')
                    mode_label.grid(row=2, column=2, sticky='nw')
                    mode_combo = ttk.Combobox(self, width=8, textvariable='', state='readonly')
                    mode_combo['value'] = ('Time', 'Phase')
                    mode_combo.current(1)
                    mode_combo.grid(row=2, column=3, sticky='nsew')
                    mode_combo.bind('<<ComboboxSelected>>', lambda e: graph.class_.phase_and_time(mode_combo))
                    width_label = tk.Label(self, text='Width')
                    width_label.grid(row=3, column=2, sticky='nw')
                    width_entry_var = tk.StringVar()
                    width_entry_var.set('100.00n')
                    width_entry = tk.Entry(self, width=6, textvariable=width_entry_var)
                    width_entry.grid(row=3, column=3, sticky='nsew')
                    sample_label = tk.Label(self, text='# Sample')
                    sample_label.grid(row=4, column=2, sticky='nw')
                    sample_entry_var = tk.StringVar()
                    sample_entry_var.set('450M')
                    sample_entry = tk.Entry(self, width=6, textvariable=sample_entry_var)
                    sample_entry.grid(row=4, column=3, sticky='nsew')

                    s2 = ttk.Separator(self, orient='vertical')
                    s2.grid(row=0, column=5, rowspan=4, sticky='nsew', padx=2)
                    box_label = tk.Label(self, text='BOXCAR')
                    box_label.grid(row=0, column=6, columnspan=1, sticky='nsew')
                    input_label = tk.Label(self, text='Input')
                    input_label.grid(row=1, column=6, sticky='nw')
                    box_combo = ttk.Combobox(self, textvariable='', width=8, state='readonly')
                    value_input = ('Sig In 1', 'Sig In 2')
                    box_combo['value'] = value_input
                    box_combo.current(0)
                    box_combo.grid(row=1, column=7, sticky='nsew')
                    ave_label = tk.Label(self, text='# Averaging P.')
                    ave_label.grid(row=2, column=6, sticky='nw')
                    ave_entry_var = tk.IntVar()
                    ave_entry_var.set(1)
                    ave_entry = tk.Entry(self, width=8, textvariable=ave_entry_var)
                    ave_entry.grid(row=2, column=7, sticky='nsew')
                    rate_label = tk.Label(self, text='Rate (Sa/s)')
                    rate_label.grid(row=3, column=6, sticky='nw')
                    rate_entry_var = tk.StringVar()
                    rate_entry_var.set('1.00M')
                    rate_entry = tk.Entry(self, width=6, textvariable=rate_entry_var)
                    rate_entry.grid(row=3, column=7, sticky='nsew')

                    s3 = ttk.Separator(self, orient='vertical')
                    s3.grid(row=0, column=9, rowspan=4, sticky='nsew', padx=2)
                    math_label = tk.Label(self, text='Math')
                    math_label.grid(row=0, column=10, columnspan=3, sticky='nsew')
                    #Button configuration for this section
                    run.config(command=lambda: graph.class_.enable_boxcar(pwa_input=pwa_combo, box_input=box_combo,
                                                                          variable=run_var))
                    show.config(command=lambda: off_on(show_var))
                    combo_dict = {'pwa_input': [pwa_combo, 'combobox', '/inputpwas/0/inputselect'],
                                  'box_input': [box_combo, 'combobox', '/boxcars/0/inputselect']}
                    frame_class.create_bind(dict_=combo_dict, type_='combo')
                    entry_dict = {'timeWidth': [width_entry, width_entry_var, 'double_str2db',
                                                '/inputpwas/0/aquisitiontime'],
                                  'sample': [sample_entry, sample_entry_var, 'double_str2db',
                                             '/inputpwas/0/samplecount'],
                                  'periods': [ave_entry, ave_entry_var, 'int', '/boxcars/0/periods'],
                                  'rate': [rate_entry, rate_entry_var, 'double_str2db', '/boxcars/0/limitrate']}
                    frame_class.create_bind(dict_=entry_dict, type_='entry')

            class PlotterOptionFrame(tk.Frame):

                def __init__(self, parent, assigned_graph, frame_class):
                    tk.Frame.__init__(self, parent)
                    graph = assigned_graph
                    run_var = tk.StringVar()
                    run_var.set('disable')
                    run = tk.Checkbutton(self, text='Display', )
                    run.grid(row=0, column=0)
                    s1 = ttk.Separator(self, orient='vertical')
                    s1.grid(row=0, column=1, rowspan=4, sticky='nsew', padx=2)
                    control_label = tk.Label(self, text='Control')
                    control_label.grid(row=0, column=2, columnspan=3, sticky='nsew')
                    preset_lbl = tk.Label(self, text='Preset')
                    preset_lbl.grid(row=1, column=2, sticky='nw')
                    preset_options = tk.StringVar(value=('Enable Demods R', 'Enable Demods Cart.',
                                                         'Enable Demods Polar', 'Boxcars', 'Arithmetic Units',
                                                         'Unpopulated', 'Manual'))
                    preset_box = tk.Listbox(self, listvariable=preset_options, height=3)
                    preset_box.selection_set(0)
                    preset_box.grid(row=2, column=2, sticky='nsew')

                    s2 = ttk.Separator(self, orient='vertical')
                    s2.grid(row=0, column=5, rowspan=4, sticky='nsew', padx=2)
                    setting_label = tk.Label(self, text='Settings')
                    setting_label.grid(row=0, column=6, columnspan=3, sticky='nsew')
                    wtime = tk.Label(self, text='Window Time')
                    wtime.grid(row=1, column=6, sticky='nw')
                    wtime_evar = tk.StringVar()
                    wtime_evar.set('100s')
                    wtime_e = tk.Entry(self, textvariable=wtime_evar, width=6)
                    wtime_e.grid(row=1, column=7, sticky='nsew')
                    wtime_e.bind('<Return>', lambda e: assigned_graph.class_.change_axislim(wtime_evar))

                    s3 = ttk.Separator(self, orient='vertical')
                    s3.grid(row=0, column=9, rowspan=4, sticky='nsew', padx=2)
                    math_label = tk.Label(self, text='Math')
                    math_label.grid(row=0, column=10, columnspan=3, sticky='nsew')

                    run.config(command=lambda: graph.class_.update_plotter(graph, run_var))

            option_g = ttk.Combobox(self, textvariable='', state='readonly', width=15)
            option_g.grid(row=0, column=2, sticky='nw')
            option_g['value'] = ('Scope', 'Plotter', 'Boxcar')
            option_g.current(0)

            graph = ttk.Labelframe(self, labelwidget=option_g)
            graph.grid(row=0, column=2, columnspan=8, rowspan=5, sticky='nsew')

            option_o = ttk.Combobox(self, textvariable='', state='readonly', width=15)
            option_o.grid(row=5, column=2, sticky='nw')
            option_o['value'] = ('Scope Option', 'Plotter Option', 'Boxcar Option')

            graph_option = ttk.Labelframe(self, labelwidget=option_o)
            graph_option.grid(row=5, column=2, columnspan=8, rowspan=2, sticky='nsew')

            scope = Scope(parent_g=graph, parent_o=graph_option, parent_=self)
            boxcar = BoxCar(parent_g=graph, parent_o=graph_option, parent_=self)
            plotter = Plotter(parent_g=graph, parent_o=graph_option, parent_=self)

            frames_option_g = {'Scope': scope.graph, 'Boxcar': boxcar.graph, 'Plotter': plotter.graph}
            frame_switch(frames_option_g, option_g.get())
            option_g.bind('<<ComboboxSelected>>', lambda x: frame_switch(frames_option_g, option_g.get()))

            for i in range(1):
                for j in range(1):
                    graph.grid_columnconfigure(i, weight=1)
                    graph.grid_rowconfigure(j, weight=1)

            frames_option_o = {'Scope Option': scope.option, 'Boxcar Option': boxcar.option,
                               'Plotter Option': plotter.option}
            option_o.current(0)
            frame_switch(frames_option_o, option_o.get())
            option_o.bind('<<ComboboxSelected>>', lambda x: frame_switch(frames_option_o, option_o.get()))

            for i in range(1):
                for j in range(1):
                    graph_option.grid_columnconfigure(i, weight=1)
                    graph_option.grid_rowconfigure(j, weight=1)

        connectionframe()
        inputframe()
        outputframe()
        demodulatorframe()
        oscframe()
        graphicframe()

    def create_bind(self, dict_=None, type_=None):

        if (not type_) or (not dict_):
            pass

        function_ = self.parent.Zurich.update_settings

        if type_ == 'entry':
            for element in dict_:
                tk_item = dict_[element]
                tk_item[0].bind('<Return>', lambda e: function_(value=tk_item[1], type_=tk_item[2],
                                                                setting_line=tk_item[3]))
        elif type_ == 'check':
            for element in dict_:
                tk_item = dict_[element]
                tk_item[0].config(command=lambda: function_(value=tk_item[1], type_=tk_item[2],
                                                            setting_line=tk_item[3]))
        elif type_ == 'spin':
            for element in dict_:
                tk_item = dict_[element]
                tk_item[0][0].config(command=lambda: function_(value=tk_item[0][1], type_=tk_item[1],
                                                               setting_line=tk_item[2]))
        elif type_ == 'combo':
            for element in dict_:
                tk_item = dict_[element]
                tk_item[0].bind('<<ComboboxSelected>>', lambda e: function_(value=tk_item[0], type_=tk_item[1],
                                                                            setting_line=tk_item[2]))
        elif type_ == 'button':
            for element in dict_:
                tk_item = dict_[element]
                tk_item[0].config(command=lambda: function_(value=None, type_=None, setting_line=tk_item[1]))


# Frame dispositions for the Monochromator and the Linear Stage of physics Intrumente
class Mono_Physics(tk.Frame):
    def __init__(self, parent, mainf=None):

        class Dialog:
            def __init__(self, parent_frame=None, main_phs=None):
                self.text = 'This method allows you to connect a single devices via the embeded graphical interface '\
                            'from GCS DLL. The first field is requiered. The second allows you to recall data and'\
                            ' settings from this key.'
                self.frame = tk.Frame(parent_frame)
                dev_lbl = tk.Label(self.frame, text='Device name:')
                dev_lbl.grid(row=0, column=0, sticky='nw')
                login_lbl = tk.Label(self.frame, text='Login key:')
                login_lbl.grid(row=2, column=0, sticky='nw')
                dev_var = tk.StringVar()
                dev_entry = tk.Entry(self.frame, width=8, textvariable=dev_var)
                login_var = tk.StringVar()
                login_entry = tk.Entry(self.frame, width=8, textvariable=login_var)
                dev_entry.grid(row=1, column=0, sticky='nsew')
                login_entry.grid(row=3, column=0, sticky='nsew')
                con_b = tk.Button(self.frame, text='Connect Device(s)',
                                  command=lambda: messagebox.showinfo(title='Sorry',
                                                                      message='Script not written'))
                con_b.grid(row=4, column=0, sticky='nsew')

        class Interface:
            def __init__(self, parent_frame=None, main_phs=None):
                class Rs232:
                    def __init__(self, parent_frame):
                        self.frame = tk.Frame(parent_frame)
                        com_lbl = tk.Label(self.frame, text='COM port')
                        com_var = tk.StringVar()
                        com_e = tk.Entry(self.frame, textvariable=com_var, width=10)
                        com_lbl.grid(row=0, column=0, sticky='nw')
                        com_e.grid(row=1, column=0, sticky='nsew')
                        baud_lbl = tk.Label(self.frame, text='Baudrate')
                        baud_var = tk.IntVar()
                        baud_e = tk.Entry(self.frame, textvariable=baud_var, width=10)
                        baud_lbl.grid(row=2, column=0, sticky='nw')
                        baud_e.grid(row=3, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Usb:
                    def __init__(self, parent_frame):
                        self.frame = tk.Frame(parent_frame)
                        serial_lbl = tk.Label(self.frame, text='Serial number:')
                        serial_var = tk.StringVar()
                        serial_e = tk.Entry(self.frame, textvariable=serial_var, width=10)
                        serial_lbl.grid(row=0, column=0, sticky='nw')
                        serial_e.grid(row=1, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Descript:
                    def __init__(self, parent_frame):
                        self.frame = tk.Frame(parent_frame)
                        descrip_lbl = tk.Label(self.frame, text='Description')
                        descrip_var = tk.StringVar()
                        descrip_e = tk.Entry(self.frame, textvariable=descrip_var, width=10)
                        descrip_lbl.grid(row=0, column=0, sticky='nw')
                        descrip_e.grid(row=1, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Adress:
                    def __init__(self, parent_frame):
                        self.frame = tk.Frame(parent_frame)
                        ip_adress_lbl = tk.Label(self.frame, text='IP Adress:')
                        ip_adress_var = tk.StringVar()
                        ip_adress_e = tk.Entry(self.frame, textvariable=ip_adress_var, width=10)
                        ip_adress_lbl.grid(row=0, column=0, sticky='nw')
                        ip_adress_e.grid(row=1, column=0, sticky='nsew')
                        port_lbl = tk.Label(self.frame, text='IP Port:')
                        port_var = tk.IntVar()
                        port_e = tk.Entry(self.frame, textvariable=port_var, width=10)
                        port_lbl.grid(row=2, column=0, sticky='nw')
                        port_e.grid(row=3, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                self.text = "This method allows you to connect a single devices via characteristics of the device. " \
                            "Here is a quick decription of every characteristics: \nCOM port : Number of the COM port" \
                            " devices is connected to. \nBaudrate : Connexion speed of the device/transfer rate of " \
                            "the data. \nIP adress: IP adress associated with the device. IP port : IP port the " \
                            "device is connected to. \nDescription: Description of the device you want to connect."
                self.frame = tk.Frame(parent_frame)
                choice = tk.StringVar()
                rs_232 = tk.Radiobutton(self.frame, text='RS-232', variable=choice, value='RS-232',
                                        command=lambda: self.frame_switch(choice))
                usb = tk.Radiobutton(self.frame, text='USB', variable=choice, value='USB',
                                     command=lambda: self.frame_switch(choice))
                desc = tk.Radiobutton(self.frame, text='TCP/IP: Description', variable=choice, value='Description',
                                      command=lambda: self.frame_switch(choice))
                adress = tk.Radiobutton(self.frame, text='TCP/IP: Adress', variable=choice, value='Adress',
                                        command=lambda: self.frame_switch(choice))
                choice.set('RS-232')
                self.dict_ = {'RS-232': Rs232(parent_frame=self.frame), 'USB': Usb(parent_frame=self.frame),
                              'Description': Descript(parent_frame=self.frame), 'Adress': Adress(parent_frame=self.frame)}
                rs_232.grid(row=0, column=0, sticky='nw')
                usb.grid(row=1, column=0, sticky='nw')
                desc.grid(row=2, column=0, sticky='nw')
                adress.grid(row=3, column=0, sticky='nw')

            def frame_switch(self, new):
                new = new.get()
                for option in self.dict_:
                    self.dict_[option].frame.grid_forget()
                self.dict_[new].frame.grid(column=0, row=4, sticky='nsew', rowspan=4, padx=5)

        class DaisyChain:
            def __init__(self, parent_frame=None, main_phs=None):
                class Rs232:
                    def __init__(self, parent_frame=None):
                        self.frame = tk.Frame(parent_frame)
                        com_lbl = tk.Label(self.frame, text='COM port')
                        com_var = tk.StringVar()
                        com_e = tk.Entry(self.frame, textvariable=com_var, width=10)
                        com_lbl.grid(row=0, column=0, sticky='nw')
                        com_e.grid(row=1, column=0, sticky='nsew')
                        baud_lbl = tk.Label(self.frame, text='Baudrate')
                        baud_var = tk.IntVar()
                        baud_e = tk.Entry(self.frame, textvariable=baud_var, width=10)
                        baud_lbl.grid(row=2, column=0, sticky='nw')
                        baud_e.grid(row=3, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Usb:
                    def __init__(self, parent_frame=None):
                        self.frame = tk.Frame(parent_frame)
                        serial_lbl = tk.Label(self.frame, text='Serial number:')
                        serial_var = tk.StringVar()
                        serial_e = tk.Entry(self.frame, textvariable=serial_var, width=10)
                        serial_lbl.grid(row=0, column=0, sticky='nw')
                        serial_e.grid(row=1, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Descript:
                    def __init__(self, parent_frame):
                        self.frame = tk.Frame(parent_frame)
                        descrip_lbl = tk.Label(self.frame, text='Description')
                        descrip_var = tk.StringVar()
                        descrip_e = tk.Entry(self.frame, textvariable=descrip_var, width=10)
                        descrip_lbl.grid(row=0, column=0, sticky='nw')
                        descrip_e.grid(row=1, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                class Adress:
                    def __init__(self, parent_frame=None):
                        self.frame = tk.Frame(parent_frame)
                        ip_adress_lbl = tk.Label(self.frame, text='IP Adress:')
                        ip_adress_var = tk.StringVar()
                        ip_adress_e = tk.Entry(self.frame, textvariable=ip_adress_var, width=10)
                        ip_adress_lbl.grid(row=0, column=0, sticky='nw')
                        ip_adress_e.grid(row=1, column=0, sticky='nsew')
                        port_lbl = tk.Label(self.frame, text='IP Port:')
                        port_var = tk.IntVar()
                        port_e = tk.Entry(self.frame, textvariable=port_var, width=10)
                        port_lbl.grid(row=2, column=0, sticky='nw')
                        port_e.grid(row=3, column=0, sticky='nsew')
                        con_b = tk.Button(self.frame, text='Connect Device(s)',
                                          command=lambda: messagebox.showinfo(title='Sorry',
                                                                              message='Script not written'))
                        con_b.grid(row=4, column=0, sticky='nsew')

                self.text = "This method allows you to connect multiple devices via an interface. When connected each" \
                            " devices will receive a different ID to be controlled in the program."
                self.frame = tk.Frame(parent_frame)
                choice = tk.StringVar()
                rs_232 = tk.Radiobutton(self.frame, text='RS-232', variable=choice, value='RS-232',
                                        command=lambda: self.frame_switch(choice))
                usb = tk.Radiobutton(self.frame, text='USB', variable=choice, value='USB',
                                     command=lambda: self.frame_switch(choice))
                desc = tk.Radiobutton(self.frame, text='TCP/IP: Description', variable=choice, value='Description',
                                      command=lambda: self.frame_switch(choice))
                adress = tk.Radiobutton(self.frame, text='TCP/IP: Adress', variable=choice, value='Adress',
                                        command=lambda: self.frame_switch(choice))
                choice.set('RS-232')
                self.dict_ = {'RS-232': Rs232(parent_frame=self.frame), 'USB': Usb(parent_frame=self.frame),
                              'Description': Descript(parent_frame=self.frame), 'Adress': Adress(parent_frame=self.frame)}
                rs_232.grid(row=0, column=0, sticky='nw')
                usb.grid(row=1, column=0, sticky='nw')
                desc.grid(row=2, column=0, sticky='nw')
                adress.grid(row=3, column=0, sticky='nw')

            def frame_switch(self, new):
                new = new.get()
                for option in self.dict_:
                    self.dict_[option].frame.grid_forget()
                self.dict_[new].frame.grid(column=0, row=4, sticky='nsew', rowspan=4, padx=5)

        class Identification:
            def __init__(self, parent_frame=None, main_phs=None):
                self.text = "This method allows you to connect a single device via a USB/IP scanning method. Inputs" \
                            " needs to either be a part of the name of the device you are looking for or a part of" \
                            " its IP adress."
                self.frame = tk.Frame(parent_frame)
                usb_lbl = tk.Label(self.frame, text='Device name:')
                usb_lbl.grid(row=0, column=0, sticky='nw')
                ip_lbl = tk.Label(self.frame, text='IP adress:')
                ip_lbl.grid(row=2, column=0, sticky='nw')
                usb_var = tk.StringVar()
                usb_var.set('C-891')
                usb_entry = tk.Entry(self.frame, width=8, textvariable=usb_var)
                ip_var = tk.StringVar()
                ip_entry = tk.Entry(self.frame, width=8, textvariable=ip_var)
                usb_entry.grid(row=1, column=0, sticky='nsew')
                ip_entry.grid(row=3, column=0, sticky='nsew')
                if main_phs.mainf == None:
                    con_b = tk.Button(self.frame, text='Connect Device(s)',
                                      command=lambda: main_phs.Linstage.connect_identification(dev_name=usb_var,
                                                                                           dev_ip=ip_var,
                                                                                           exp_dependencie=False))
                else:
                    con_b = tk.Button(self.frame, text='Connect Device(s)',
                                      command=lambda: main_phs.Linstage.connect_identification(dev_name=usb_var,
                                                                                           dev_ip=ip_var,
                                                                                           exp_dependencie=True))

                con_b.grid(row=4, column=0, sticky='nsew')

        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.mainf = mainf
        self.Mono = Monochromator.MonoChrom(mainf=mainf)
        self.Linstage = Physics_Instrument.LinearStage(mainf=mainf)
        self.config(bg='gray', width=100, height=100)
        # Monochromator Stuff
        mono_frame = ttk.LabelFrame(self, text='Monochromator')
        mono_frame.grid(row=0, column=0, sticky='nsew')
        # This frame has lot of free space right now kinda disturbing
        mono_connect_b = tk.Button(mono_frame, text='Connect', width=8,
                                   command=lambda: self.Mono.connect(exp_dependencie=True))
        mono_connect_b.grid(row=0, column=0, sticky='nsew')
        wave_lbl = tk.Label(mono_frame, text='Wavelength')
        wave_lbl.grid(row=2, column=0, sticky='nw')
        wave_entry_var = tk.IntVar()
        wave_entry = tk.Entry(mono_frame, textvariable=wave_entry_var, width=6)
        wave_entry.bind('<Return>', lambda e: self.Mono.roll_dial(wave_entry_var.get() - self.Mono.current_position))
        wave_entry.grid(row=3, column=0, sticky='nsew')
        if self.mainf == None:
            calibrate_b = tk.Button(mono_frame, text='Calibrate', width=8,
                                    command=lambda: print('Option not available in independant window'))
        else:
            calibrate_b = tk.Button(mono_frame, text='Calibrate', width=8,
                                    command=lambda: self.Mono.calibrate(self.mainf.Frame[3].Spectro.spectro, wave_entry_var))
        calibrate_b.grid(row=1, column=0, sticky='nsew')
        # Physics Linear Stage Stuff
        phs_frame = ttk.LabelFrame(self, text='Physics Linear Stage')
        phs_frame.grid(row=0, column=1, columnspan=3, sticky='nsew')

        phs_con_frame = tk.Frame(phs_frame)
        phs_con_frame.grid(row=0, column=0, rowspan=2, sticky='nsew')

        con_meth = ttk.Combobox(phs_con_frame, width=16, state='readonly', textvariable='')
        con_meth['value'] = ('Dialog', 'Interface', 'Identification', 'Daisy Chain')
        con_meth.current(2)
        con_meth.grid(row=0, column=0, sticky='nw')
        con_meth.bind('<<ComboboxSelected>>', lambda e: self.frame_switch(con_meth, textb))

        phs_control = tk.Frame(phs_frame)
        phs_control.grid(row=2, column=0, rowspan=3, sticky='nsew')

        textb = tk.Text(phs_con_frame, width=50, height=16, wrap='word', state='disabled')
        textb.grid(row=1, column=0, sticky='nsew')

        self.list_ = [Dialog(parent_frame=phs_con_frame, main_phs=self),
                      Interface(parent_frame=phs_con_frame, main_phs=self),
                      Identification(parent_frame=phs_con_frame, main_phs=self),
                      DaisyChain(parent_frame=phs_con_frame, main_phs=self)]
        self.frame_switch(con_meth, textb)
        for i in range(5):
            phs_frame.grid_rowconfigure(i, weight=1)
        phs_frame.grid_columnconfigure(0, weight=1)

        s = ttk.Separator(phs_control, orient='horizontal')
        s.grid(row=0, column=0, columnspan=20, sticky='nsew')
        scanning = tk.Label(phs_control, text='Scanning')
        scanning.grid(row=1, column=0, columnspan=2, sticky='nw')
        pos_lbl = tk.Label(phs_control, text='Position:')
        pos_lbl.grid(row=2, column=0, sticky='nw', pady=3)
        max_pos = tk.Label(phs_control, text='Max:')
        max_pos.grid(row=3, column=0, sticky='nw', pady=3)
        min_pos = tk.Label(phs_control, text='Min:')
        min_pos.grid(row=3, column=1, sticky='nw', pady=3)
        max_evar = tk.DoubleVar()
        max_evar.set(40)
        min_evar = tk.DoubleVar()
        min_evar.set(39.99)
        max_e = tk.Entry(phs_control, textvariable=max_evar, width=8)
        min_e = tk.Entry(phs_control, textvariable=min_evar, width=8)
        max_e.grid(row=4, column=0, sticky='nsew', padx=3)
        min_e.grid(row=4, column=1, sticky='nsew', padx=3)
        ite_var = tk.IntVar()
        ite_var.set(1)
        ite_e = tk.Entry(phs_control, width=6, textvariable=ite_var)
        ite_e.grid(row=5, column=1, sticky='nsew', padx=3)
        ite_lbl = tk.Label(phs_control, text='# Iteration :')
        ite_lbl.grid(row=5, column=0, sticky='nw', padx=3)


        # Entries for the scan and measure function
        step = tk.DoubleVar()
        step.set(0.02) #um
        step_e = tk.Entry(phs_control, textvariable=step, width=8)
        step_e.grid(row=6, column=1, sticky = 'nsew', padx=3)
        step_text = tk.Label(phs_control, text='stage step (um)')
        step_text.grid(row=6, column=0, sticky='nsew', padx=3)
        duree = tk.DoubleVar()
        duree.set(300)
        duree_entry = tk.Entry(phs_control, width=6, textvariable=duree)
        duree_entry.grid(row=7, column=1, sticky='nsew', padx=3)
        duree_text = tk.Label(phs_control, text='measure duration per point (ms)')
        duree_text.grid(row=7, column=0, sticky='nsew', padx=3)



	# Here we should add a step size for the linear stage due the short time I have left I am skipping this part
        # I don't know what should be the best way to implement this quickly and the best way
        scan_b = tk.Button(phs_control, text='SCAN', width=8,
                           command=lambda: threading.Thread(target = self.Linstage.scanning,
                               args = (min_evar, max_evar, ite_var, duree, step)).start())
        scan_b.grid(row=9, column=0, columnspan=2, sticky='nsew', padx=3)


        ## New column in the software for measures without scans (again temporary solution)
        s3 = ttk.Separator(phs_control, orient='vertical')
        s3.grid(row=0, column=14, rowspan=20, sticky='nsew')
        s4 = ttk.Separator(phs_control, orient='horizontal')
        s4.grid(row=0, column=10, columnspan=3)
        measure_only = tk.Label(phs_control, text='Measure only')
        measure_only.grid(row=1, column=11, sticky='nsew', columnspan=2)
        file_measure = tk.StringVar()
        file_measure.set('data')
        filem_entry = tk.Entry(phs_control, width=6, textvariable=file_measure)
        filem_entry.grid(row=2, column=12, sticky='nsew', padx=3)
        filem_text = tk.Label(phs_control, text='name of the saved file')
        filem_text.grid(row=2, column=11, sticky='nsew', padx=3)
        duree_m = tk.DoubleVar()
        duree_m.set(1.0)
        dureem_entry = tk.Entry(phs_control, width=6, textvariable=duree_m)
        dureem_entry.grid(row=3, column=12, sticky='nsew', padx=3)
        dureem_text = tk.Label(phs_control, text='measure duration (s)')
        dureem_text.grid(row=3, column=11, sticky='nsew', padx=3)

        def update_speed(scale, variable):
            scale.configure(label='{}'.format(variable[scale.get()]))
            self.Linstage.change_speed(factor=scale.get())

        s1 = ttk.Separator(phs_control, orient='vertical')
        s1.grid(row=0, column=2, rowspan=20, sticky='nsew')
        config = tk.Label(phs_control, text='Configure')
        config.grid(row=1, column=3, sticky='nw', columnspan=2)
        speed = tk.Label(phs_control, text='Velocity:')
        speed.grid(row=2, column=3, sticky='nw')
        speed_value = ['Slow', 'Medium', 'Quick', 'U-Fast', '5', '6', '7', '8', '9', '10']
        speed_scale = tk.Scale(phs_control, orient='horizontal', from_=0, to=9, width=16, showvalue=False, length=150,
                               command=lambda x: update_speed(speed_scale, speed_value))
        speed_scale.configure(label='{}'.format(speed_value[speed_scale.get()]))
        speed_scale.grid(row=3, column=3, columnspan=2, sticky='nsew')
        calib_lin = tk.Button(phs_control, text='Calibrate device', width=16,
                              command=lambda: self.Linstage.calibration())
        calib_lin.grid(row=6, column=3, columnspan=2, sticky='nsew', padx=3)
        s2 = ttk.Separator(phs_control, orient='vertical')
        s2.grid(row=0, column=5, sticky='nsew', padx=2, rowspan=20)
        control = tk.Label(phs_control, text='Control')
        control.grid(row=1, column=6, columnspan=2, sticky='nw')
        go2 = tk.Label(phs_control, text='Go to position:')
        go2.grid(row=2, column=6, sticky='nw')
        go_var = tk.DoubleVar()
        go_e = tk.Entry(phs_control, width=8, textvariable=go_var)
        go_e.grid(row=2, column=7, sticky='nsew', padx=2, pady=2)
        go_e.bind('<Return>', lambda e: self.Linstage.go_2position(go_var))
        inc = tk.Label(phs_control, text='Increment:')
        inc.grid(row=3, column=6, sticky='nw')
        inc_var = tk.DoubleVar()
        inc_e = tk.Entry(phs_control, width=8, textvariable=inc_var)
        inc_e.grid(row=3, column=7, sticky='nsew', padx=2, pady=2)
        left_b = tk.Button(phs_control, text='L',
                           command=lambda:self.Linstage.increment_move(position=go_var, increment=inc_var, direction='left'))
        right_b = tk.Button(phs_control, text='R',
                           command=lambda:self.Linstage.increment_move(position=go_var, increment=inc_var, direction='right'))
        left_b.grid(row=4, column=6, sticky='nsew', padx=2, pady=2)
        right_b.grid(row=4, column=7, sticky='nsew', padx=2, pady=2)
        s3 = ttk.Separator(phs_control, orient='vertical')
        s3.grid(row=0, column=8, sticky='nsew', rowspan=20)

        for i in range(4):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def frame_switch(self, new, textbox):
        new = new.current()
        textbox.configure(state='normal')
        textbox.delete('1.0', tk.END)
        for class_ in self.list_:
            class_.frame.grid_forget()
        self.list_[new].frame.grid(column=1, row=0, sticky='nsew', rowspan=2, padx=5)
        textbox.insert('1.0', chars=self.list_[new].text)
        textbox.configure(state='disable')


# Frame dispositions for the spectrometer interactions
class SpectroFrame(tk.Frame):
    def __init__(self, parent, mainf=None):
        tk.Frame.__init__(self, parent)
        self.config(bg='brown', width=100, height=100)
        self.parent = parent
        self.Spectro = Spectrometer.Spectro(mainf=mainf)
        option_frame = ttk.Labelframe(self, text='Options')
        option_frame.grid(row=0, column=0, sticky='nsew')
        graph_frame = tk.Frame(self)
        graph_frame.grid(row=0, column=1, columnspan=4, sticky='nsew')
        graph_frame.grid_rowconfigure(0, weight=1)
        graph_frame.grid_columnconfigure(0, weight=1)
        self.graph = Graphic.GraphicFrame(graph_frame, axis_name=['Wavelength', 'Intensity'], figsize=[9, 6])
        self.Spectro.wv_graphic = self.graph
        self.bind('<Configure>', self.graph.change_dimensions)
        # Possible option
        dev_lbl = tk.Label(option_frame, text='Specific Device?')
        dev_evar = tk.StringVar()
        dev_e = tk.Entry(option_frame, textvariable=dev_evar, width=8)
        connect = tk.Button(option_frame, text='Connect',
                            command=lambda: self.Spectro.connect(exp_dependencie=True))
        self.inte_var = tk.IntVar()
        self.inte_var.set(1000)
        inte_lbl = tk.Label(option_frame, text='Integration time [ms]:')
        inte = tk.Entry(option_frame, textvariable=self.inte_var, width=6)
        inte.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(self.inte_var))
        dev_lbl.grid(row=0, column=0, sticky='nw')
        dev_e.grid(row=1, column=0, sticky='nsew')
        connect.grid(row=2, column=0, sticky='nsew')
        inte_lbl.grid(row=3, column=0, sticky='nw')
        inte.grid(row=4, column=0, sticky='nsew')
        dark_spectrum_var = tk.StringVar()
        dark_spectrum_var.set('disable')
        dark_spectrum = tk.Checkbutton(option_frame, text='Dark Spectrum substraction:', variable=dark_spectrum_var,
                                       command=lambda: self.Spectro.enable_darkspectrum(dark_spectrum_var),
                                       onvalue='enable', offvalue='disable')
        dark_spectrum.grid(row=5, column=0, sticky='nw')
        eff_var = tk.StringVar()
        eff_var.set('disable')
        eff = tk.Checkbutton(option_frame, text='Detector efficiencie divider:', variable=eff_var,
                             command=lambda: print('Je vais pas tout faire quand même'),
                             onvalue='enable', offvalue='disable')
        eff.grid(row=6, column=0, sticky='nw')

        logascale_var = tk.StringVar()
        logascale_var.set('disable')
        logascale = tk.Checkbutton(option_frame, text='Logarithmic scale:', variable=logascale_var,
                                   command=lambda: print('You just got fooled again ;)'),
                                   onvalue='enable', offvalue='disable')
        logascale.grid(row=7, column=0, sticky='nw')

        dual_plotting_var = tk.StringVar()
        dual_plotting_var.set('disable')
        dual_plotting = tk.Checkbutton(option_frame, text='Wavalenght + FFT:', variable=dual_plotting_var,
                                       command=lambda: self.Spectro.switch_graphics(dual_plotting_var,
                                                                                           graph_frame),
                                       onvalue='enable', offvalue='disable')
        dual_plotting.grid(row=8, column=0, sticky='nw')

        run_var = tk.StringVar()
        run_var.set('disable')
        run = tk.Button(option_frame, text='RUN', width=8, command=lambda: self.measure(run, run_var, click=True))
        run.grid(row=9, column=0, sticky='nsew')
        for i in range(1,5):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(0, weight=1)

    # It need to have Save Data, Statistics, Axis Modification, Overlaps
    def measure(self, button, variable, click=None):
        if not self.Spectro.spectro:
            return

        t = self.inte_var.get()
        if t == 0:
            t = 1
        if click:
            if variable.get() == 'disable':
                variable.set('enable')
                button.config(text='STOP')
                self.Spectro.extract_intensities()
                self.after(t, self.measure, button, variable)
            elif variable.get() == 'enable':
                variable.set('disable')
                button.config(text='RUN')
        elif not click:
            if variable.get() == 'enable':
                self.Spectro.extract_intensities()
                self.after(t, self.measure, button, variable)


# Window for all of the experiement
class Experiment(ttk.LabelFrame):

    def __init__(self, parent, mainf=None):

        ttk.LabelFrame.__init__(self, parent)
        self.mainf = mainf

        def frame_switch(list_, new):
            for frame in list_:
                list_[frame].containing_frame.grid_forget()
            list_[new].containing_frame.grid(column=0, row=0, sticky='nsew')

        experiment_name = ttk.Combobox(self, textvariable='', state='readonly')
        experiment_name.grid(row=0, column=0, sticky='nsew')
        values = []
        self.parent = parent
        self.experiment_dict = {}

        experiment_name.bind('<<ComboboxSelected>>', lambda e: frame_switch(self.experiment_dict, experiment_name.get()))

        def create_layout(name=None, function_=None, option=None, graph=None):
            if not name:
                pass
            if type(name) == str:
                values.append(name)
                experiment_name['value'] = tuple(values)
                self.experiment_dict[name] = Experiment_file.CreateLayout(mainf=self.mainf, window=self,
                                                                          tools_names=option, graph_names=graph,
                                                                          function_class=function_)

        self.config(labelwidget=experiment_name, width=100, height=100)
        ##########
        # Example of layout creation
        # name : The name of the experiement
        # function_ : This is the class in the Experiment_file
        # option : This contains all the option required for a given experiment all options are displayed in the
        # experiment file
        # graph : is a dictionary containing the name of the desired graph and the name of the axis as a tuple
        # window
        create_layout(name='White_Light', function_=Experiment_file.WhiteLight,
                      option=['Monochrom', 'Zurich', 'Spectrometer', 'Physics_Linear_Stage'],
                      graph={'Wave': ['Wavelength', 'Max Delay'], 'Delay': ['Delay', 'Intensity']})
        create_layout(name='Zero Delay', function_=Experiment_file.ZeroDelay,
                      option=['Physics_Linear_Stage'],
                      graph={'Power': ['Stage position [um]', 'Normalized Voltage'], 'Else': ['a', 'b']})
        create_layout(name='Electro Optic Sampling', function_=Experiment_file.Electro_Optic_Sampling,
                      option=['Physics_Linear_Stage'],
                      graph={'Scanning': ['Required stage position [\mu m]', 'Measured stage position [\mu m]'], 'Else': ['a', 'b']})
        #create_layout(name='Template', function_=Experiment_file.TemplateForExperiment,
        #              option=['Zurich', 'Spectrometer', 'Monochrom'], graph={'1': ['a', 'b'], '2': ['c', 'd']})
        ##########
        experiment_name.current(2)

        frame_switch(self.experiment_dict, experiment_name.get())
        for i in range(1):
            for j in range(1):
                self.grid_columnconfigure(i, weight=1)
                self.grid_rowconfigure(j, weight=1)

if __name__ == '__main__':
    app = MainFrame()
    app.mainloop()
