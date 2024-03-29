"Python program used to combine all instrument functions"
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import matplotlib.pyplot as plt
import numpy as np
import Graphic
import datetime
import femtoQ.tools as fq
import scipy.interpolate as interp
import scipy.signal as sgn
import scipy.constants as sc
import serial
import os
import time
import zhinst.utils
from _horiba_ihr import HoribaIHR320
import femtoQ.pulse_retrieval as fqpr


class CreateLayout:
    """
    This class is used to create the layout in the MainFrame it is called in
    the ExperimentFrame. This is only usable in this way, it creates only the
    main characteristic of the layout but not all of the widget.

    Attributes:
        dependant_function: This is the Experiment class that contains all your
        function in this class. You can see the class template below.
        tools_names: This is all of the classes used in your experiment, ie
        Monochromator and so on.
        containing_frame: This is the frame that is directly linked to your
        experiement in the big Experiement window.
        free_frame: This is the part of your frame that is available for you to
        display all of your widget.
        graph_frame: This is the frame that contains all of your graphics under
        the Combobox widget.
    """
    def __init__(self, function_class=None, mainf=None, window=None, graph_names={}, tools_names=[]):
        """
        The constructor for the Create Class.

        Parameters:
            function_class : This argument is the class of which you stored the experiment so it should be call as self,
            window is the tkinter Frame in which this layout will be put into: should be the experiment Frame called in
            the Main_Frame program
            graph_names : This has to contain every graphic names. We could have for the withelight a delay induced for a
            designed wavelength format should be : { 'Wavelength' : [datax, datay], ... } this can be called in the
            class experiment if needed
            tools_names : This argument should be a list of the item necessary : [ 'Monochromator', ...] the possible
            options are : 'Monochromator', 'Spectrometer', 'Physics_Linear_Stage', 'Zurich'
        """
        if not window:
            pass
        self.dependant_function = function_class(mainf=mainf)

        self.tools_names = tools_names

        def grid_options(dict_, tools_):
            """
                This option displays the tools_names that are required to start
                the experiement.

                Parameters:
                    dict_:Regroupement of tkinter widget that linked to
                    laboratory tools
                    tools_: List of tools wanted in the experiement.
            """
            rw = 0
            for tool in tools_:
                clm = 0
                for tk_module in dict_[tool]:
                    tk_module.grid(row=rw, column=clm, sticky='nsew')
                    clm += 1
                rw += 1

        def frame_switch(dict_, new):
            """
                This switch allows to change graphic that are displayed a
                selected experiement.

                Parameters:
                    dict_:Regroupement of tkinter widget that linked to
                    laboratory tools
                    new: String of the given new frame that will be displayed.
            """
            for frame in dict_:
                dict_[frame].grid_forget()
            dict_[new].grid(column=0, row=0, sticky='nsew')

        self.containing_frame = tk.Frame(window)
        self.free_frame = ttk.LabelFrame(self.containing_frame, text='Experiment special input')
        self.free_frame.grid(row=1, column=0, rowspan=2, sticky='nsew')
        self.dependant_function.create_frame(frame=self.free_frame)
        graph_available = ttk.Combobox(self.containing_frame, textvariable='', state='readonly')
        graph_available.grid(row=0, column=1, sticky='nsew')
        self.graph_frame = ttk.LabelFrame(self.containing_frame, labelwidget=graph_available)
        self.graph_frame.grid(row=0, column=1, rowspan=3, columnspan=4, sticky='nsew')
        graph_possible = {}
        values = []
        # Going through every graphic to allow them to change shape and
        # dimensions and to change inbetween them when you select the right
        # combobox
        for item in graph_names:
            values.append(item)
            graph_possible[item] = tk.Frame(self.graph_frame)
            self.dependant_function.graph_dict[item] = Graphic.GraphicFrame(graph_possible[item],
                                                                            axis_name=graph_names[item])
            graph_possible[item].bind('<Configure>', self.dependant_function.graph_dict[item].change_dimensions)
        # Setting up the initial value of the graph
        graph_available['value'] = tuple(values)
        graph_available.current(0)
        frame_switch(graph_possible, graph_available.get())
        # Combobox that allows you to select the graphic
        graph_available.bind('<<ComboboxSelected>>', lambda x: frame_switch(graph_possible, graph_available.get()))
        option_window = ttk.LabelFrame(self.containing_frame, text='Needed Option')
        option_window.grid(row=0, column=0, sticky='nsew')
        # Creating the initial state of every tools available
        mono_state = tk.StringVar()
        spectro_state = tk.StringVar()
        phs_lin_state = tk.StringVar()
        zurich_state = tk.StringVar()
        self.state_dict = {'Monochrom': mono_state,
                           'Spectrometer': spectro_state,
                           'Physics_Linear_Stage': phs_lin_state,
                           'Zurich': zurich_state
                           }
        mono_state.set('disconnected')
        spectro_state.set('disconnected')
        phs_lin_state.set('disconnected')
        zurich_state.set('disconnected')
        # Tools dictionnairy that contains everything to be displayed
        tools_dict = {'Monochrom': [tk.Label(option_window, text='Monochromator'),
                                    tk.Checkbutton(option_window, state='disable', onvalue='ready',
                                                   offvalue='disconnected', variable=mono_state)],
                      'Spectrometer': [tk.Label(option_window, text='Spectrometer'),
                                       tk.Checkbutton(option_window, state='disable', onvalue='ready',
                                                      offvalue='disconnected', variable=spectro_state)],
                      'Physics_Linear_Stage': [tk.Label(option_window, text='Physics Linear Stage'),
                                               tk.Checkbutton(option_window, state='disable', onvalue='ready',
                                                              offvalue='disconnected', variable=phs_lin_state)],
                      'Zurich': [tk.Label(option_window, text='Zurich Instrument'),
                                 tk.Checkbutton(option_window, state='disable', onvalue='ready', offvalue='disconnected',
                                                variable=zurich_state)],
                      }
        grid_options(tools_dict, tools_names)
        # Allowing column and row to be modified in the frame.
        for i in range(1, 4):
            for j in range(1, 3):
                self.containing_frame.grid_columnconfigure(i, weight=1)
                self.containing_frame.grid_rowconfigure(j, weight=1)
        for i in range(1):
            for j in range(1):
                self.graph_frame.grid_columnconfigure(0, weight=1)
                self.graph_frame.grid_rowconfigure(0, weight=1)

    def update_options(self, tool):
        """
            This function allow to change the state of a tkinter Checkbutton
            that displays the state of a device

            Parameters:
                tool: This is the name of the tool for which the state is
                updated.
        """
        # Changing state of the button
        current_state = self.state_dict[tool].get()
        if current_state == 'disconnected':
            self.state_dict[tool].set('ready')
        elif current_state == 'ready':
            self.state_dict[tool].set('disconnected')

        change_start = False
        # Looking it the start button can be modified
        if len(self.tools_names) == 1:
            state = self.state_dict[self.tools_names[0]].get()
            change_start = (state == 'ready')
        else:
            for tool in self.tools_names:
                state = self.state_dict[tool].get()
                if state == 'disconnected':
                    break

        if change_start:
            self.dependant_function.start_button['state'] = 'normal'


class TemplateForExperiment:
    """
    This is a template to create an experiment window it contains the main
    functions that are required to make it functionnal. Your class does not
    need to be called it is implicitly called during the CreateLayout class.

    Attributes:
        empty_var: This is a random variable in your case it will probably be a
        lot of different things. It is everything that you need to be global in
        your class.
        graph_dict: This is an element that is required, it will be updated and
        will contain all of the Graphic by name that you decided to create in
        the ExperimentFrame. Each key is a name of the graph. Therefore you can
        acces each graph by calling the key of the dict.
    """

    def __init__(self, mainf=None):
        """
        The constructor for your Experiment.

        Parameters:
            mainf : This is the Mainframe, it cannot be anything else.
        """
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}

    def create_frame(self, frame):
        """
        This function is used to create the free frame mentionned in the
        CreateLayout.This is where you place all of the widget you desire to
        have in your experiment.

        Parameters:
            frame : This is the section attributed to your widget in the big
            Experiment frame.
        """

        # this function contains at minimum :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment())
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=11, column=0, columnspan=2, sticky='nsew')

    def stop_experiment(self):
        self.running = False

    def start_experiment(self):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.running = True

        # Here should be all of your experiment for here we have a huge program where we print literally nothing
        print(self.empty_var)
        # You can add a break variable to get out of anyloop you might have like in the Zero Delay Program with
        # The self.running variable

        #if not self.running:
        #    break

        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'






class WhiteLight:

    def __init__(self, ZiData = None, PiData = None, mainf=None):

        # Variables Initialization
        self.main = mainf
        self.zidata = ZiData
        self.PiData = PiData
        self.graph_dict = {}
        self.Zurich = mainf.Frame[1].Zurich

    def create_frame(self, frame):

        nb_wavelenghtpt = tk.Label(frame, text='# Wavelength')
        nb_wavelenghtpt.grid(row=0, column=0, sticky='nw')
        nb_wvlenghtpt_var = tk.IntVar()
        nb_wvlenghtpt = tk.Entry(frame, width=8, textvariable=nb_wvlenghtpt_var)
        nb_wvlenghtpt.grid(row=0, column=1, sticky='nsew')
        
        nb_maxwavelenghtpt = tk.Label(frame, text='Max Wavelength')
        nb_maxwavelenghtpt.grid(row=1, column=0, sticky='nw')
        nb_maxwvlenghtpt_var = tk.IntVar()
        nb_maxwvlenghtpt = tk.Entry(frame, width=8, textvariable=nb_maxwvlenghtpt_var)
        nb_maxwvlenghtpt.grid(row=1, column=1, sticky='nsew')
        
        nb_minwavelenghtpt = tk.Label(frame, text='Min Wavelength')
        nb_minwavelenghtpt.grid(row=2, column=0, sticky='nw')
        nb_minwvlenghtpt_var = tk.IntVar()
        nb_minwvlenghtpt = tk.Entry(frame, width=8, textvariable=nb_minwvlenghtpt_var)
        
        min_pos = tk.Label(frame, text = 'min_pos')
        min_pos.grid(row=11, column=0, sticky='nw')
        mini_pos_var = tk.IntVar()
        mini_pos = tk.Entry(frame, width=8, textvariable=mini_pos_var)
        mini_pos.grid(row=11, column=1, sticky='nsew')
        
        max_pos = tk.Label(frame, text='max_pos')
        max_pos.grid(row=12, column=0, sticky='nw')
        maxi_pos_var = tk.IntVar()
        maxi_pos = tk.Entry(frame, width=8, textvariable=maxi_pos_var)
        maxi_pos.grid(row=12, column=1, sticky='nsew')
        
        iteration = tk.Label(frame, text='nbIterations')
        iteration.grid(row=13, column=0, sticky='nw')
        iteration_var = tk.IntVar()
        iterat = tk.Entry(frame, width=8, textvariable=iteration_var)
        iterat.grid(row=13, column=1, sticky='nsew')
        
        length = tk.Label(frame, text = 'duration of measure per point')
        length.grid(row=14, column=0, sticky='nw')
        length_var = tk.IntVar()
        length_e = tk.Entry(frame, width=8, textvariable=length_var)
        length_e.grid(row=14, column=1, sticky='nsew')
        
        steps = tk.Label(frame, text = 'number of stage steps')
        steps.grid(row=15, column=0, sticky='nw')
        step_var = tk.IntVar()
        step = tk.Entry(frame, width=8, textvariable=step_var)
        step.grid(row=15, column=1, sticky='nsew')
        
        nb_minwvlenghtpt.grid(row=2, column=1, sticky='nsew')
        
        dir_lbl = tk.Label(frame, text='Directory')
        dir_lbl.grid(row=3, column=0, sticky='nw')
        dir_evar = tk.StringVar()
        dir_evar.set('Du coup')
        dir_e = tk.Entry(frame, textvariable=dir_evar, width=8)
        dir_e.grid(row=3, column=1, sticky='nsew')
        dir_b = tk.Button(frame, text='Choose Dir.', command=lambda: filedialog.askdirectory())
        dir_b.grid(row=4, column=0, columnspan=2, sticky='nsew')
        
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment())
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')

    def start_experiment(self):
        '''The experiment in this section is a scan of the delay stage, in this function, we save the measures we take with the lockin'''
	# Here will be implemented the subscription to the lockin

	# After the subscription we scan with the stage (we can use the parameters input in this window)

        self.main.Linstage.scanning_measure(mini_pos_var, maxi_pos_var, iteration_var, lenght_var, step_var)

	# Then we unsubscribe and acquire data in this part (TODO)

        print('hello world')


    def StartMeasure(self):

        poll_length = 0.1  # [s]
        poll_timeout = 500  # [ms]
        poll_flags = 0
        poll_return_flat_dict = True
        self.Find_Delay()
        fullsweep = False
        fullsweep_state = 0
        fullsweep_lim = 1400
        Nbr_nm_perstep = 10
        Position = self.DelayZero
        Pi_dev = self.PiData['Device_id']
        Pi_Axe = self.PiData['Axes']
        Zi_Daq = self.ZiData['DAQ']
        #Full sweep nm
        while fullsweep == False:
            Pi_dev.MOV(Pi_Axe,Position)
            pitools.waitontarget(Pi_dev)
            Zi_Daq.subscribe(self.ZiData['BC_Smp_PATH'])
            time.sleep(0.1)
            Data_Set = Zi_Daq.poll( poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
            Zi_Daq.unsubscribe(self.ZiData['BC_Smp_PATH'])
            Position -= 1
            Sample = DATA_Set[self.ZiData['BC_Smp_PATH']]
            Intensity.append([Pi_dev.qPOS(),np.mean(Sample['value'])])
            if Position == -40:
                Position = self.DelayZero
                self.Coms.RollDial(Nbr_nm_perstep)
                fullsweep_state += Nbr_nm_perstep
                if fullsweep_state == fullsweep_lim:
                    fullsweep = True
        self.Coms.Reset()

        try:
            data = data_set[path]['x']
#            print(data)
#            print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data

    def Find_Delay(self):

        # First, we take measurements, then we find the mean value for a given delay. Then we move the stage and do it again
        # We create a vector of the mean values to find the interference pattern
        poll_length = 0.1  # [s]
        poll_timeout = 500  # [ms]
        poll_flags = 0
        poll_return_flat_dict = True
        Intensity = np.array()

        i = 40

        while (i >= -40):
            self.PiData['Device_id'].MOV(self.PiData['Axes'], i)
            pitools.waitontarget(self.PiData['Device_id'])
            self.ZiData['DAQ'].subscribe(self.ZiData['BC_Smp_PATH'])
            time.sleep(0.1)
            Data_Set = self.ZiData['DAQ'].poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
            self.ZiData['DAQ'].unsubscribe(self.ZiData['BC_Smp_PATH'])
            i -= 2
            Sample = DATA_Set[self.ZiData['BC_Smp_PATH']]
            Intensity.append([self.PiData["Device_id"].qPOS(), np.mean(Sample['value'])])

        # Find the interference pattern
        l = Intensity.size
        left = Intensity[0][0]
        right = Intensity[l][0]
        # Intensity is the array of measurements, the format is couples of values, stage position and intensity
        # thresh is the threshold value for the interference pattern detection, when the intensity drops, it means we
        # reached the delay where the interferences are happening
        thresh = 100
        i = 0
        # We start from left and right and detect a significant change in intensity
        while (abs(Intensity[i + 1][1] - Intensity[i][1]) < thresh):
            i += 1
        left_lim = i

        i = l
        while (abs(Intensity[i][1] - Intensity[i - 1][1]) < thresh):
            i -= 1
        right_lim = i
        # The interference happens between the positions left_lim and right_lim
        # We have to swipe again in this area to get the position of the maximum

        self.DelayZero = None




class FiberCaract:
    
    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Zurich = mainf.Frame[1].Zurich
        self.plotRefSignal = False
        self.refSignal =[]
        self.refTime =[]
        self.refExists = False
        self.LogSpec = False
        self.phaseExists = False
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        lamda_min_lbl = tk.Label(frame, text = 'Min. Wavelength (nm):')
        lamda_max_lbl = tk.Label(frame, text = 'Max. Wavelength (nm):')
        lamda_delta_lbl = tk.Label(frame, text = 'Wavelength inccrement (nm):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        directory_lbl = tk.Label(frame, text='Data saving directory')
        
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-891',
                                                                                   exp_dependencie=True))

        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        self.vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        lamda_min_var = tk.DoubleVar()
        lamda_max_var = tk.DoubleVar()
        lamda_delta_var = tk.DoubleVar()        
        utime_var = tk.IntVar()
        self.wait_var = tk.IntVar()
        self.directory_var=tk.StringVar()
        
        pos_var.set(0)
        self.vel_var.set(0.5)
        min_var.set(0)
        max_var.set(39)
        lamda_min_var.set(1200)
        lamda_max_var.set(2200)
        lamda_delta_var.set(200)
        step_var.set(1000)
        utime_var.set(1)
        self.directory_var.set('E:/Gabriel/Fiber_Charact/')
        
        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = self.vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        lamda_min_e = tk.Entry(frame, width = 6, textvariable = lamda_min_var)
        lamda_max_e = tk.Entry(frame, width = 6, textvariable = lamda_max_var)
        lamda_delta_e = tk.Entry(frame, width = 6, textvariable = lamda_delta_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)
        directory_e = tk.Entry(frame, width=30, textvariable = self.directory_var)

        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=4, column=0, sticky='nsw')
        pos_e.grid(row=4, column=1, sticky='nse')
        vel_lbl.grid(row=5, column=0, sticky='nsw')
        vel_e.grid(row=5, column=1, sticky='nse')
        param_lbl.grid(row=6, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=7, column=0, sticky='nsw')
        min_e.grid(row=7, column=1, sticky='nse')
        max_lbl.grid(row=8, column=0, sticky='nsw')
        max_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')
        lamda_min_lbl.grid(row=10, column=0, sticky='nsw')
        lamda_min_e.grid(row=10, column=1, sticky='nse')
        lamda_max_lbl.grid(row=11, column=0, sticky='nsw')
        lamda_max_e.grid(row=11, column=1, sticky='nse')
        lamda_delta_lbl.grid(row=12, column=0, sticky='nsw')
        lamda_delta_e.grid(row=12, column=1, sticky='nse')
        utime_lbl.grid(row=13, column=0, sticky='nsw')
        utime_e.grid(row=13, column=1, sticky='nse')
        directory_lbl.grid(row=15, column=0, sticky='nsw')
        directory_e.grid(row=15, column=1, sticky='nse')



        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=17, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(self.vel_var))
            
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, lamda_max=lamda_max_var, lamda_min=lamda_min_var, lamda_delta=lamda_delta_var, progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=16, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=18, column=0, columnspan=2, sticky='nsew')   
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save())
        self.RefSignal_button = tk.Button(frame, text='Signal reference', state='disabled', command=lambda: self.SignalRef())
        self.RefSignal_button.grid(row=19, column=0, sticky='nsw')
        self.RefOff_button = tk.Button(frame, text='Ref ON/OFF', state='disabled',command=lambda: self.RemoveRef())
        self.RefOff_button.grid(row=19, column=1, sticky='nse')
        self.Log_button = tk.Button(frame, text='Log Spectrum ON/OFF', state='disabled',command=lambda: self.LogSpectrum())
        self.Log_button.grid(row=20, columnspan=2, sticky='nsew')
        self.save_button.grid(row=21, column=0, columnspan=2, sticky='nsew')
        self.wait = tk.Checkbutton(frame,text='Settling wait time', variable=self.wait_var)   
        self.wait.grid(row=14, column=0, columnspan=2, sticky='nsew')
    def save(self):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(self.directory_var.get() + timeStamp+'_FiberCharact_measurement',data = self.data_array ,lamda = self.lamda_array)
        
    def LogSpectrum(self):
        if self.LogSpec is False:
            self.LogSpec = True
            LogAA = np.log(self.AA)
            self.graph_dict['Spectrum'].Line.set_ydata(LogAA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                LogAref = np.log(self.refSpec)
                self.graph_dict['Spectrum'].LineRef.set_ydata(LogAref)
            self.graph_dict['Spectrum'].axes.set_ylim([np.min(LogAA),1.2*np.max(LogAA)])
            self.graph_dict['Spectrum'].update_graph()
        elif self.LogSpec is True:
            self.LogSpec = False
            self.graph_dict['Spectrum'].Line.set_ydata(self.AA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                self.graph_dict['Spectrum'].LineRef.set_ydata(self.refSpec)
            self.graph_dict['Spectrum'].axes.set_ylim([1.2*np.min(self.AA),1.2*np.max(self.AA)])
            self.graph_dict['Spectrum'].update_graph()
            
    def SignalRef(self):
        if self.refExists is False:
            self.graph_dict['Signal'].LineRef, =  self.graph_dict['Signal'].axes.plot([], [])
            self.graph_dict['Spectrum'].LineRef, = self.graph_dict['Spectrum'].axes.plot([],[])
            self.refExists = True
        self.refSignal = self.S
        self.refTime = self.t
        self.refFreq = self.v
        self.refSpec = self.AA
        if self.plotRefSignal is False:
            self.plotRefSignal = True
        return
    def RemoveRef(self):
        if self.refExists is True:
            if self.plotRefSignal is True:    
                self.plotRefSignal = False
                self.graph_dict['Signal'].LineRef.set_xdata([])
                self.graph_dict['Signal'].LineRef.set_ydata([])
                self.graph_dict['Spectrum'].LineRef.set_xdata([])
                self.graph_dict['Spectrum'].LineRef.set_ydata([])
            elif self.plotRefSignal is False:
                self.plotRefSignal = True
                self.graph_dict['Signal'].LineRef.set_xdata(self.refTime)
                self.graph_dict['Signal'].LineRef.set_ydata(self.refSignal)
                self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
                if self.LogSpec is True:
                    self.graph_dict['Spectrum'].LineRef.set_ydata(np.log(self.refSpec))
                else:
                    self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Signal'].update_graph()
            self.graph_dict['Spectrum'].update_graph()
        return
    
    def Zurich_acquire(self):
        import time
        path = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/sample'
        path2 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/timeconstant'
        path3 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/order'
        tc= self.Zurich.info['daq'].getDouble(path2)
        # print
        order= self.Zurich.info['daq'].getDouble(path3)
        if self.wait_var.get() == 1:
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            if order == 1:
                Settling_time = 4.61*tc
            elif order == 2:
                Settling_time = 6.64*tc
            elif order == 3:
                Settling_time = 8.41*tc
            elif order == 4:
                Settling_time = 10.05*tc
            time.sleep(Settling_time)
        self.Zurich.info['daq'].subscribe(path)
        data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)


        try:
            data = data_set[path]['x']
            # print(data)
            # print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data



    def zurich_Boxcar(device_id, do_plot=False):
        apilevel_example = 6  # The API level supported by this example.
        err_msg = "This example can only be ran on UHF Instruments with the BOX option enabled."
        # Call a zhinst utility function that returns:
        # - an API session `daq` in order to communicate with devices via the data server.
        # - the device ID string that specifies the device branch in the server's node hierarchy.
        # - the device's discovery properties.
        (daq, device, props) = zhinst.utils.create_api_session(
            device_id, apilevel_example, required_devtype="UHF", required_options=["BOX"], required_err_msg=err_msg
        )
        zhinst.utils.api_server_version_check(daq)
    
        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(daq, device)
    
        # Now configure the instrument for this experiment. The following channels
        # and indices work on all device configurations. The values below may be
        # changed if the instrument has multiple input/output channels and/or either
        # the Multifrequency or Multidemodulator options installed.
    #    out_channel = 0
    #    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
        in_channel = 0
        osc_index = 0
    #    frequency = 400e3
        boxcar_index = 0
        inputpwa_index = 0
        amplitude = 0.6
        frequency = 39.063e6
        windowstart = 5 # boxcar windowstart [degrees]
        windowsize = 15e-9  # boxcar windowsize [seconds]
        periods_vals = np.logspace(4, 4, 1, base=2)
        demod_1_index = 3
        demod_2_index = 7
    #    demod_rate = 10e3
        exp_setting = [
            ["/%s/sigins/%d/imp50" % (device, in_channel), 1],
            ["/%s/sigins/%d/ac" % (device, in_channel), 0],
            ["/%s/sigins/%d/range" % (device, in_channel), 2 * amplitude],
    #        ["/%s/demods/%d/enable" % (device, demod_index), 1],
    #        ["/%s/demods/%d/order" % (device, demod_index), 4],
            ["/%s/extrefs/0/enable" % (device), 0],
            ["/%s/extrefs/1/enable" % (device), 0],
            ["/%s/demods/%d/adcselect" % (device, demod_1_index), 3],
            ["/%s/demods/%d/adcselect" % (device, demod_2_index), 3],
    #        ["/%s/demods/%d/mode" % (device, demod_index), 2],
    #        ["/%s/demods/%d/rate" % (device, demod_index), demod_rate],
            ["/%s/inputpwas/%d/oscselect" % (device, inputpwa_index), osc_index],
            ["/%s/inputpwas/%d/inputselect" % (device, inputpwa_index), in_channel],
            ["/%s/inputpwas/%d/mode" % (device, inputpwa_index), 1],
            ["/%s/inputpwas/%d/shift" % (device, inputpwa_index), 0],
            ["/%s/inputpwas/%d/harmonic" % (device, inputpwa_index), 1],
            ["/%s/inputpwas/%d/samplecount" % (device, inputpwa_index), 33.5544e6],
            ["/%s/inputpwas/%d/enable" % (device, inputpwa_index), 1],
            ["/%s/boxcars/%d/oscselect" % (device, boxcar_index), osc_index],
            ["/%s/boxcars/%d/inputselect" % (device, boxcar_index), in_channel],
            ["/%s/boxcars/%d/windowstart" % (device, boxcar_index), windowstart],
            ["/%s/boxcars/%d/windowsize" % (device, boxcar_index), windowsize],
            ["/%s/boxcars/%d/limitrate" % (device, boxcar_index), 13e6],
            ["/%s/boxcars/%d/periods" % (device, boxcar_index), periods_vals[0]],
            ["/%s/boxcars/%d/baseline/windowstart" % (device, boxcar_index), 220],
            ["/%s/boxcars/%d/baseline/enable" % (device, boxcar_index), 0],
            ["/%s/boxcars/%d/enable" % (device, boxcar_index), 1],
            #ziDAQ('setInt', '/dev2318/boxcars/0/baseline/enable', 1);
            ["/%s/oscs/%d/freq" % (device, osc_index), frequency],
    #        ["/%s/sigouts/%d/on" % (device, out_channel), 1],
    #        ["/%s/sigouts/%d/enables/%d" % (device, out_channel, out_mixer_channel), 1],
    #        ["/%s/sigouts/%d/range" % (device, out_channel), 1],
    #        ["/%s/sigouts/%d/amplitudes/%d" % (device, out_channel, out_mixer_channel), amplitude],
        ]
        daq.set(exp_setting)
    
        # Wait for boxcar output to settle
        time.sleep(periods_vals[0] / frequency)
    
        # Perform a global synchronisation between the device and the data server:
        # Ensure that the settings have taken effect on the device before issuing
        # the poll().
        daq.sync()
    
        # Get the values that were actually set on the device
        frequency_set = daq.getDouble("/%s/oscs/%d/freq" % (device, osc_index))
        windowstart_set = daq.getDouble("/%s/boxcars/%d/windowstart" % (device, boxcar_index))
        windowsize_set = daq.getDouble("/%s/boxcars/%d/windowsize" % (device, boxcar_index))
        rate = daq.getDouble("/%s/boxcars/%d/rate" % (device, boxcar_index))
        bw = daq.getDouble("/%s/boxcars/%d/averagerbandwidth" % (device, boxcar_index))
    
        # Subscribe to the nodes we would like to record data from
        boxcar_sample_path = "/%s/boxcars/%d/sample" % (device, boxcar_index)
        boxcar_periods_path = "/%s/boxcars/%d/periods" % (device, boxcar_index)
        inputpwa_wave_path = "/%s/inputpwas/%d/wave" % (device, inputpwa_index)
        daq.subscribe([boxcar_sample_path, boxcar_periods_path, inputpwa_wave_path])
        # We use getAsEvent() to ensure we obtain the first ``periods`` value; if
        # its value didn't change, the server won't report the first value.
        daq.getAsEvent(boxcar_periods_path)
        
    
        for periods in periods_vals:
            time.sleep(0.5)
            daq.setInt(boxcar_periods_path, int(periods))
    
        # Poll the data
        poll_length = 4 # [s]
        poll_timeout = 500 # [ms]
        poll_flags = 0
        poll_return_flat_dict = True
        data = daq.poll(poll_length, poll_timeout, poll_flags, poll_return_flat_dict)
    
        # Unsubscribe from all paths
        daq.unsubscribe("*")
    
        # Check the dictionary returned by poll contains the subscribed data. The
        # data returned is a dictionary with keys corresponding to the recorded
        # data's path in the node hierarchy
        assert data, "poll returned an empty data dictionary, did you subscribe to any paths?"
        assert boxcar_sample_path in data, "data dictionary has no key '%s'" % boxcar_sample_path
        assert boxcar_periods_path in data, "data dictionary has no key '%s'" % boxcar_periods_path
        assert inputpwa_wave_path in data, "data dictionary has no key '%s'" % inputpwa_wave_path
    
        sample = data[boxcar_sample_path]
    #    pwa = data[inputpwa_wave_path]
    
        # When using API Level 4 (or higher) poll() returns both the 'value' and
        # 'timestamp' of the node. These are two vectors of the same length;
        # which consist of (timestamp, value) pairs.
        boxcar_value = sample["value"]
        boxcar_timestamp = sample["timestamp"]
        boxcar_periods_value = data[boxcar_periods_path]["value"]
        boxcar_periods_timestamp = data[boxcar_periods_path]["timestamp"]
        clockbase = float(daq.getInt("/%s/clockbase" % device))
    
        print(f"Measured average boxcar amplitude is {np.mean(boxcar_value):.5e} V.")
    
        if do_plot:
            # get the sample rate of the device's ADCs
            clockbase = float(daq.getInt("/%s/clockbase" % device))
            # convert timestamps from ticks to seconds via clockbase
            boxcar_t = (boxcar_timestamp - boxcar_timestamp[0]) / clockbase
            boxcar_periods_t = (boxcar_periods_timestamp - boxcar_periods_timestamp[0]) / clockbase
            boxcar_periods_t[0] = boxcar_t[0]
            # Create plot
            import matplotlib.pyplot as plt
    
            _, ax1 = plt.subplots()
            ax2 = ax1.twinx()
    
            ax1.grid(True)
            ax1.plot(boxcar_t, boxcar_value, label="boxcar output")
            ax1.set_xlabel("Time (s)")
    
            ax2.step(
                np.append(boxcar_periods_t, boxcar_t[-1]),
                np.append(boxcar_periods_value, boxcar_periods_value[-1]),
                "-r",
                label="Averaging periods",
            )
            ax2.set_yscale("log")
            ax1.set_xlim(min(boxcar_t[0], boxcar_periods_t[0]), max(boxcar_t[-1], boxcar_periods_t[-1]))
            ax2.legend(loc=1)
            ax1.set_title("Boxcar output: The effect of averaging\nperiods on the boxcar value.")
            ax1.legend(loc=4)
            ax1.set_ylabel("Boxcar value (V)")
            ax2.set_ylabel("Number of Averaging Periods")
    
            _, ax = plt.subplots()
            ax.grid(True)
            pwa_wave = data[inputpwa_wave_path][-1]
            pwa_wave["binphase"] = pwa_wave["binphase"] * 360 / (2 * np.pi)
            ax.axhline(0, color="k")
    #         The inputpwa waveform is stored in 'x', currently 'y' is unused.
            ax.plot(pwa_wave["binphase"], 1e6*pwa_wave["x"])
            windowsize_set_degrees = 360 * frequency_set * windowsize_set
            phase_window = (pwa_wave["binphase"] >= windowstart_set) & (
                pwa_wave["binphase"] <= windowstart_set + windowsize_set_degrees
            )
            ax.fill_between(pwa_wave["binphase"], 0, pwa_wave["x"], where=phase_window, alpha=0.2)
            ax.set_xlim(0, 360)
            title = "Input PWA waveform, the shaded region shows the portion\n of the waveform the boxcar is integrating."
            ax.set_title(title)
            ax.set_xlabel("Phase (degrees)")
            ax.set_ylabel("Amplitude (uV)")
    
    #        plt.savefig('ac_on.png')
            plt.show()
        return sample,clockbase,bw,rate
    # device_id="dev2318"
    # sample,clockbase,bw,rate=run_example(device_id, do_plot=False)
    # values=sample["value"]
    # timestmp=(sample["timestamp"]-sample["timestamp"][0])/clockbase
    # print("The averaging bandwidth is",bw," and the actual rate is",rate)
    # #fin_table = np.column_stack((timestmp,values))
    # #titre= "Rate "+str(rate)+" bw : "+str(bw)
    # #title="gatewidth_5n_ps32_2Mlowpass_1Mohm_ACon_3.txt"
    # #np.savetxt(title,fin_table,delimiter=" ",header=titre)





    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, lamda_max=None, lamda_min=None, lamda_delta=None, progress=None, update_time=None):
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.RefSignal_button['state'] = 'disabled'
        self.RefOff_button['state'] = 'disabled'
        self.Log_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        import scipy
        import femtoQ.tools as fQ
        c = scipy.constants.c
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()/1000
        lamda_min=int(lamda_min.get())
        lamda_max=int(lamda_max.get())
        lamda_delta=int(lamda_delta.get())
        
        update_time = update_time.get()

        return_vel = tk.IntVar()
        return_vel.set(1)


            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))
        
        
            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)


            # Wavelength steps initialization
        steps_lamda = int(np.floor((lamda_max-lamda_min)/lamda_delta)+1)
        self.lamda_array=np.linspace(lamda_min,lamda_max,steps_lamda)
        self.data_array = np.zeros([steps_lamda,2,nsteps+1])

            # Variables for the graph update
        
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        EOS_graph = self.graph_dict['Signal']
        EOS_graph.axes.set_ylim([-10,10])
        EOS_graph.axes.set_xlim([0, (max_pos-min_pos)*2/1000/c*1e15])
        EOS_graph.Line.set_xdata([])
        EOS_graph.Line.set_ydata([])
        if self.plotRefSignal is True:
            EOS_graph.LineRef.set_xdata(self.refTime)
            EOS_graph.LineRef.set_ydata(self.refSignal)
            EOS_graph.LineRef.set_linestyle('--')
            self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
            self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Spectrum'].LineRef.set_linestyle('--')
        EOS_graph.update_graph()
        self.graph_dict['Spectrum'].update_graph()
            #Steps in wavelength
        for j in range(len(self.lamda_array)):
            answer = messagebox.askokcancel(title='Verify Wavelength', message='Are you sure the laser is at ' + str(int(self.lamda_array[j])) + ' nm?', icon=messagebox.WARNING)
            if not answer:
                self.running = False
                return
            
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(move[0])
            self.PI.set_velocity(self.vel_var)
            
            pos = np.zeros(nsteps+1)
            self.S = np.zeros(nsteps+1)
            self.t= np.zeros(nsteps+1)
            
                # Main scanning and measurements
            for i in range(nsteps+1):
                # Move stage to required position
                self.PI.go_2position(move[i])
                # Measure real position
                pos[i] = self.PI.get_position()
                # Measure signal
                self.t[i] = (pos[i]-pos[0])*2/1000/c*1e15
                self.S[i] = np.mean(self.Zurich_acquire())*1000
                
                # Actualise progress bar
                if progress:
                    progress['value'] = (i)/(nsteps)
                    progress.update()
                # Actualise graph if required
                if (time.time() - last_gu) > update_time:
                    scan_graph.Line.set_xdata(iteration[:i])
                    scan_graph.Line.set_ydata(pos[:i])
                    scan_graph.update_graph()
                    EOS_graph.Line.set_xdata(self.t[:i])
                    EOS_graph.Line.set_ydata(self.S[:i])
                    EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
                    EOS_graph.update_graph()
                    
                    last_gu = time.time()
                    
                if not self.running:
                    break
            
            
            # data = np.array([self.t,self.S])
            print(self.t,self.S)
            self.data_array[j,0]=self.t
            self.data_array[j,1]=self.S

            
            if not self.running:
                    break
        if not self.running:

            self.PI.set_velocity(return_vel)
            self.PI.go_2position(min_pos)
            self.PI.set_velocity(self.vel_var)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:

            self.PI.set_velocity(return_vel)
            self.PI.go_2position(min_pos)
            self.PI.set_velocity(self.vel_var)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
            EOS_graph.Line.set_xdata(self.t)
            EOS_graph.Line.set_ydata(self.S)
            EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
            EOS_graph.update_graph()
            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
        
            # Display spectrum graph
            spec_t = self.t*1e-15
            t_sort, indices = np.unique(spec_t,return_index=True)
            S_sort = self.S[indices]
            func = interp.interp1d(t_sort, S_sort,kind='quadratic')
            t_interp = np.linspace(t_sort.min(),t_sort.max(),len(t_sort))
            E_interp = func(t_interp)
            self.v,self.A = fQ.ezfft(t_interp,E_interp)
            self.AA = np.abs(self.A)**2
            self.AA = self.AA/np.max(self.AA)
            self.v = self.v/1e12
            Spectrum_graph = self.graph_dict['Spectrum']
            Spectrum_graph.axes.set_ylim([0, 1.1*np.max(self.AA)])
            Spectrum_graph.axes.set_xlim([np.min(self.v), np.max(self.v)])
            Spectrum_graph.Line.set_xdata([self.v])
            Spectrum_graph.Line.set_ydata([self.AA])
            
            if self.phaseExists is False:
                        self.Phase_graph_ax = Spectrum_graph.axes.twinx()
                        self.LinePhase, = self.Phase_graph_ax.plot([],[],'m')
                        self.phaseExists = True
            phi = np.arctan2(self.A.imag,self.A.real)
            phi = np.unwrap(phi)
            a,b = np.polyfit(self.v,phi,deg=1,w=self.AA)
            slope = a*self.v+b
            phi = phi - slope
            self.Phase_graph_ax.set_ylim([-2*np.pi,2*np.pi])
            self.LinePhase.set_xdata(self.v)
            self.LinePhase.set_ydata([phi])
            self.LinePhase.set_linestyle(':')
            Spectrum_graph.update_graph()
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.RefSignal_button['state'] = 'normal'
        self.RefOff_button['state'] = 'normal'
        self.Log_button['state'] = 'normal'





# Here is the template for the experiement
class ZeroDelay:

    # This class is implicitly called in the main frame
    def __init__(self, mainf=None):
        import Red_DAQ
        # here are the initiation of the item that will be called throughout the program as self
        self.mainf = mainf
        self.PI = None
        self.DAQ = Red_DAQ.PMD_1008()
        self.graph_dict = {}
        self.running = False

    def create_frame(self, frame):

        daqc_b = tk.Button(frame, text='Connect ME-RedLab', command=lambda:self.DAQ.connect_card())
        scan_lbl = tk.Label(frame, text='Scanning option')
        maxp_lbl = tk.Label(frame, text='Max. pos. [mm]:')
        minp_lbl = tk.Label(frame, text='Min. pos. [mm]:')
        step_lbl = tk.Label(frame, text='Step size [um]:')
        filen_lbl = tk.Label(frame, text='File name :')
        mtime_lbl = tk.Label(frame, text='Time @ pts [ms]:')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        scan_lbl = tk.Label(frame, text='Number of ave. scans :')
        nite_lbl = tk.Label(frame, text='# of iteration done :')
        daqc_b.grid(row=0, column=0, columnspan=2, sticky='nsew')
        scan_lbl.grid(row=1, column=0, sticky='nsw')
        maxp_lbl.grid(row=2, column=0, sticky='nsw')
        minp_lbl.grid(row=3, column=0, sticky='nsw')
        step_lbl.grid(row=4, column=0, sticky='nsw')
        filen_lbl.grid(row=5, column=0, sticky='nsw')
        mtime_lbl.grid(row=6, column=0, sticky='nsw')
        utime_lbl.grid(row=7, column=0, sticky='nsw')
        scan_lbl.grid(row=8, column=0, sticky='nsw')
        nite_lbl.grid(row=12, column=0, sticky='nsw')
        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=9, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1

        maxp_var = tk.DoubleVar()
        maxp_var.set(-16.26)
        minp_var = tk.DoubleVar()
        minp_var.set(-16.28)
        step_var = tk.DoubleVar()
        step_var.set(0.05)
        filen_var = tk.StringVar()
        filen_var.set('Test')
        mtime_var = tk.IntVar()
        mtime_var.set(1)
        utime_var = tk.IntVar()
        utime_var.set(5)
        scan_var = tk.IntVar()
        scan_var.set(10)
        nite_var = tk.IntVar()
        nite_var.set(0)

        maxp_e = tk.Entry(frame, width=6, textvariable=maxp_var)
        minp_e = tk.Entry(frame, width=6, textvariable=minp_var)
        step_e = tk.Entry(frame, width=6, textvariable=step_var)
        filen_e = tk.Entry(frame, width=6, textvariable=filen_var)
        mtime_e = tk.Entry(frame, width=6, textvariable=mtime_var)
        utime_e = tk.Entry(frame, width=6, textvariable=utime_var)
        scan_e = tk.Entry(frame, width=6, textvariable=scan_var)
        nite_e = tk.Entry(frame, width=6, textvariable=nite_var,
                          state='disabled')
        maxp_e.grid(row=2, column=1, sticky='nse')
        minp_e.grid(row=3, column=1, sticky='nse')
        step_e.grid(row=4, column=1, sticky='nse')
        filen_e.grid(row=5, column=1, sticky='nse')
        mtime_e.grid(row=6, column=1, sticky='nse')
        utime_e.grid(row=7, column=1, sticky='nse')
        scan_e.grid(row=8, column=1, sticky='nse')
        nite_e.grid(row=12, column=1, sticky='nse')
        # this function contains at minimum :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(min_pos=minp_var, max_pos=maxp_var,
                                      iteration=scan_var, duree = mtime_var, step = step_var, file_name = filen_var,
                                      progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')

        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=11, column=0, columnspan=2, sticky='nsew')

    def stop_experiment(self):
        self.running = False

    def update_std(self, graph, ydata, xdata, std1, std2, std3):
        std = np.std(ydata, axis=0)
        xdata = np.mean(xdata, axis=0)
        ymean = np.mean(ydata, axis=0)
        std1.remove()
        std1 = graph.axes.fill_between(xdata, ymean+std, ymean-std, alpha=0.6,
                                       interpolate=True, step='mid')
        std2.remove()
        std2 = graph.axes.fill_between(xdata, ymean+2*std, ymean-2*std, alpha=0.4,
                                       interpolate=True, step='mid')
        std3.remove()
        std3 = graph.axes.fill_between(xdata, ymean+3*std, ymean-3*std, alpha=0.2,
                                       interpolate=True, step='mid')

        return std1, std2, std3

    def start_experiment(self, min_pos=None, max_pos=None, iteration=None, duree = .1, step = 0.0001,
                         file_name = 'default', progress=None, update_time=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.running = True

        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        iteration = iteration.get()
        duree = duree.get()/1000
        step = step.get()/1000
        file_name = file_name.get()
        update_time = update_time.get()
        absc = []
        values = []
        filename = file_name + str(int(1000000 * step)) + '_nm_' + str(duree*1000) + '_ms_from_' + str(min_pos) + '_to_' + str(max_pos)

        if not self.PI.device:
            return

        if not max_pos and not min_pos and not iteration:
            return

        # Pipython :
        from pipython import GCSDevice
        from pipython import pitools
        # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))

        # This is a fail safe in case you don't know your device ( I should have done a manual for this...)
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return


        import time
        import sys
        import usb_1208LS as us

        chan = 1
        if self.DAQ.card == None:
            messagebox.showinfo(title='Error', message='DAQ device not connected')
            return
        gain = self.DAQ.card.BP_1_00V
        # Variable for the graph update
        last_gu = time.time()
        power_graph = self.graph_dict['Power']
        power_graph.axes.set_xlim([min_pos*1000, max_pos*1000])
        power_graph.Line.set_xdata([])
        power_graph.Line.set_ydata([])
        power_graph.Line.set_color('r')
        power_graph.Line.set_marker('.')
        power_graph.Line.set_markersize(2)
        power_graph.update_graph()
        # Standard deviation measure
        std1 = power_graph.axes.fill_between([0], [0], [0], alpha=0.6,
                                             interpolate=True, step='mid')
        std2 = power_graph.axes.fill_between([0], [0], [0], alpha=0.4,
                                             interpolate=True, step='mid')
        std3 = power_graph.axes.fill_between([0], [0], [0], alpha=0.2,
                                             interpolate=True, step='mid')
        #Add an option to have many measurements
        # ...
        # This section is to obtain average over many scan by creating a numpy array
        # that has dimension related to the number of step and the number of iteration
        nsteps = (max_pos - min_pos)/step
        values = np.zeros((iteration, int(nsteps)))
        absc_vals = np.zeros((iteration, int(nsteps)))
        value = np.zeros(nsteps)
        absc = np.zeros(nsteps)
        for i in range(iteration):
            self.PI.device.MOV(self.PI.axes, min_pos)
            time.sleep(.1)
            pos = min_pos
            for j in range(int(nsteps)):
                if not self.running:
                    break
                time.sleep(.1)
                value_step = np.zeros(0)
                start = time.time()
                while((time.time() - start) < duree):
                    value_step = np.append(value_step, self.DAQ.card.AIn(chan, gain))

                if progress:
                    progress['value'] = (i*nsteps + j)/(iteration*nsteps)
                    progress.update()

                pos += step
                self.PI.device.MOV(self.PI.axes, pos)

                value[j] = np.mean(value_step)
                pos_val = pos*1000
                absc[j] = pos_val

                if (time.time() - last_gu) > update_time:
                    power_graph.Line.set_xdata(absc)
                    power_graph.Line.set_ydata(value)
                    power_graph.update_graph()
                    last_gu = time.time()
            if not self.running:
                break
            values[i,:] = value
            absc_vals[i,:] = absc
            std1, std2, std3 = self.update_std(power_graph, values[:i,:], absc_vals[:i,:],
                                               std1, std2, std3)
            power_graph.update_graph()

        if not self.running:
            self.PI.device.MOV(self.PI.axes, min_pos)
            time.sleep(.1)
            answ = messagebox.askyesno(title='INFO', message='Experiment was'+
                                       'aborted./n Do you want to save your Data?')
            if answ:
                file_data = np.array([absc_vals[:i,:], values[:i, :]])
                np.save('measurements/' + filename, file_data)
        else:
            self.PI.device.MOV(self.PI.axes, min_pos)
            time.sleep(.1)
            ave_vals = np.mean(values, axis=0)
            ave_absc = np.mean(absc_vals, axis=0)
            power_graph.Line.set_xdata(ave_absc)
            power_graph.Line.set_ydata(ave_vals)
            power_graph.update_graph()
            messagebox.showinfo(title='INFO', message='Measurements is done.')
            file_data = np.array([absc_vals, values])
            np.save('measurements/' + filename, file_data)

        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'


class Electro_Optic_Sampling_ZeroDelay:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage

        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
                # 
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-863.11',
                                                                                   exp_dependencie=True))
                # 
                
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(77.5)
        vel_var.set(1)
        min_var.set(75)
        max_var.set(80)
        step_var.set(1000)
        utime_var.set(1)

        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=2, column=0, sticky='nsw')
        pos_e.grid(row=2, column=1, sticky='nse')
        vel_lbl.grid(row=3, column=0, sticky='nsw')
        vel_e.grid(row=3, column=1, sticky='nse')
        param_lbl.grid(row=4, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=5, column=0, sticky='nsw')
        min_e.grid(row=5, column=1, sticky='nse')
        max_lbl.grid(row=6, column=0, sticky='nsw')
        max_e.grid(row=6, column=1, sticky='nse')
        step_lbl.grid(row=7, column=0, sticky='nsw')
        step_e.grid(row=7, column=1, sticky='nse')
        utime_lbl.grid(row=8, column=0, sticky='nsw')
        utime_e.grid(row=8, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=11, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(vel_var))

        # this function contains at minimum :

        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'       
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectro']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        # Temporary Spectrometer things
        cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_spectrometer(self))
        cons_b.grid(row=13, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(10)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=14, column=0, sticky='nsw')
        inte_e.grid(row=14, column=1,sticky='nse')
        minwl_lbl = tk.Label(frame, text = 'min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'max wl for integration(nm)')
        minwl_var = tk.DoubleVar()
        maxwl_var = tk.DoubleVar()
        minwl_var.set(350)
        maxwl_var.set(500)
        minwl_e = tk.Entry(frame, width = 6, textvariable = minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = maxwl_var)
        minwl_lbl.grid(row=15, column=0, sticky='nsw')
        maxwl_lbl.grid(row=16, column=0, sticky='nsw')
        minwl_e.grid(row=15, column=1, sticky='nse')
        maxwl_e.grid(row=16, column=1, sticky='nse')
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=19,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=20,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=21,column=0,sticky='nsew')
        
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, minwl=minwl_var, maxwl=maxwl_var))
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=12, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=17, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=18, column=0, sticky='nsew')
        
        
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        if self.PI.device:
            self.start_button['state'] = 'normal'
        
        
        
        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None,
                         inte_time=None, minwl=None, maxwl=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()/1000
        update_time = update_time.get()

            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))

            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)

        # Variables for the graph update
        Si = np.zeros(nsteps+1)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()

        
            # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        Signal_graph = self.graph_dict['Signal']
        Signal_graph.axes.set_xlim([2*min_pos,2*max_pos])
        Signal_graph.axes.set_ylim([0,1])
        minwl = minwl.get()
        maxwl = maxwl.get()
        
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            
            # Acquire spectrum and plot graph 
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            wl_crop = wl[(wl>minwl)&(wl<maxwl)]
            S_crop = S[(wl>minwl)&(wl<maxwl)]
            Si[i] = np.trapz(S_crop,wl_crop) 
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                #Spectro signal and integrated signal
                spectro_graph.Line.set_xdata(wl)
                spectro_graph.Line.set_ydata(S)
                spectro_graph.update_graph()
                Signal_graph.Line.set_xdata(2*pos[:i])
                Signal_graph.Line.set_ydata(Si[:i]/np.max(Si))
                Signal_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(77.5)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(77.5)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            Signal_graph.Line.set_xdata(2*pos)
            Signal_graph.Line.set_ydata(Si/np.max(Si))
            Signal_graph.update_graph()
            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')

        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        
        
        
class CHI3_Sampling_ZeroDelay:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage

        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
                # 
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-863.12',
                                                                                   exp_dependencie=True))
                # 
                
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(52.295)
        vel_var.set(1)
        min_var.set(52.27)
        max_var.set(52.31)
        step_var.set(1)
        utime_var.set(1)

        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=2, column=0, sticky='nsw')
        pos_e.grid(row=2, column=1, sticky='nse')
        vel_lbl.grid(row=3, column=0, sticky='nsw')
        vel_e.grid(row=3, column=1, sticky='nse')
        param_lbl.grid(row=4, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=5, column=0, sticky='nsw')
        min_e.grid(row=5, column=1, sticky='nse')
        max_lbl.grid(row=6, column=0, sticky='nsw')
        max_e.grid(row=6, column=1, sticky='nse')
        step_lbl.grid(row=7, column=0, sticky='nsw')
        step_e.grid(row=7, column=1, sticky='nse')
        utime_lbl.grid(row=8, column=0, sticky='nsw')
        utime_e.grid(row=8, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=11, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(vel_var))

        # this function contains at minimum :

        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'       
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectro']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        # Temporary Spectrometer things
        cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_spectrometer(self))
        cons_b.grid(row=13, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(10)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=14, column=0, sticky='nsw')
        inte_e.grid(row=14, column=1,sticky='nse')
        minwl_lbl = tk.Label(frame, text = 'min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'max wl for integration(nm)')
        minwl_var = tk.DoubleVar()
        maxwl_var = tk.DoubleVar()
        minwl_var.set(350)
        maxwl_var.set(500)
        minwl_e = tk.Entry(frame, width = 6, textvariable = minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = maxwl_var)
        minwl_lbl.grid(row=15, column=0, sticky='nsw')
        maxwl_lbl.grid(row=16, column=0, sticky='nsw')
        minwl_e.grid(row=15, column=1, sticky='nse')
        maxwl_e.grid(row=16, column=1, sticky='nse')
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=19,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=20,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=21,column=0,sticky='nsew')
        
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, minwl=minwl_var, maxwl=maxwl_var))
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=12, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=17, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=18, column=0, sticky='nsew')
        
        self.save_button = tk.Button(frame, text='Save trace', state='disabled',width=18,
                                        command=lambda: self.save())
        self.save_button.grid(row=22,column=0,sticky='nsew')
        
    def save(self):
        
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(timeStamp+'_autocorrelation',wavelength = self.wl_crop ,position = self.pos,autocorr = self.Si)
         
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        if self.PI.device:
            self.start_button['state'] = 'normal'
        
        
        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None,
                         inte_time=None, minwl=None, maxwl=None):

        self.save_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()/1000
        update_time = update_time.get()

            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))

            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        self.pos = np.zeros(nsteps+1)
        # Variables for the graph update
        self.Si = np.zeros(nsteps+1)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()

        
            # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        Signal_graph = self.graph_dict['Signal']
        Signal_graph.axes.set_xlim([2*min_pos,2*max_pos])
        Signal_graph.axes.set_ylim([0,1])
        minwl = minwl.get()
        maxwl = maxwl.get()
        
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            self.pos[i] = self.PI.get_position()
            
            # Acquire spectrum and plot graph 
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            self.wl_crop = wl[(wl>minwl)&(wl<maxwl)]
            S_crop = S[(wl>minwl)&(wl<maxwl)]
            self.Si[i] = np.trapz(S_crop,self.wl_crop) 
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(self.pos[:i])
                scan_graph.update_graph()
                #Spectro signal and integrated signal
                spectro_graph.Line.set_xdata(wl)
                spectro_graph.Line.set_ydata(S)
                spectro_graph.update_graph()
                Signal_graph.Line.set_xdata(2*self.pos[:i])
                # Signal_graph.Line.set_ydata(self.Si[:i])
                Signal_graph.Line.set_ydata(self.Si[:i]/np.max(self.Si))
                Signal_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(1)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(50)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(1)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(50)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(self.pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            Signal_graph.Line.set_xdata(2*self.pos)
            Signal_graph.Line.set_ydata(self.Si/np.max(self.Si))
            Signal_graph.update_graph()
            
            dp = np.std(self.pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')

        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        
        
        
        
class FROG:
    # This class is implicitly called in the main frame
    """
    This is a class to create the user interface required to run a FROG experiment.
    It allows to control and read a spectrometer, control a PI stage, and then
    run an experiment synchronizing the movement of the stage and the spectra acquisition.
    
    Attributes:
        
        
    """

    def __init__(self, mainf = None):
        """
        This is the constructor for the FROG class.
        Parameters:
            
        """
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        """
        The frame is created here, i.e. the labels, boxes and buttons are
        defined here.
        """
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (um):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (um):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (um):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
                # 
        
        # Define buttons and their action
                # Pi Stage
        self.con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: connect_stage(self))
                # 
                
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        #vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(0)
        #vel_var.set(1)
        min_var.set(-20)
        max_var.set(20)
        step_var.set(1)
        utime_var.set(1)
        
        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        #vel_e = tk.Entry(frame, width = 6, textvariable = vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)
        
        # Define position of all objects on the grid
                # PI stage
        self.con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=2, column=0, sticky='nsw')
        pos_e.grid(row=2, column=1, sticky='nse')
        #vel_lbl.grid(row=3, column=0, sticky='nsw')
        #vel_e.grid(row=3, column=1, sticky='nse')
        param_lbl.grid(row=4, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=5, column=0, sticky='nsw')
        min_e.grid(row=5, column=1, sticky='nse')
        max_lbl.grid(row=6, column=0, sticky='nsw')
        max_e.grid(row=6, column=1, sticky='nse')
        step_lbl.grid(row=7, column=0, sticky='nsw')
        step_e.grid(row=7, column=1, sticky='nse')
        utime_lbl.grid(row=8, column=0, sticky='nsw')
        utime_e.grid(row=8, column=1, sticky='nse')
                # 
        
        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=11, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage[]{}
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        #vel_e.bind('<Return>', lambda e: self.PI.set_velocity(vel_var))
        
        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'
            self.cons_b['state'] = 'disabled'
        
        def connect_stage(self):
            self.PI.connect_identification(dev_name='E-816',exp_dependencie=True)
            self.con_b['state'] = 'disabled'
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectrometer']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        # Temporary Spectrometer things
        self.cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_spectrometer(self))
        self.cons_b.grid(row=13, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(10)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=14, column=0, sticky='nsw')
        inte_e.grid(row=14, column=1,sticky='nse')
        minwl_lbl = tk.Label(frame, text = 'min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'max wl for integration(nm)')
        minwl_var = tk.DoubleVar()
        maxwl_var = tk.DoubleVar()
        minwl_var.set(350)
        maxwl_var.set(500)
        minwl_e = tk.Entry(frame, width = 6, textvariable = minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = maxwl_var)
        minwl_lbl.grid(row=15, column=0, sticky='nsw')
        maxwl_lbl.grid(row=16, column=0, sticky='nsw')
        minwl_e.grid(row=15, column=1, sticky='nse')
        maxwl_e.grid(row=16, column=1, sticky='nse')
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=19,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=20,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=21,column=0,sticky='nsew')
        
        # Start & stop buttons :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, minwl=minwl_var, maxwl=maxwl_var))
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=12, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=17, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=18, column=0, sticky='nsew')
        
        
        self.save_button = tk.Button(frame, text='Save trace', state='disabled',width=18,
                                        command=lambda: self.save())
        self.save_button.grid(row=22,column=0,sticky='nsew')
        
        autocorr_lbl = tk.Label(frame, text = 'Autocorrelation FWHM [fs]')
        self.autocorr_var = tk.DoubleVar()
        self.autocorr_var.set(0)
        self.autocorr_e = tk.Entry(frame, width = 6, textvariable = self.autocorr_var, state = 'disabled')
        autocorr_lbl.grid(row=23, column=0, sticky='nsw')
        self.autocorr_e.grid(row=23, column=1, sticky='nse')
        

    def adjust_2dgraph(self):#, step=None):
# =============================================================================
#         step = step.get()
#         if step == 0:
#             step=1
# =============================================================================
        try:
             wl = len(self.Spectro.spectro.wavelengths())
        except:
            return
        
        parent2d = self.graph_dict["FROG trace"].parent
        self.graph_dict["FROG trace"].destroy_graph()
        #print(wl, step)
        self.graph_dict["FROG trace"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size= np.transpose(self.trace).shape)
        trace = (self.trace-np.min(self.trace))
        trace = trace/np.max(trace)
        self.graph_dict["FROG trace"].change_data(np.transpose(trace),False)
        self.graph_dict["FROG trace"].im.set_extent((self.timeDelay[0],self.timeDelay[-1],self.wl_crop[-1],self.wl_crop[0]))
        aspectRatio = abs((self.timeDelay[-1]-self.timeDelay[0])/(self.wl_crop[0]-self.wl_crop[-1]))
        self.graph_dict["FROG trace"].axes.set_aspect(aspectRatio)
        self.graph_dict["FROG trace"].axes.set_xlabel('Delay [fs]')
        self.graph_dict["FROG trace"].axes.set_ylabel('Wavelengths [nm]')
        cbar = self.graph_dict["FROG trace"].Fig.colorbar(self.graph_dict["FROG trace"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["FROG trace"].update_graph()
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        if self.PI.device:
            self.start_button['state'] = 'normal'
        
    def save(self):
        
        
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(timeStamp+'_FROG_trace_pythonformat',wavelengths = self.wl_crop,time = self.timeDelay,trace = self.trace)
        
        np.savetxt(timeStamp+'_FROG_trace_matlabformat'+'_M.dat', self.trace, fmt='%.18e', delimiter='\t', newline='\n')       
        np.savetxt(timeStamp+'_FROG_trace_matlabformat'+'_L.dat', self.wl_crop, fmt='%.18e', delimiter='\t', newline='\n')  
        np.savetxt(timeStamp+'_FROG_trace_matlabformat'+'_T.dat', self.timeDelay, fmt='%.18e', delimiter='\t', newline='\n')
        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None,
                         inte_time=None, minwl=None, maxwl=None):

        self.save_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        #self.update_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True
        
        # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage
            
            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()
        update_time = update_time.get()
        
            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return
        
            # Getting the max and min possible value of the device
        if self.PI.dev_name == 'E-816':
            maxp = 250
            minp = -250
        else:
            maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
            minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))
        
            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return
            
            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        Si = np.zeros(nsteps+1)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        
            # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        Signal_graph = self.graph_dict['Autocorrelation']
        Signal_graph.axes.set_xlim([2*min_pos*1e-6/299792458*1e15,2*max_pos*1e-6/299792458*1e15])
        Signal_graph.axes.set_ylim([0,1])
        minwl = minwl.get()
        maxwl = maxwl.get()
        
        self.wl_crop = wl[(wl>minwl)&(wl<maxwl)]
        self.trace = np.zeros((nsteps+1,self.wl_crop.shape[0]))
        
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            
            # Acquire spectrum and plot graph 
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            wl_crop = wl[(wl>minwl)&(wl<maxwl)]
            S_crop = S[(wl>minwl)&(wl<maxwl)]
            Si[i] = np.trapz(S_crop,wl_crop) 
            self.trace[i] = S_crop
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                #Spectro signal and integrated signal
                spectro_graph.Line.set_xdata(wl)
                spectro_graph.Line.set_ydata(S)
                spectro_graph.update_graph()
                Signal_graph.Line.set_xdata(2*pos[:i]*1e-6/299792458*1e15)
                Signal_graph.Line.set_ydata(Si[:i]/np.max(Si))
                Signal_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break       
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            Signal_graph.Line.set_xdata(2*pos*1e-6/299792458*1e15)
            Signal_graph.Line.set_ydata(Si/np.max(Si))
            Signal_graph.update_graph()
            
            
            dp = np.std(pos-move)/1000
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
        
        # Going back to initial state
        self.running = False
        self.timeDelay = 2*pos*1e-6/299792458*1e15
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        #self.update_button['state'] = 'normal'
        self.adjust_2dgraph()
        
        autocorr = Si - np.min(Si)
        autocorr = autocorr/np.max(autocorr)
        
        T = self.timeDelay[-1] - self.timeDelay[0]
        dt = 0.025
        t = np.linspace(self.timeDelay[0],self.timeDelay[-1],int(T/dt))
        
        sig = np.interp(t,self.timeDelay,autocorr)
        
        t0 = t[sig>=0.5][0]
        t1 = t[sig>=0.5][-1]
        self.autocorr_var.set(round(abs(t1-t0),1))
        
        
        
        
        
class TwoDSI:
    # This class is implicitly called in the main frame
    """
    This is a class to create the user interface required to run a FROG experiment.
    It allows to control and read a spectrometer, control a PI stage, and then
    run an experiment synchronizing the movement of the stage and the spectra acquisition.
    
    Attributes:
        
        
    """

    def __init__(self, mainf = None):
        """
        This is the constructor for the FROG class.
        Parameters:
            
        """
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        """
        The frame is created here, i.e. the labels, boxes and buttons are
        defined here.
        """
        # Define labels
        
        step1_lbl = tk.Label(frame, text = 'Step 1: Connect spectro & piezo')
        
        genCtrl_lbl = tk.Label(frame, text = 'Step 2: Setup spectro & piezo')
        pos_lbl = tk.Label(frame, text = 'Go to position (um):')
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        minwl_lbl = tk.Label(frame, text = 'Min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'Max wl for integration(nm)')
        utime_lbl = tk.Label(frame, text='Update figures after [s]:')
        
        step2_lbl = tk.Label(frame, text = 'Step 3: Block fixed stage & optimize signal')
        
        step3_lbl = tk.Label(frame, text = 'Step 4: Block piezo stage & optimize signal')
        average_lbl = tk.Label(frame, text = 'Averaging:')
        
        step4_lbl = tk.Label(frame, text = 'Step 5: Block fixed stage & calibrate shear')
        min_lbl = tk.Label(frame, text = 'Min. pos. (um):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (um):')
        stepsize4_lbl = tk.Label(frame, text = 'Step size (um):')
        
        step5_lbl = tk.Label(frame, text = 'Step 6: Unblock all beams & measure')
        minShear_lbl = tk.Label(frame, text = 'Min. shear (THz):')
        maxShear_lbl = tk.Label(frame, text = 'Max. shear (THz):')
        shear_lbl = tk.Label(frame, text = 'Shear freq. (THz):')
        scanLength_lbl = tk.Label(frame, text = 'Scan length (um):')
        stepsize5_lbl = tk.Label(frame, text = 'Step size (um):')
        
        
                # 
        
        # Define buttons and their action
        self.con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: connect_stage(self))
        self.cons_b = tk.Button(frame, text='Connect spectrometer',
                                command=lambda: connect_spectrometer(self))
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.startShear_button = tk.Button(frame, text='Measure shear', state='disabled', width=18,
                                      command=lambda: self.start_shearMeasurement(max_pos=max_var, min_pos=min_var, step=step4_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, minwl=minwl_var, maxwl=maxwl_var))
        self.stopShear_button = tk.Button(frame, text='Stop shear measurement', state='disabled', width=18,
                                     command=lambda: self.stop_shearMeasurement())
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(shear=shear_var, scanLength=scanLength_var, minShear = self.minShear, maxShear=self.maxShear, step=step5_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, minwl=minwl_var, maxwl=maxwl_var))
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.saveRef_button = tk.Button(frame, text='Save reference', state='disabled',width=18,
                                        command=lambda: self.saveRef())
        self.saveRef2_button = tk.Button(frame, text='Save reference', state='disabled',width=18,
                                        command=lambda: self.saveRef2(average = average_var))
        self.save_button = tk.Button(frame, text='Save trace', state='disabled',width=18,
                                        command=lambda: self.save())
        
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step4_var = tk.DoubleVar()
        shear_var = tk.DoubleVar()
        self.minShear_var = tk.DoubleVar()
        self.maxShear_var = tk.DoubleVar()
        scanLength_var = tk.DoubleVar()
        step5_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        inte_var = tk.IntVar()
        minwl_var = tk.DoubleVar()
        maxwl_var = tk.DoubleVar()
        average_var = tk.IntVar()
        average_var.set(1)
        minwl_var.set(350)
        maxwl_var.set(500)
        inte_var.set(10)
        pos_var.set(0)
        min_var.set(-20)
        max_var.set(20)
        step4_var.set(1)
        shear_var.set(3)
        scanLength_var.set(3)
        step5_var.set(0.03)
        utime_var.set(1)
        self.minShear_var.set(0)
        self.maxShear_var.set(0)
        
        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step4_e = tk.Entry(frame, width = 6, textvariable = step4_var)
        step5_e = tk.Entry(frame, width = 6, textvariable = step5_var)
        shear_e = tk.Entry(frame, width = 6, textvariable = shear_var)
        minShear_e = tk.Entry(frame, width = 6, textvariable = self.minShear_var, state = 'disabled')
        maxShear_e = tk.Entry(frame, width = 6, textvariable = self.maxShear_var, state = 'disabled')
        scanLength_e = tk.Entry(frame, width = 6, textvariable = scanLength_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        minwl_e = tk.Entry(frame, width = 6, textvariable = minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = maxwl_var)
        average_e = tk.Entry(frame, width = 6, textvariable = average_var)
        
        
        # Progress bar
        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar['maximum'] = 1
        
        
        
        
        # Define position of all objects on the grid
                # PI stage
        
        
        step1_lbl.grid(row = 0, column = 0, sticky = 'nsw')
        
        self.con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        
        self.cons_b.grid(row=2, column=0, columnspan=2, sticky='nsew')
        
        
        genCtrl_lbl.grid(row = 3, column = 0, sticky = 'nsw')
        
        pos_lbl.grid(row=4, column=0, sticky='nsw')
        pos_e.grid(row=4, column=1, sticky='nse')
        
        inte_lbl.grid(row=5, column=0, sticky='nsw')
        inte_e.grid(row=5, column=1,sticky='nse')
        
        minwl_lbl.grid(row=6, column=0, sticky='nsw')
        minwl_e.grid(row=6, column=1, sticky='nse')
        
        maxwl_lbl.grid(row=7, column=0, sticky='nsw')
        maxwl_e.grid(row=7, column=1, sticky='nse')
        
        utime_lbl.grid(row=8, column=0, sticky='nsw')
        utime_e.grid(row=8, column=1, sticky='nse')
        
        self.spectro_start_button.grid(row=9, column=0, sticky='nsew')
        
        self.dark_button.grid(row=10,column=0,sticky='nsew')
        
        self.sub_dark_button.grid(row=11,column=0,sticky='nsew')
        
        self.rescale_button.grid(row=12,column=0,sticky='nsew')
        
        
        
        
        step2_lbl.grid(row = 13, column = 0, sticky = 'nsw')
        
        self.saveRef_button.grid(row=14, column=0, columnspan=2, sticky='nsew')
        
        
        step3_lbl.grid(row = 15, column = 0, sticky = 'nsw')
        
        average_lbl.grid(row = 16, column = 0, sticky = 'nsw')
        average_e.grid(row = 16, column = 1, sticky = 'nsw')
    
        self.saveRef2_button.grid(row=17, column=0, columnspan=2, sticky='nsew')
        
        
        self.spectro_stop_button.grid(row=18, column=0,columnspan=2, sticky='nsew')
        
        
        step4_lbl.grid(row = 19, column = 0, sticky = 'nsw')
        
        min_lbl.grid(row=20, column=0, sticky='nsw')
        min_e.grid(row=20, column=1, sticky='nse')
        
        max_lbl.grid(row=21, column=0, sticky='nsw')
        max_e.grid(row=21, column=1, sticky='nse')
        
        stepsize4_lbl.grid(row=22, column=0, sticky='nsw')
        step4_e.grid(row=22, column=1, sticky='nse')
        
        self.startShear_button.grid(row=23, column=0, columnspan=2, sticky='nsew')
        
        self.stopShear_button.grid(row=24, column=0, columnspan=2, sticky='nsew')
        
        step5_lbl.grid(row = 25, column = 0, sticky = 'nsw')
        
        
        minShear_lbl.grid(row=26, column=0, sticky='nsw')
        minShear_e.grid(row=26, column=1, sticky='nse')
        maxShear_lbl.grid(row=27, column=0, sticky='nsw')
        maxShear_e.grid(row=27, column=1, sticky='nse')
        
        shear_lbl.grid(row=28, column=0, sticky='nsw')
        shear_e.grid(row=28, column=1, sticky='nse')
        
        scanLength_lbl.grid(row=29, column=0, sticky='nsw')
        scanLength_e.grid(row=29, column=1, sticky='nse')
        
        
        stepsize5_lbl.grid(row=30, column=0, sticky='nsw')
        step5_e.grid(row=30, column=1, sticky='nse')
        
        
        self.start_button.grid(row=31, column=0, columnspan=2, sticky='nsew')
        
        self.stop_button.grid(row=32, column=0, columnspan=2, sticky='nsew')
        
        
        
        p_bar.grid(row=33, column=0, sticky='nsew', columnspan=2)
        
        
        
        self.save_button.grid(row=34,column=0,sticky='nsew')
        
        
        
        # Select a key and its effect when pressed in an entry box
            # PI stage[]{}
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        
        # Start & stop buttons :
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        
            # For spectrometer :
        
        self.plotRefSpectrum = False
        self.shearCalculated = False
        self.allowShearMeasurement = False
        
        
        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'
            self.cons_b['state'] = 'disabled'
        
        def connect_stage(self):
            self.PI.connect_identification(dev_name='E-816',exp_dependencie=True)
            self.con_b['state'] = 'disabled'
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectrometer']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        
    def start_shearMeasurement(self,max_pos, min_pos, step, progress, update_time,
                                            inte_time, minwl, maxwl):
        
        self.spectro_start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.stopShear_button['state'] = 'normal'
        self.startShear_button['state'] = 'disabled'
        self.running = True
        
         # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage
            
            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()
        update_time = update_time.get()
        minwl = minwl.get()
        maxwl = maxwl.get()
        
            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return
        
            # Getting the max and min possible value of the device
        if self.PI.dev_name == 'E-816':
            maxp = 250
            minp = -250
        else:
            maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
            minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))
        
            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return
            
            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        Si = np.zeros(nsteps+1)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        
            # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        
        
        
        self.wl_crop = wl[(wl>minwl)&(wl<maxwl)]
        self.shearTrace = np.zeros((nsteps+1,self.wl_crop.shape[0]))
        
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            
            # Acquire spectrum and plot graph 
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            wl_crop = wl[(wl>minwl)&(wl<maxwl)]
            S_crop = S[(wl>minwl)&(wl<maxwl)]
            Si[i] = np.trapz(S_crop,wl_crop) 
            self.shearTrace[i] = S_crop
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                #Spectro signal and integrated signal
                spectro_graph.Line.set_xdata(wl)
                spectro_graph.Line.set_ydata(S)
                spectro_graph.update_graph()
                
                
                last_gu = time.time()
            if not self.running:
                break       
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            
            
            dp = np.std(pos-move)/1000
            
                
            self.shearPos = pos
            self.shearWL = wl_crop
            self.adjust_sheargraph()
            self.start_button['state'] = 'normal'
            
            
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
            
            
            
            
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stopShear_button['state'] = 'disabled'
        self.startShear_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        #self.update_button['state'] = 'normal'
        
        
        
        
        
        return
    
    def find_shear(self,wavelengths_copy, upconvPowerSpectrum, movingMirrorData, movingMirror_Z):
        """ Calculate shear frequency as a function of stage position,
        and take its value at the middle position as constant approximation """
        
        C =299792458
        wavelengths = wavelengths_copy*1e-9
        
        
        # Normalize spectra to max of one
        upconvPowerSpectrum = upconvPowerSpectrum / np.max(upconvPowerSpectrum)
        
        maxValues = np.max(movingMirrorData, axis = 1)
        tmp = wavelengths.shape[0]
        maxValues = np.transpose( np.tile(maxValues, (tmp,1)) )
        movingMirrorData = movingMirrorData / maxValues
        
    
    
        # Convert wavelengths to frequencies
        frequencies = C / wavelengths
        
        frequencies = np.flip(frequencies) # Flipping from low to high frequencies
        upconvPowerSpectrum = np.flip(upconvPowerSpectrum)
        movingMirrorData = np.flip(movingMirrorData,axis = 1)
        
        # Interpolate to a linear spacing of frequencies
        # Choice of datapoint position strongly affect results, here I am copying Matlab
        # need to check if another strategy would work better
        Df = frequencies[-1] - frequencies[0]
        df = np.max( np.diff(frequencies) ) / 16
        N = round(Df / df)
        linFreqs = np.linspace(frequencies[-1]-(N-1)*df, frequencies[-1], N )
        upconvPowerSpectrum = np.interp(linFreqs, frequencies, upconvPowerSpectrum)
        
        
        newMovingMirrorData = np.zeros((movingMirrorData.shape[0], linFreqs.shape[0]))
        
        for ii in range( movingMirrorData.shape[0] ):
            newMovingMirrorData[ii,:] = np.interp(linFreqs, frequencies, movingMirrorData[ii,:])
        
        movingMirrorData = newMovingMirrorData
        frequencies = linFreqs
        
        
        
        #crossCorr = np.zeros( (movingMirrorData.shape[0], movingMirrorData.shape[1]))
        crossCorr = np.zeros( (movingMirrorData.shape[0], movingMirrorData.shape[1]*2-1))
    
        lags = np.zeros_like(crossCorr)
        shearMap = np.zeros( movingMirrorData.shape[0] )
        
        for ii in range( movingMirrorData.shape[0] ):
            #lags[ii,:], crossCorr[ii,:] =fq.ezcorr(frequencies, movingMirrorData[ii,:], upconvPowerSpectrum) 
            #shearMap[ii] = lags[ii,:][ crossCorr[ii,:] == np.max(crossCorr[ii,:]) ]
            crossCorr[ii,:] =  np.correlate(movingMirrorData[ii,:], upconvPowerSpectrum,'full')
            maxId = np.argmax(crossCorr[ii,:])
            peakFreq = -(N - (maxId+1))*df
            lags = -(N - np.linspace(1,2*N-1,2*N-1) ) *df
            
            
            x,y = fq.ezdiff(lags, crossCorr[ii,:])
            
            f = interp.interp1d(x, y, kind = 'cubic')
            
            err = 1
            threshold = 1e-5
            maxIter = 1000
            nIter = 0
            x0 = peakFreq - 5*df
            x1 = peakFreq + 5*df
            
            while err > threshold:
                nIter += 1
                if nIter > maxIter:
                    break
                
                if x1<lags[0]:
                    x1 = lags[0]
                if x1>lags[-1]:
                    x1 = lags[-1]
                    
                f0 = f(x0)
                f1 = f(x1)
                dfdx = (f1-f0) / (x1 - x0)
                b = f0 - dfdx*x0
                
                x0 = x1
                x1 = -b/dfdx
                err = abs((x1-x0)/x0)
                
                
                 
            
            shearMap[ii] = x1# -(N - (maxId+1))*df
        
        shearMap /= 1e12
        self.shearFit = np.polyfit(movingMirror_Z,shearMap, 1)
        self.shearMap = shearMap
    
    
    
    def stop_shearMeasurement(self):
        
        self.running = False
        self.spectro_start_button['state'] = 'normal'
        self.stopShear_button['state'] = 'normal'
        self.startShear_button['state'] = 'disabled'
        
        
        return
    
    
    def saveRef(self):
        
        self.refSpectrum = self.Spectro.get_intensities()
        if self.plotRefSpectrum is False:
            self.plotRefSpectrum = True
            self.graph_dict['Spectrometer'].LineRef, =  self.graph_dict['Spectrometer'].axes.plot([], [])
            
        return
    
    def saveRef2(self, average):
        
        average = average.get()
        if average < 1:
            average = 1
        if average > 100:
            average = 100
        
        self.allowShearMeasurement = True
        
        self.refSpectrum = np.zeros((average,self.Spectro.get_intensities().shape[0]))
        for ii in range(average):
            self.refSpectrum[ii,:] = self.Spectro.get_intensities()
        self.refSpectrum = np.mean(self.refSpectrum,0)
        
        if self.plotRefSpectrum is False:
            self.plotRefSpectrum = True
            self.graph_dict['Spectrometer'].LineRef, =  self.graph_dict['Spectrometer'].axes.plot([], [])
            
        return
    
    
    

    def adjust_sheargraph(self):
# =============================================================================
#         try:
#              wl = len(self.Spectro.spectro.wavelengths())
#         except:
#             return
# =============================================================================
        
        if not self.shearCalculated:
            self.graph_dict["Shear calc. curve"].LineFit, =  self.graph_dict["Shear calc. curve"].axes.plot([], [])
        
        wl = self.Spectro.spectro.wavelengths()
        refSpectrum = self.refSpectrum[(wl >= self.shearWL[0])&(wl<=self.shearWL[-1])]
        self.find_shear(self.shearWL, refSpectrum, self.shearTrace, self.shearPos)
        
        shearFitCurve = np.polyval(self.shearFit,self.shearPos)
        self.shearCalculated = True
        
        
        parent2d = self.graph_dict["Shear reference"].parent
        self.graph_dict["Shear reference"].destroy_graph()
        #print(wl, step)
        self.graph_dict["Shear reference"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size=self.shearTrace.shape)
        trace = (self.shearTrace-np.min(self.shearTrace))
        trace = trace/np.max(trace)
        self.graph_dict["Shear reference"].change_data(trace,False)
        self.graph_dict["Shear reference"].im.set_extent((self.shearWL[0],self.shearWL[-1],self.shearPos[-1],self.shearPos[0]))
        aspectRatio = abs((self.shearWL[-1]-self.shearWL[0])/(self.shearPos[0]-self.shearPos[-1]))
        self.graph_dict["Shear reference"].axes.set_aspect(aspectRatio)
        self.graph_dict["Shear reference"].axes.set_xlabel('Wavelengths [nm]')
        self.graph_dict["Shear reference"].axes.set_ylabel('Delay [um]')
        cbar = self.graph_dict["Shear reference"].Fig.colorbar(self.graph_dict["Shear reference"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["Shear reference"].update_graph()
        
        shearFit_graph = self.graph_dict["Shear calc. curve"]
        shearFit_graph.axes.set_xlim([np.min(self.shearPos),np.max(self.shearPos)])
        shearFit_graph.axes.set_ylim([np.min(self.shearMap),np.max(self.shearMap)])
        shearFit_graph.Line.set_xdata(self.shearPos)
        shearFit_graph.Line.set_ydata(self.shearMap)
        
        shearFit_graph.LineFit.set_xdata(self.shearPos)
        shearFit_graph.LineFit.set_ydata(shearFitCurve)
        self.minShear = np.min(shearFitCurve)
        self.maxShear = np.max(shearFitCurve)
        self.minShear_var.set( np.round( self.minShear , 1) )
        self.maxShear_var.set( np.round( self.maxShear , 1) )
        shearFit_graph.update_graph()
        
        
        
    def adjust_2dsigraph(self):
        try:
             wl = len(self.Spectro.spectro.wavelengths())
        except:
            return
        
        parent2d = self.graph_dict["2DSI trace"].parent
        self.graph_dict["2DSI trace"].destroy_graph()
        #print(wl, step)
        self.graph_dict["2DSI trace"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size=self.twoDSITrace.shape)
        trace = (self.twoDSITrace-np.min(self.twoDSITrace))
        trace = trace/np.max(trace)
        self.graph_dict["2DSI trace"].change_data(trace,False)
        self.graph_dict["2DSI trace"].im.set_extent((self.twoDSIWL[0],self.twoDSIWL[-1],self.twoDSIPos[-1],self.twoDSIPos[0]))
        aspectRatio = abs((self.twoDSIWL[-1]-self.twoDSIWL[0])/(self.twoDSIPos[0]-self.twoDSIPos[-1]))
        self.graph_dict["2DSI trace"].axes.set_aspect(aspectRatio)
        self.graph_dict["2DSI trace"].axes.set_xlabel('Wavelengths [nm]')
        self.graph_dict["2DSI trace"].axes.set_ylabel('Stage position [um]')
        cbar = self.graph_dict["2DSI trace"].Fig.colorbar(self.graph_dict["2DSI trace"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["2DSI trace"].update_graph()
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.saveRef_button['state'] = 'normal'
        self.saveRef2_button['state'] = 'normal'
        self.startShear_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            if self.plotRefSpectrum:
                spectro_graph.LineRef.set_xdata(wl)
                spectro_graph.LineRef.set_ydata(self.refSpectrum)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal' 
        self.saveRef_button['state'] = 'disabled' 
        self.saveRef2_button['state'] = 'disabled'
        if self.PI.device:
            if self.shearCalculated:
                self.start_button['state'] = 'normal'
        if self.allowShearMeasurement:
            self.startShear_button['state'] = 'normal'
        
    def save(self):
        
        wl = self.Spectro.spectro.wavelengths()
        refSpectrum = self.refSpectrum[(wl >= self.shearWL[0])&(wl<=self.shearWL[-1])]
        
        if not np.all( self.shearWL == self.twoDSIWL ):
            messagebox.showinfo(title='INFO', message='Wavelengths integration range inconsistant between trace and shear calibration. Please repeat steps 5 & 6 without changing spectral range.')
            return
        
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(timeStamp+'_2DSI_data',wavelengths = self.shearWL,shearStagePosition = self.shearPos, shearTrace = self.shearTrace,upconvSpectrum = refSpectrum, twoDSIStagePosition = self.twoDSIPos, twoDSITrace = self.twoDSITrace)
        


        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'



    def start_experiment(self, shear=None, scanLength=None,minShear = None, maxShear = None, step = None, progress=None, update_time=None,
                         inte_time=None, minwl=None, maxwl=None):

        self.spectro_start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.startShear_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
         # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage
            
            # Parameters initialisation
        shear = shear.get()
        scanLength = scanLength.get()
        step = step.get()
        update_time = update_time.get()
        minwl = minwl.get()
        maxwl = maxwl.get()
        
        
        
        central_pos = (shear - self.shearFit[1])/self.shearFit[0]
        min_pos = central_pos - scanLength/2
        max_pos = central_pos + scanLength/2
        
        
            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return
        
            # Getting the max and min possible value of the device
        if self.PI.dev_name == 'E-816':
            maxp = 250
            minp = -250
        else:
            maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
            minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))
        
            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            
            self.stop_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.startShear_button['state'] = 'normal'
            self.spectro_start_button['state'] = 'normal'
            return
        
        if (shear < minShear) or (shear > maxShear):
            messagebox.showinfo(title='Error', message='Requested shear is outside of calibration range.')
                
            self.stop_button['state'] = 'disabled'
            self.start_button['state'] = 'normal'
            self.startShear_button['state'] = 'normal'
            self.spectro_start_button['state'] = 'normal'
            return
        
        
            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        Si = np.zeros(nsteps+1)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        
            # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        
        
        
        self.wl_crop = wl[(wl>minwl)&(wl<maxwl)]
        self.twoDSITrace = np.zeros((nsteps+1,self.wl_crop.shape[0]))
        
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            
            # Acquire spectrum and plot graph 
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            wl_crop = wl[(wl>minwl)&(wl<maxwl)]
            S_crop = S[(wl>minwl)&(wl<maxwl)]
            Si[i] = np.trapz(S_crop,wl_crop) 
            self.twoDSITrace[i] = S_crop
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                #Spectro signal and integrated signal
                spectro_graph.Line.set_xdata(wl)
                spectro_graph.Line.set_ydata(S)
                spectro_graph.update_graph()
                
                
                last_gu = time.time()
            if not self.running:
                break       
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(0)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            
            
            dp = np.std(pos-move)/1000
            
                
            self.twoDSIPos = pos
            self.twoDSIWL = wl_crop
            self.adjust_2dsigraph()
            self.save_button['state'] = 'normal'
            
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
            
            
            
            
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.startShear_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        #self.update_button['state'] = 'normal'
        
        
        
        
        
        return
        

class Electro_Optic_Sampling:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Zurich = mainf.Frame[1].Zurich
        self.plotRefSignal = False
        self.refSignal =[]
        self.refTime =[]
        self.refExists = False
        self.LogSpec = False
        self.phaseExists = False
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-863.11',
                                                                                   exp_dependencie=True))

        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        self.vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        self.wait_var = tk.IntVar()
        pos_var.set(77.5)
        self.vel_var.set(1)
        min_var.set(75)
        max_var.set(80)
        step_var.set(1000)
        utime_var.set(1)
        
        
        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = self.vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=4, column=0, sticky='nsw')
        pos_e.grid(row=4, column=1, sticky='nse')
        vel_lbl.grid(row=5, column=0, sticky='nsw')
        vel_e.grid(row=5, column=1, sticky='nse')
        param_lbl.grid(row=6, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=7, column=0, sticky='nsw')
        min_e.grid(row=7, column=1, sticky='nse')
        max_lbl.grid(row=8, column=0, sticky='nsw')
        max_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')
        utime_lbl.grid(row=11, column=0, sticky='nsw')
        utime_e.grid(row=11, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=13, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(self.vel_var))
            
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=12, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')   
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save())
        self.RefSignal_button = tk.Button(frame, text='Signal reference', state='disabled', command=lambda: self.SignalRef())
        self.RefSignal_button.grid(row=15, column=0, sticky='nsw')
        self.RefOff_button = tk.Button(frame, text='Ref ON/OFF', state='disabled',command=lambda: self.RemoveRef())
        self.RefOff_button.grid(row=15, column=1, sticky='nse')
        self.Log_button = tk.Button(frame, text='Log Spectrum ON/OFF', state='disabled',command=lambda: self.LogSpectrum())
        self.Log_button.grid(row=16, columnspan=2, sticky='nsew')
        self.save_button.grid(row=20, column=0, columnspan=2, sticky='nsew')
        self.wait = tk.Checkbutton(frame,text='Settling wait time', variable=self.wait_var)   
        self.wait.grid(row=10, column=0, columnspan=2, sticky='nsew')
    def save(self):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(timeStamp+'_EOS_measurement',time = self.t,signal = self.S)
        
    def LogSpectrum(self):
        if self.LogSpec is False:
            self.LogSpec = True
            LogAA = np.log(self.AA)
            self.graph_dict['Spectrum'].Line.set_ydata(LogAA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                LogAref = np.log(self.refSpec)
                self.graph_dict['Spectrum'].LineRef.set_ydata(LogAref)
            self.graph_dict['Spectrum'].axes.set_ylim([np.min(LogAA),1.2*np.max(LogAA)])
            self.graph_dict['Spectrum'].update_graph()
        elif self.LogSpec is True:
            self.LogSpec = False
            self.graph_dict['Spectrum'].Line.set_ydata(self.AA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                self.graph_dict['Spectrum'].LineRef.set_ydata(self.refSpec)
            self.graph_dict['Spectrum'].axes.set_ylim([1.2*np.min(self.AA),1.2*np.max(self.AA)])
            self.graph_dict['Spectrum'].update_graph()
            
    def SignalRef(self):
        if self.refExists is False:
            self.graph_dict['Signal'].LineRef, =  self.graph_dict['Signal'].axes.plot([], [])
            self.graph_dict['Spectrum'].LineRef, = self.graph_dict['Spectrum'].axes.plot([],[])
            self.refExists = True
        self.refSignal = self.S
        self.refTime = self.t
        self.refFreq = self.v
        self.refSpec = self.AA
        if self.plotRefSignal is False:
            self.plotRefSignal = True
        return
    def RemoveRef(self):
        if self.refExists is True:
            if self.plotRefSignal is True:    
                self.plotRefSignal = False
                self.graph_dict['Signal'].LineRef.set_xdata([])
                self.graph_dict['Signal'].LineRef.set_ydata([])
                self.graph_dict['Spectrum'].LineRef.set_xdata([])
                self.graph_dict['Spectrum'].LineRef.set_ydata([])
            elif self.plotRefSignal is False:
                self.plotRefSignal = True
                self.graph_dict['Signal'].LineRef.set_xdata(self.refTime)
                self.graph_dict['Signal'].LineRef.set_ydata(self.refSignal)
                self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
                if self.LogSpec is True:
                    self.graph_dict['Spectrum'].LineRef.set_ydata(np.log(self.refSpec))
                else:
                    self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Signal'].update_graph()
            self.graph_dict['Spectrum'].update_graph()
        return
    
    def Zurich_acquire(self):
        import time
        path = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/sample'
        path2 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/timeconstant'
        path3 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/order'
        tc= self.Zurich.info['daq'].getDouble(path2)
        order= self.Zurich.info['daq'].getDouble(path3)
        if self.wait_var.get() == 1:
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            if order == 1:
                Settling_time = 4.61*tc
            elif order == 2:
                Settling_time = 6.64*tc
            elif order == 3:
                Settling_time = 8.41*tc
            elif order == 4:
                Settling_time = 10.05*tc
            time.sleep(Settling_time)
        self.Zurich.info['daq'].subscribe(path)
        data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)


        try:
            data = data_set[path]['x']
#            print(data)
#            print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data
    
    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None):
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.RefSignal_button['state'] = 'disabled'
        self.RefOff_button['state'] = 'disabled'
        self.Log_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        import scipy
        import femtoQ.tools as fQ
        c = scipy.constants.c
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()/1000
        update_time = update_time.get()

            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))

            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        self.S = np.zeros(nsteps+1)
        self.t= np.zeros(nsteps+1)

        # Variables for the graph update
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        EOS_graph = self.graph_dict['Signal']
        EOS_graph.axes.set_ylim([-10,10])
        EOS_graph.axes.set_xlim([0, (max_pos-min_pos)*2/1000/c*1e15])
        EOS_graph.Line.set_xdata([])
        EOS_graph.Line.set_ydata([])
        if self.plotRefSignal is True:
            EOS_graph.LineRef.set_xdata(self.refTime)
            EOS_graph.LineRef.set_ydata(self.refSignal)
            EOS_graph.LineRef.set_linestyle('--')
            self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
            self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Spectrum'].LineRef.set_linestyle('--')
        EOS_graph.update_graph()
        self.graph_dict['Spectrum'].update_graph()
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            # Measure signal
            self.t[i] = (pos[i]-pos[0])*2/1000/c*1e15
            self.S[i] = np.mean(self.Zurich_acquire())*1000
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                EOS_graph.Line.set_xdata(self.t[:i])
                EOS_graph.Line.set_ydata(self.S[:i])
                EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
                EOS_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(77.5)
            self.PI.set_velocity(self.vel_var)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(77.5)
            self.PI.set_velocity(self.vel_var)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
            EOS_graph.Line.set_xdata(self.t)
            EOS_graph.Line.set_ydata(self.S)
            EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
            EOS_graph.update_graph()
            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
        
            # Display spectrum graph
            spec_t = self.t*1e-15
            t_sort, indices = np.unique(spec_t,return_index=True)
            S_sort = self.S[indices]
            func = interp.interp1d(t_sort, S_sort,kind='quadratic')
            t_interp = np.linspace(t_sort.min(),t_sort.max(),len(t_sort))
            E_interp = func(t_interp)
            self.v,self.A = fQ.ezfft(t_interp,E_interp)
            self.AA = np.abs(self.A)**2
            self.AA = self.AA/np.max(self.AA)
            self.v = self.v/1e12
            Spectrum_graph = self.graph_dict['Spectrum']
            Spectrum_graph.axes.set_ylim([0, 1.1*np.max(self.AA)])
            Spectrum_graph.axes.set_xlim([np.min(self.v), np.max(self.v)])
            Spectrum_graph.Line.set_xdata([self.v])
            Spectrum_graph.Line.set_ydata([self.AA])
            
            if self.phaseExists is False:
                        self.Phase_graph_ax = Spectrum_graph.axes.twinx()
                        self.LinePhase, = self.Phase_graph_ax.plot([],[],'m')
                        self.phaseExists = True
            phi = np.arctan2(self.A.imag,self.A.real)
            phi = np.unwrap(phi)
            a,b = np.polyfit(self.v,phi,deg=1,w=self.AA)
            slope = a*self.v+b
            phi = phi - slope
            self.Phase_graph_ax.set_ylim([-2*np.pi,2*np.pi])
            self.LinePhase.set_xdata(self.v)
            self.LinePhase.set_ydata([phi])
            self.LinePhase.set_linestyle(':')
            Spectrum_graph.update_graph()
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.RefSignal_button['state'] = 'normal'
        self.RefOff_button['state'] = 'normal'
        self.Log_button['state'] = 'normal'








class CHI3_Sampling:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Zurich = mainf.Frame[1].Zurich
        self.plotRefSignal = False
        self.refSignal =[]
        self.refTime =[]
        self.refExists = False
        self.LogSpec = False
        self.phaseExists = False
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        
        self.directory_var=tk.StringVar()
        
        
        self.directory_var.set('E:/Marco/Raw_data/EOS/')
        
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-863.12',
                                                                                   exp_dependencie=True))

        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        self.vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        self.wait_var = tk.IntVar()
        self.wait_var2 = tk.IntVar()
        
        pos_var.set(50)
        self.vel_var.set(1)
        min_var.set(49.8)
        max_var.set(50.4)
        step_var.set(1)
        utime_var.set(1)
        
    
        
        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = self.vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=4, column=0, sticky='nsw')
        pos_e.grid(row=4, column=1, sticky='nse')
        vel_lbl.grid(row=5, column=0, sticky='nsw')
        vel_e.grid(row=5, column=1, sticky='nse')
        param_lbl.grid(row=6, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=7, column=0, sticky='nsw')
        min_e.grid(row=7, column=1, sticky='nse')
        max_lbl.grid(row=8, column=0, sticky='nsw')
        max_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')
        utime_lbl.grid(row=11, column=0, sticky='nsw')
        utime_e.grid(row=11, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=13, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(self.vel_var))
            
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=12, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')   
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save())
        self.RefSignal_button = tk.Button(frame, text='Signal reference', state='disabled', command=lambda: self.SignalRef())
        self.RefSignal_button.grid(row=15, column=0, sticky='nsw')
        self.RefOff_button = tk.Button(frame, text='Ref ON/OFF', state='disabled',command=lambda: self.RemoveRef())
        self.RefOff_button.grid(row=15, column=1, sticky='nse')
        self.Log_button = tk.Button(frame, text='Log Spectrum ON/OFF', state='disabled',command=lambda: self.LogSpectrum())
        self.Log_button.grid(row=16, columnspan=2, sticky='nsew')
        self.save_button.grid(row=20, column=0, columnspan=2, sticky='nsew')
        self.wait = tk.Checkbutton(frame,text='Wait 1s', variable=self.wait_var)   
        self.wait.grid(row=21, column=0, columnspan=2, sticky='nsew')
        self.wait2 = tk.Checkbutton(frame,text='Wait 2s', variable=self.wait_var2)   
        self.wait2.grid(row=22, column=0, columnspan=2, sticky='nsew')
    def save(self):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(self.directory_var.get() + timeStamp+'_EOS_measurement',time = self.t,signal = self.S)
        
    def LogSpectrum(self):
        if self.LogSpec is False:
            self.LogSpec = True
            LogAA = np.log(self.AA)
            self.graph_dict['Spectrum'].Line.set_ydata(LogAA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                LogAref = np.log(self.refSpec)
                self.graph_dict['Spectrum'].LineRef.set_ydata(LogAref)
            self.graph_dict['Spectrum'].axes.set_ylim([np.min(LogAA),1.2*np.max(LogAA)])
            self.graph_dict['Spectrum'].update_graph()
        elif self.LogSpec is True:
            self.LogSpec = False
            self.graph_dict['Spectrum'].Line.set_ydata(self.AA)
            if ((self.refExists is True)&(self.plotRefSignal is True)):
                self.graph_dict['Spectrum'].LineRef.set_ydata(self.refSpec)
            self.graph_dict['Spectrum'].axes.set_ylim([1.2*np.min(self.AA),1.2*np.max(self.AA)])
            self.graph_dict['Spectrum'].update_graph()
            
    def SignalRef(self):
        if self.refExists is False:
            self.graph_dict['Signal'].LineRef, =  self.graph_dict['Signal'].axes.plot([], [])
            self.graph_dict['Spectrum'].LineRef, = self.graph_dict['Spectrum'].axes.plot([],[])
            self.refExists = True
        self.refSignal = self.S
        self.refTime = self.t
        self.refFreq = self.v
        self.refSpec = self.AA
        if self.plotRefSignal is False:
            self.plotRefSignal = True
        return
    def RemoveRef(self):
        if self.refExists is True:
            if self.plotRefSignal is True:    
                self.plotRefSignal = False
                self.graph_dict['Signal'].LineRef.set_xdata([])
                self.graph_dict['Signal'].LineRef.set_ydata([])
                self.graph_dict['Spectrum'].LineRef.set_xdata([])
                self.graph_dict['Spectrum'].LineRef.set_ydata([])
            elif self.plotRefSignal is False:
                self.plotRefSignal = True
                self.graph_dict['Signal'].LineRef.set_xdata(self.refTime)
                self.graph_dict['Signal'].LineRef.set_ydata(self.refSignal)
                self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
                if self.LogSpec is True:
                    self.graph_dict['Spectrum'].LineRef.set_ydata(np.log(self.refSpec))
                else:
                    self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Signal'].update_graph()
            self.graph_dict['Spectrum'].update_graph()
        return
    
    def Zurich_acquire(self):
        import time
        path = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/sample'
        path2 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/timeconstant'
        path3 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/order'
        tc= self.Zurich.info['daq'].getDouble(path2)
        # print
        order= self.Zurich.info['daq'].getDouble(path3)
        # if self.wait_var.get() == 1:
        #     # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
        #     if order == 1:
        #         Settling_time = 4.61*tc
        #     elif order == 2:
        #         Settling_time = 6.64*tc
        #     elif order == 3:
        #         Settling_time = 8.41*tc
        #     elif order == 4:
        #         Settling_time = 10.05*tc
        #     time.sleep(Settling_time)
        # self.Zurich.info['daq'].subscribe(path)
        # data_set = self.Zurich.info['daq'].poll(0.01,200,0,True)
        self.Zurich.info['daq'].subscribe(path)
        if self.wait_var.get() == 1:
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            data_set = self.Zurich.info['daq'].poll(1,100,0,True)
        # else:
        #     data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)
            
        if self.wait_var2.get() == 1:
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            data_set = self.Zurich.info['daq'].poll(2,100,0,True)
        # else:
        #     data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)
        if (self.wait_var.get() == 0 & self.wait_var2.get() == 0):
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)
        

        try:
            data = data_set[path]['x']
            # print(data)
            # print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data


    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None):
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.RefSignal_button['state'] = 'disabled'
        self.RefOff_button['state'] = 'disabled'
        self.Log_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        import scipy
        import femtoQ.tools as fQ
        c = scipy.constants.c
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()/1000
        update_time = update_time.get()

            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = self.PI.device.qTMX(self.PI.axes).get(str(self.PI.axes))
        minp = self.PI.device.qTMN(self.PI.axes).get(str(self.PI.axes))

            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your physik instrument device')
            return

            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        # move = np.linspace(min_pos, max_pos, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        self.S = np.zeros(nsteps+1)
        self.t= np.zeros(nsteps+1)

        # Variables for the graph update
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        EOS_graph = self.graph_dict['Signal']
        EOS_graph.axes.set_ylim([-10,10])
        EOS_graph.axes.set_xlim([0, (max_pos-min_pos)*2/1000/c*1e15])
        EOS_graph.Line.set_xdata([])
        EOS_graph.Line.set_ydata([])
        if self.plotRefSignal is True:
            EOS_graph.LineRef.set_xdata(self.refTime)
            EOS_graph.LineRef.set_ydata(self.refSignal)
            EOS_graph.LineRef.set_linestyle('--')
            self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
            self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Spectrum'].LineRef.set_linestyle('--')
        EOS_graph.update_graph()
        self.graph_dict['Spectrum'].update_graph()
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            # Measure signal
            self.t[i] = (pos[i]-pos[0])*2/1000/c*1e15
            self.S[i] = np.mean(self.Zurich_acquire())*1000
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                EOS_graph.Line.set_xdata(self.t[:i])
                EOS_graph.Line.set_ydata(self.S[:i])
                EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
                EOS_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(1)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(50)
            self.PI.set_velocity(self.vel_var)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(1)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(50)
            self.PI.set_velocity(self.vel_var)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
            EOS_graph.Line.set_xdata(self.t)
            EOS_graph.Line.set_ydata(self.S)
            EOS_graph.axes.set_ylim([1.2*np.min(self.S),1.2*np.max(self.S)])
            EOS_graph.update_graph()
            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
        
            # Display spectrum graph
            spec_t = self.t*1e-15
            t_sort, indices = np.unique(spec_t,return_index=True)
            S_sort = self.S[indices]
            func = interp.interp1d(t_sort, S_sort,kind='quadratic')
            t_interp = np.linspace(t_sort.min(),t_sort.max(),len(t_sort))
            E_interp = func(t_interp)
            self.v,self.A = fQ.ezfft(t_interp,E_interp)
            self.AA = np.abs(self.A)**2
            self.AA = self.AA/np.max(self.AA)
            self.v = self.v/1e12
            Spectrum_graph = self.graph_dict['Spectrum']
            Spectrum_graph.axes.set_ylim([0, 1.1*np.max(self.AA)])
            Spectrum_graph.axes.set_xlim([np.min(self.v), np.max(self.v)])
            Spectrum_graph.Line.set_xdata([self.v])
            Spectrum_graph.Line.set_ydata([self.AA])
            
            if self.phaseExists is False:
                        self.Phase_graph_ax = Spectrum_graph.axes.twinx()
                        self.LinePhase, = self.Phase_graph_ax.plot([],[],'m')
                        self.phaseExists = True
            phi = np.arctan2(self.A.imag,self.A.real)
            phi = np.unwrap(phi)
            a,b = np.polyfit(self.v,phi,deg=1,w=self.AA)
            slope = a*self.v+b
            phi = phi - slope
            self.Phase_graph_ax.set_ylim([-2*np.pi,2*np.pi])
            self.LinePhase.set_xdata(self.v)
            self.LinePhase.set_ydata([phi])
            self.LinePhase.set_linestyle(':')
            Spectrum_graph.update_graph()
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.RefSignal_button['state'] = 'normal'
        self.RefOff_button['state'] = 'normal'
        self.Log_button['state'] = 'normal'








class PumpProbe:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Spectro = mainf.Frame[3].Spectro
        
    def pos_2_delay(self,zero,pos):
            return  (pos-zero)*2e12/(sc.c)
        
    def delay_2_pos(self,zero,delay):
            return zero+(delay*sc.c/(2e12))
        
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        filename_lbl = tk.Label(frame, text = 'File name:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. timing. (fs):')
        max_lbl = tk.Label(frame, text = 'Max. timing (fs):')
        zero_lbl = tk.Label(frame, text = 'Pos. Zero Delay (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (fs):')
        step_log_lbl = tk.Label(frame, text = 'Number of step (log):')
        # delay_lbl = tk.Label(frame, text = 'Delay per step (ps):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
                # 
        def connect_and_disable_stage(self,dev_name=None):
            self.PI.connect_identification(dev_name=dev_name,exp_dependencie=True)
            con_b['state']='disabled'
            return
        
        # Define buttons and their action
                # Pi Stage
        con_b = tk.Button(frame, text='Connect SMC linear stage',
                                      command=lambda: connect_and_disable_stage(self,dev_name='SMC100'))

                
        # Define variables
                # PI stage
        self.pos_var = tk.DoubleVar()
        self.vel_var = tk.DoubleVar()
        self.filename_var = tk.StringVar()
        self.vel_disp = tk.DoubleVar()
        max_t_var = tk.DoubleVar()
        min_t_var = tk.DoubleVar()
        zero_var = tk.DoubleVar()
        step_t_var = tk.DoubleVar()
        self.step_log_var = tk.IntVar()
        # delay_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        self.pos_var.set(0)
        self.vel_var.set(1)
        self.filename_var.set("2022-MM-JJ_Test_1")
        self.vel_disp.set(2)
        min_t_var.set(-1000)
        max_t_var.set(10000)
        zero_var.set(-29.7)
        step_t_var.set(200)
        self.step_log_var.set(4)
        # delay_var.set(-1*self.pos_2_delay(0,step_var.get()/1000))
        # step_var.set(self.delay_2_pos(delay_var.get()))
        utime_var.set(0.1)

        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = self.pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = self.vel_var)
        filename_e = tk.Entry(frame, width = 18, textvariable = self.filename_var)
        min_t_e = tk.Entry(frame, width = 6, textvariable = min_t_var)
        max_t_e = tk.Entry(frame, width = 6, textvariable = max_t_var)
        zero_e = tk.Entry(frame, width = 6, textvariable = zero_var)
        step_t_e = tk.Entry(frame, width = 6, textvariable = step_t_var)
        step_log_e = tk.Entry(frame, width = 6, textvariable = self.step_log_var)
        # delay_e = tk.Entry(frame, width = 6, textvariable = delay_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)
        
        # Define position of all objects on the grid
                # PI stage
        con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        pos_lbl.grid(row=2, column=0, sticky='nsw')
        pos_e.grid(row=2, column=1, sticky='nse')
        vel_lbl.grid(row=3, column=0, sticky='nsw')
        vel_e.grid(row=3, column=1, sticky='nse')
        filename_lbl.grid(row=4, column=0, sticky='nsw')
        filename_e.grid(row=4, column=1, sticky='nse')

        param_lbl.grid(row=5, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=6, column=0, sticky='nsw')
        min_t_e.grid(row=6, column=1, sticky='nse')
        max_lbl.grid(row=7, column=0, sticky='nsw')
        max_t_e.grid(row=7, column=1, sticky='nse')
        zero_lbl.grid(row=8, column=0, sticky='nsw')
        zero_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_t_e.grid(row=9, column=1, sticky='nse')
        step_log_lbl.grid(row=10, column=0, sticky='nsw')
        step_log_e.grid(row=10, column=1, sticky='nse')
        # delay_lbl.grid(row=9, column=0, sticky='nsw')
        # delay_e.grid(row=9, column=1, sticky='nse')
        utime_lbl.grid(row=11, column=0, sticky='nsw')
        utime_e.grid(row=11, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=15, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(self.pos_var.get()))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(self.vel_var))


        # this function contains at minimum :

        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'       
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectro']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        def connect_and_disable_spectro(self):
            connect_spectrometer(self)
            cons_b['state']='disabled'
            return
        
        # Temporary Spectrometer things
        cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_and_disable_spectro(self))
        cons_b.grid(row=16, column=0, columnspan=2, sticky='nsew')
        
        self.align_state=False

        self.align_button = tk.Button(frame, text='Alignment Mode', command=lambda: self.Alignment_Mode())
        self.align_button.grid(row=17, column=0, columnspan=2, sticky='nsew')

        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(1)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=18, column=0, sticky='nsw')
        inte_e.grid(row=18, column=1,sticky='nse')
        int_period_lbl = tk.Label(frame, text = 'Integration period (ms):')
        self.int_period_var = tk.IntVar()
        self.int_period_var.set(1000)
        int_period_e = tk.Entry(frame, width = 6, textvariable = self.int_period_var)
        int_period_lbl.grid(row=19, column=0, sticky='nsw')
        int_period_e.grid(row=19, column=1,sticky='nse')

        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18, 
                                      command=lambda: self.start_experiment(max_pos=self.delay_2_pos(zero_var.get(),max_t_var.get()) , min_pos=self.delay_2_pos(zero_var.get(),min_t_var.get()), zero=zero_var, step=step_t_var.get()*sc.c/(2e12), progress=p_bar, 
                                                                            update_time=utime_var, inte_time=inte_var, int_period=self.int_period_var))
        self.start_button.grid(row=13, column=0, sticky='nsew')
        
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=13, column=1, sticky='nsew')
        
        
        self.save_button = tk.Button(frame, text='Save Data To File', state='disabled', width=18,
                                     command=lambda: self.save_data())
        self.save_button.grid(row=14, column=0, columnspan=2, sticky='nsew')
        
        
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=20, column=0, sticky='nsew')

        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=20, column=1, sticky='nsew')
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=21,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=21,column=1,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=22,column=0,sticky='nsew')
        

      

        param_lbl = tk.Label(frame, text = 'Retrieval Algorithm')
        param_lbl.grid(row=23, column=0, columnspan=2, sticky='nsew')


        minwl_lbl = tk.Label(frame, text = 'min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'max wl for integration(nm)')
        self.minwl_var = tk.DoubleVar()
        self.maxwl_var = tk.DoubleVar()
        self.minwl_var.set(600)
        self.maxwl_var.set(950)
        minwl_e = tk.Entry(frame, width = 6, textvariable = self.minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = self.maxwl_var)
        minwl_lbl.grid(row=24, column=0, sticky='nsw')
        maxwl_lbl.grid(row=25, column=0, sticky='nsw')
        minwl_e.grid(row=24, column=1, sticky='nse')
        maxwl_e.grid(row=25, column=1, sticky='nse')

        timingWL_lbl = tk.Label(frame, text = 'Timing beam WL (nm)')
        self.timingWL_var = tk.DoubleVar()
        self.timingWL_var.set(531)
        timingWL_e = tk.Entry(frame, width = 6, textvariable = self.timingWL_var)
        timingWL_lbl.grid(row=26, column=0, sticky='nsw')
        timingWL_e.grid(row=26, column=1, sticky='nse')

        self.filename_ret_var = tk.StringVar()
        self.filename_ret_var.set(self.filename_var.get())
        filename_ret_e = tk.Entry(frame, width = 18, textvariable = self.filename_ret_var)
        filename_ret_lbl = tk.Label(frame, text = 'Retrieval Filename:')
        filename_ret_lbl.grid(row=27, column=0, sticky='nsw')
        filename_ret_e.grid(row=27, column=1, sticky='nse')

        self.subtract_var = tk.IntVar()
        self.subtract_var.set(1)
        subtract = tk.Checkbutton(frame,text='Subtract negative delay?', variable=self.subtract_var)   
        subtract.grid(row=28, column=0, sticky='nsew')

        self.subtract_int_var = tk.IntVar()
        self.subtract_int_var.set(3)
        subtract_int = tk.Entry(frame, width=6, textvariable=self.subtract_int_var)   
        subtract_int.grid(row=28, column=1, sticky='nsew')

        self.g_factor_var = tk.IntVar()
        self.g_factor_var.set(0)
        g_factor = tk.Checkbutton(frame,text=r'Apply p(x) Correction, order:', variable=self.g_factor_var)   
        g_factor.grid(row=29, column=0, sticky='nsew')

        self.g_factor_int_var = tk.IntVar()
        self.g_factor_int_var.set(5)
        g_factor_int = tk.Entry(frame, width=6, textvariable=self.g_factor_int_var)   
        g_factor_int.grid(row=29, column=1, sticky='nsew')

        retrieve_b = tk.Button(frame, text='Retrieve Pump-Probe Signal', command=lambda: self.Retrieve_pump_probe(min_wl=self.minwl_var.get(),max_wl=self.maxwl_var.get(),timingWL=self.timingWL_var.get()))
        retrieve_b.grid(row=30, column=0, columnspan=2, sticky='nsew')

        save_trace_b = tk.Button(frame, text='Save Pump-Probe Trace', command=lambda: self.save_trace())
        save_trace_b.grid(row=31, column=0, columnspan=2, sticky='nsew')


        self.data_exist=False



    def Retrieve_pump_probe(self,min_wl=None,max_wl=None, timingWL=None):
        from scipy.signal import savgol_filter
        if self.data_exist==False:

            if messagebox.askokcancel(title='INFO', message='No current data\n Use file {}'.format(self.filename_ret_var.get())):
                file=self.filename_ret_var.get()
            else:
                return
        else:
            if messagebox.askokcancel(title='INFO', message='Use current data for retrieval?'):
                file=self.filename_var.get()
            else:
                return

        
        data=np.load("E:\Gabriel\Laser_Cooling_Measurement\_" + str(file) + "\data_dict.npz", allow_pickle=True)
        delay=np.load("E:\Gabriel\Laser_Cooling_Measurement\_" + str(file) + "\delay.npz", allow_pickle=True)
        wavelength=np.load("E:\Gabriel\Laser_Cooling_Measurement\_" + str(file) + "\wl.npz", allow_pickle=True)
        
        
        delay=np.array(delay['delay'])
        wavelength=np.array(wavelength['wl'])
              
        self.timeDelay = delay
        self.wl=wavelength

        signal_graph = self.graph_dict['Signal']
        signal_graph.Line.set_xdata(wavelength)
        signal_graph.axes.set_xlim([self.minwl_var.get(),self.maxwl_var.get()])
        signal_graph.axes.set_ylim([-0.1,0.1])

        self.trace = np.zeros((len(delay),wavelength.shape[0]))
        
        witness=abs(wavelength-self.timingWL_var.get()) <= 1
            
        for i in range(len(delay)):
            data_pos=data["pos_{}".format(i)]
            data_pos[data_pos==0]=1
            
            pump_series=np.average(data_pos[:,witness],axis=1)
            pump_series-=np.average(pump_series)
            
            pump_series_on= pump_series > 0
            pump_on = pump_series/np.average(pump_series[pump_series_on]) > 0.2
            
            pump_series_off= pump_series < 0
            pump_off= pump_series/np.average(pump_series[pump_series_off]) > 0.2
                        
            data_on_temporary=[]
            data_off_temporary=[]
            
            data_on=[]
            data_off=[]
                        
            for k in range(len(pump_series)-1):
                if pump_on[k]==True:
                    data_on_temporary.append(data_pos[k])
                    if pump_on[k+1]==False:
                        data_on.append(np.average(data_on_temporary,axis=0))
                        data_on_temporary=[]
                elif pump_off[k]==True:
                    data_off_temporary.append(data_pos[k])
                    if pump_off[k+1]==False:
                        data_off.append(np.average(data_off_temporary,axis=0))
                        data_off_temporary=[]
            
            data_on=np.array(data_on)
            data_off=np.array(data_off)
            
            if data_on.shape[0]>data_off.shape[0]:
                delta=data_on.shape[0]-data_off.shape[0]
                data_on = np.delete(data_on,np.arange(-delta,0,1),axis=0)
            elif data_off.shape[0]>data_on.shape[0]:
                delta=data_off.shape[0]-data_on.shape[0]
                data_off = np.delete(data_off,np.arange(-delta,0,1),axis=0)
            
            data_off[data_off==0]=1
            
            g_x=np.ones([len(data_on),len(wavelength)])
            
            if self.g_factor_var.get()==True:
                wvlt=wavelength[np.r_[274:296,396:791,859:1009]]
                data_on_factor=data_on[:,np.r_[274:296,396:791,859:1009]]
                data_off_factor=data_off[:,np.r_[274:296,396:791,859:1009]]
            

                for k in range(len(data_on_factor)):
                    p_x=data_on_factor[k]/data_off_factor[k]
                    f_x=np.poly1d(np.polyfit(wvlt-700,p_x,self.g_factor_int_var.get()))
                    g_x[k]=f_x(wavelength-700)
                        
            self.trace[i]=savgol_filter(np.average(((data_on/g_x)-(data_off))/(data_off),axis=0), 11, 2)
            self.adjust_2dgraph(self.trace)
                        
            signal_graph.Line.set_ydata(self.trace[i])
            signal_graph.update_graph()

    

        if self.subtract_var.get()==True:
            self.trace-=np.average(self.trace[0:self.subtract_int_var.get()],axis=0)
        self.adjust_2dgraph(self.trace)

        signal_graph.Line.set_ydata(self.trace[i])
        signal_graph.update_graph()
        
        messagebox.showinfo(title='Data Analysis Complete', message='Data Analysis Complete')
        
        return


    def Alignment_Mode(self):
        from scipy.signal import savgol_filter
        self.align_state = not self.align_state
        data_pos=[]
        wavelength=self.Spectro.spectro.wavelengths()
        witness=abs(wavelength-self.timingWL_var.get()) <= 1
        
        signal_graph = self.graph_dict['Signal']
        signal_graph.Line.set_xdata(wavelength)
        signal_graph.axes.set_xlim([self.minwl_var.get(),self.maxwl_var.get()])
        signal_graph.axes.set_ylim([-0.04,0.04])

        while self.align_state == True:

            start_daq=time.time()
            while time.time()-start_daq < self.int_period_var.get()/1000. :
                data_pos.append(self.Spectro.get_intensities())
                
            data_pos=np.array(data_pos)
            data_pos[data_pos==0]=1
                                    
            pump_series=np.average(data_pos[:,witness],axis=1)
            pump_series-=np.average(pump_series)
            
            pump_series_on= pump_series > 0
            pump_on = pump_series/np.average(pump_series[pump_series_on]) > 0.2
            
            pump_series_off= pump_series < 0
            pump_off= pump_series/np.average(pump_series[pump_series_off]) > 0.2
                        
            data_on_temporary=[]
            data_off_temporary=[]
            
            data_on=[]
            data_off=[]
                        
            for k in range(len(pump_series)-1):
                if pump_on[k]==True:
                    data_on_temporary.append(data_pos[k])
                    if pump_on[k+1]==False:
                        data_on.append(np.average(data_on_temporary,axis=0))
                        data_on_temporary=[]
                elif pump_off[k]==True:
                    data_off_temporary.append(data_pos[k])
                    if pump_off[k+1]==False:
                        data_off.append(np.average(data_off_temporary,axis=0))
                        data_off_temporary=[]
            
            data_on=np.array(data_on)
            data_off=np.array(data_off)
            
            if data_on.shape[0]>data_off.shape[0]:
                data_on = np.delete(data_on,-1,0)
            elif data_off.shape[0]>data_on.shape[0]:
                data_off = np.delete(data_off,-1,0)
            
            data_off[data_off==0]=0.00001
            
            S=np.average((data_on-data_off)/data_off,axis=0)
            
            S_ave=savgol_filter(S, 11, 0)
            # S_ave=S
            
            signal_graph.Line.set_ydata(S_ave)
            signal_graph.update_graph()

            data_pos=[]            



        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        #self.Spectro.set_trigger(0)         #Setting an external hardware edge trigger
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        if self.PI.device:
            self.start_button['state'] = 'normal'
        


    def adjust_2dgraph2(self,trace):#, step=None):
# =============================================================================
#         step = step.get()
#         if step == 0:
#             step=1
# =============================================================================
        # try:
        #      wl = len(self.Spectro.spectro.wavelengths())
        # except:
        #     return
        
        parent2d = self.graph_dict["Pump_Probe"].parent
        self.graph_dict["Pump_Probe"].destroy_graph()
        self.graph_dict["Pump_Probe"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size= np.transpose(trace).shape,cmap='seismic',vmin=-0.05,vmax=0.05)
        self.graph_dict["Pump_Probe"].change_data(np.transpose(trace),False)
        self.graph_dict["Pump_Probe"].im.set_extent((self.timeDelay[0],self.timeDelay[-1],self.minwl_var.get(),self.maxwl_var.get()))
        aspectRatio = abs((self.timeDelay[-1]-self.timeDelay[0])/(self.wl[-1]-self.wl[0]))
        self.graph_dict["Pump_Probe"].axes.set_aspect('auto')
        self.graph_dict["Pump_Probe"].axes.set_xlabel('Delay [fs]')
        self.graph_dict["Pump_Probe"].axes.set_ylabel('Wavelengths [nm]')
        cbar = self.graph_dict["Pump_Probe"].Fig.colorbar(self.graph_dict["Pump_Probe"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["Pump_Probe"].update_graph()




    def adjust_2dgraph(self,trace):#, step=None):

        logthresh=4
        
        parent2d = self.graph_dict["Pump_Probe"].parent
        self.graph_dict["Pump_Probe"].destroy_graph()
        self.graph_dict["Pump_Probe"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size= np.transpose(trace).shape,cmap='seismic',vmin=-0.02,vmax=0.02)
        self.graph_dict["Pump_Probe"].imshow_symlog(-1,1,logthresh=logthresh)
        self.graph_dict["Pump_Probe"].change_data(np.transpose(trace),False)
        self.graph_dict["Pump_Probe"].im.set_extent((self.timeDelay[0],self.timeDelay[-1],self.wl[-1],self.wl[0]))
        self.graph_dict["Pump_Probe"].axes.set_aspect('auto')
        self.graph_dict["Pump_Probe"].axes.set_xlabel('Delay [fs]')
        self.graph_dict["Pump_Probe"].axes.set_ylabel('Wavelengths [nm]')
        tick_locations=([-(10**x) for x in range(0,-logthresh-1,-1)]
                        +[0.0]
                        +[(10**x) for x in range(-logthresh,0+1)] )
        cbar = self.graph_dict["Pump_Probe"].Fig.colorbar(self.graph_dict["Pump_Probe"].im,ticks=tick_locations)
        cbar.set_label(r'Differential Transimission ($\Delta$T / T)')
        self.graph_dict["Pump_Probe"].update_graph()
        
        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, min_pos=None, max_pos=None, zero=None, step = None, progress=None, update_time=None,
                         inte_time=None, int_period=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True

        try:
            os.mkdir("E:\Gabriel\Laser_Cooling_Measurement\_" + str(self.filename_var.get()))
            print('Directory created')
        except OSError:
            if not messagebox.askokcancel(title='INFO', message='File Name Already Used\n (Click OK to overwrite files)\n (Click Cancel to abort experiment)'):
                self.stop_experiment()

        # Imports
        from pipython import pitools
        import time
        # Main experiment
        if self.PI == None:
            self.PI = self.mainf.Frame[2].Linstage

            # Parameters initialisation
        max_pos = max_pos
        min_pos = min_pos
        zero=zero.get()
        
        step = step
        step_log = self.step_log_var.get()
        update_time = update_time.get()
        int_period=int_period.get()

            # Verification
        if not self.PI.device:
            return

        if (max_pos is None) or (min_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = 49.999 #mm
        minp = -49.999 #mm
            # This is a fail safe in case you don't know your device
        if not(min_pos >= minp and max_pos >= minp and min_pos <= maxp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower limit of '+
                                'of your SMC stage')
            return
        

            # Steps and position vector initialisation

        if step_log==0:
            nsteps = int(np.ceil((max_pos - min_pos)/step))
            iteration = np.arange(0, nsteps, 1)

            move = np.arange(min_pos, max_pos, step)
            self.pos = np.zeros_like(move)
            
        else:
            
            max_pos_rel=max_pos-zero #self.delay_2_pos(0,self.pos_2_delay(max_pos)-zeros)
            min_pos_log=self.delay_2_pos(0,(100))
            
            x_neg = np.log10(max_pos_rel/(100*min_pos_log))*step_log
            x_pos = np.log10(max_pos_rel/(min_pos_log))*step_log
                        
            move_neg = -min_pos_log*10**(np.arange(x_neg,-1,-1)/step_log)
            move_pos =  min_pos_log*10**(np.flip(np.arange(x_pos,-1,-1))/step_log)
            move = np.concatenate((move_neg, [0], move_pos))+zero

            print(self.pos_2_delay(zero,move)/1000)

            nsteps = len(move)
            iteration = np.arange(0, nsteps, 1)
            self.pos = np.zeros_like(move)

        self.PI.set_velocity(vel=self.vel_disp)
        self.PI.go_2position(move[0]-0.001)
        self.PI.set_velocity(vel=self.vel_var)
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min(move), max(move)])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()


        # Define Arduino
        # arduino=serial.Serial('COM9',115200,timeout=None)


            # Spectro
        self.Spectro.set_trigger(0)
        self.wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(self.wl),np.max(self.wl)])
        spectro_graph.Line.set_xdata(self.wl)
        spectro_graph.Line.set_ydata(S)

        signal_graph = self.graph_dict['Signal']
        signal_graph.axes.set_ylim([1,-1])
        signal_graph.axes.set_xlim([np.min(self.wl),np.max(self.wl)])
        signal_graph.Line.set_xdata(self.wl)
        signal_graph.Line.set_ydata(S)

        self.data_dict={}
                
            # Main scanning and measurements
        for i in range(nsteps):
        
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            self.pos[i] = self.PI.get_position()
            
            spectra_pos=[]            
            
            start_daq=time.time()
            while time.time()-start_daq < int_period/1000. :
                spectra_pos.append(self.Spectro.get_intensities())
                
            spectra_pos=np.array(spectra_pos)
            spectra_pos[spectra_pos==0]=1
            
            self.data_dict['pos_{}'.format(i)] = spectra_pos[:,670:1679]
            self.wl_crop=self.wl[670:1679]
            
            scan_graph.Line.set_xdata(iteration[:i])
            scan_graph.Line.set_ydata(self.pos[:i])
            scan_graph.update_graph()
            signal_graph.Line.set_xdata(self.wl)
            signal_graph.Line.set_ydata(spectra_pos[-1])
            signal_graph.axes.set_ylim([np.min(spectra_pos[-1]),np.max(spectra_pos[-1])])
            signal_graph.update_graph()            
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps) 
                progress.update()
                
            if not self.running:
                break
                           
        
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(self.pos_var)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(5)
            self.PI.set_velocity(return_vel)
            self.PI.go_2position(self.pos_var)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(self.pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(self.wl)
            spectro_graph.Line.set_ydata(spectra_pos[-1])
            spectro_graph.update_graph()

            self.timeDelay =self.pos_2_delay(zero,self.pos)
            
            dp = np.std(self.pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')



        # Final calculations
        self.timeDelay =self.pos_2_delay(zero,self.pos)
        


        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        self.data_exist=True
        

    def save_data(self):
        np.savez_compressed("E:\Gabriel\Laser_Cooling_Measurement\_" + str(self.filename_var.get()) + "\data_dict.npz", **self.data_dict)
        np.savez("E:\Gabriel\Laser_Cooling_Measurement\_" + str(self.filename_var.get()) + "\delay.npz",delay=self.timeDelay, allow_pickle=True)
        np.savez("E:\Gabriel\Laser_Cooling_Measurement\_" + str(self.filename_var.get()) + "\wl.npz",wl=self.wl_crop, allow_pickle=True)
        messagebox.showinfo(title='Data Saved', message='Data Saved')

    def save_trace(self):
        try:
            self.trace
            np.savez("E:\Gabriel\Laser_Cooling_Measurement\_" + str(self.filename_ret_var.get()) + "\trace.npz", trace=self.trace, allow_pickle=True)
            messagebox.showinfo(title='Data Saved', message='Data Saved')
        except AttributeError:
            messagebox.showinfo(title='Trace Error', message='Trace not retrieved yet')


class batchSpectra:
    # This class is implicitly called in the main frame
    """
    This is a class to create the user interface required to run a FROG experiment.
    It allows to control and read a spectrometer, control a PI stage, and then
    run an experiment synchronizing the movement of the stage and the spectra acquisition.
    
    Attributes:
        
        
    """

    def __init__(self, mainf = None):
        """
        This is the constructor for the FROG class.
        Parameters:
            
        """
        self.empty_var = []
        self.graph_dict = {}
        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        """
        The frame is created here, i.e. the labels, boxes and buttons are
        defined here.
        """
        # Define labels
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
                # 
        
                
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        #vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(0)
        #vel_var.set(1)
        min_var.set(-20)
        max_var.set(20)
        step_var.set(1)
        utime_var.set(1)
        
        # Define entry boxes
        # Define position of all objects on the grid
                # PI stage
        #self.con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        param_lbl.grid(row=4, column=0, columnspan=2, sticky='nsew')
        
        numDark_lbl = tk.Label(frame, text = 'Average how many dark spectra?')
        numSpec_lbl = tk.Label(frame, text = 'Save how may spectra?')
        numFile_lbl = tk.Label(frame, text = 'Save into how many files?')
        numSpec_var = tk.IntVar()
        numFile_var = tk.IntVar()
        numDark_var = tk.IntVar()
        numSpec_var.set(100)
        numFile_var.set(1)
        numDark_var.set(1)
        numSpec_e = tk.Entry(frame, width = 6, textvariable = numSpec_var)
        numFile_e = tk.Entry(frame, width = 6, textvariable = numFile_var)
        numDark_e = tk.Entry(frame, width = 6, textvariable = numDark_var)
        numDark_lbl.grid(row=5, column=0, sticky='nsw')
        numDark_e.grid(row=5, column=1, sticky='nse')
        
        numSpec_lbl.grid(row=6, column=0, sticky='nsw')
        numSpec_e.grid(row=6, column=1, sticky='nse')
        numFile_lbl.grid(row=7, column=0, sticky='nsw')
        numFile_e.grid(row=7, column=1, sticky='nse')
        
        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=15, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        
        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'
            self.cons_b['state'] = 'disabled'
        
        
        
        def get_average_dark_spectrum(self,numDark):
            numDark = numDark.get()
            self.Spectro.measure_average_darkspectrum(numDark)
            self.sub_dark_button['state']='normal'
        
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectrometer']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        # Temporary Spectrometer things
        self.cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_spectrometer(self))
        self.cons_b.grid(row=8, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(10)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=9, column=0, sticky='nsw')
        inte_e.grid(row=9, column=1,sticky='nse')
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_average_dark_spectrum(self,numDark = numDark_var))
        self.dark_button.grid(row=10,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=11,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=12,column=0,sticky='nsew')
        
        # Start & stop buttons :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, numSpec=numSpec_var, numFile=numFile_var))
        self.start_button.grid(row=13, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=2, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=3, column=0, sticky='nsew')
        
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        self.start_button['state'] = 'normal'
        

    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, progress=None, update_time=None,
                         inte_time=None, numSpec=None, numFile=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        #self.update_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True
        
            # Parameters initialisation
        numSpec = numSpec.get()
        numFile = numFile.get()
        update_time = update_time.get()
        
        
        # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        
        # Create folder to save
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        folderPath = 'measurements/Batch acquisition - ' + timeStamp
        os.mkdir(folderPath)
        
        # Save wavelengths vector
        np.save(folderPath + '/Wavelengths.npy', wl)
        
        # Determine how to split spectra
        if numFile<2:
            numFile = 1
            lastFileNum = numSpec
            mainFileNum = numSpec
        else:
            if numSpec%(numFile) == 0:
                mainFileNum = round(numSpec/numFile)
                lastFileNum = round(numSpec/numFile)
                
            elif  numSpec%(numFile-1) == 0:
                mainFileNum = round(numSpec/(numFile-1))-1
                lastFileNum = numFile-1
            else:
                lastFileNum = numSpec%(numFile-1)
                mainFileNum = round((numSpec - lastFileNum)/(numFile-1))
        
            # Main scanning and measurements
        for ii in range(numFile):
            
            if ii == numFile-1:
                savSpecArray = np.zeros((lastFileNum, len(wl)))
            else:
                savSpecArray = np.zeros((mainFileNum, len(wl)))
            
            for jj in range(savSpecArray.shape[0]):
                savSpecArray[jj,:] = self.Spectro.get_intensities()
                
            fileName = 'spectra - ' + str(ii) + '.npy'
            np.save(folderPath + '/' + fileName, savSpecArray)
            
            # Actualise progress bar
            if progress:
                progress['value'] = (ii+1)/(numFile)
                progress.update()
                
            if not self.running:
                break       
            
            
        if not self.running:
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            messagebox.showinfo(title='INFO', message='Measurements is done.')
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        #self.update_button['state'] = 'normal'
        
        
        

class iHR320:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.mono = None
        
    def create_frame(self, frame):


        # this function contains at minimum :
        #self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
        #                              command=lambda: self.start_experiment())
        #self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        #self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
        #                             command=lambda: self.stop_experiment())
        #self.stop_button.grid(row=11, column=0, columnspan=2, sticky='nsew')
        
        pos_lbl = tk.Label(frame, text = 'Set position to (nm):')
        posd_lbl = tk.Label(frame, text = 'Position according to the device (nm):')
        gra_lbl = tk.Label(frame, text = 'Set grating to (g/mm):')
        esw_lbl = tk.Label(frame, text = 'Set entrance slit width to (mm):')
        eswd_lbl = tk.Label(frame, text = 'Entrance slit according to the device (mm):')
        ssw_lbl = tk.Label(frame, text = 'Set exit slit width to (mm):')
        sswd_lbl = tk.Label(frame, text = 'Exit slit according to the device (mm):')
        exm_lbl = tk.Label(frame, text = 'Set exit mirror to (front or side):')
        
        
        self.pos_var = tk.DoubleVar()
        self.posd_var = tk.DoubleVar()
        self.gra_var = tk.DoubleVar()
        self.esw_var = tk.DoubleVar()
        self.ssw_var = tk.DoubleVar()
        self.eswd_var = tk.DoubleVar()
        self.sswd_var = tk.DoubleVar()
        self.exm_var = tk.StringVar()
      
        
        self.pos_var.set(0)
        self.posd_var.set(0)
        self.gra_var.set(0)
        self.esw_var.set(0)
        self.ssw_var.set(0)
        self.eswd_var.set(0)
        self.sswd_var.set(0)
        self.exm_var.set("front")
        
        pos_e = tk.Entry(frame, width = 6, textvariable = self.pos_var)
        gra_e = tk.Entry(frame, width = 6, textvariable = self.gra_var)
        esw_e = tk.Entry(frame, width = 6, textvariable = self.esw_var)
        ssw_e = tk.Entry(frame, width = 6, textvariable = self.ssw_var)
        exm_e = tk.Entry(frame, width = 6, textvariable = self.exm_var)
        
        pos_lbl.grid(row=5, column=0, sticky='nsw')
        pos_e.grid(row=5, column=1, sticky='nse')
        posd_lbl.grid(row=6, column=0, sticky='nsw')
        gra_lbl.grid(row=7, column=0, sticky='nsw')
        gra_e.grid(row=7, column=1, sticky='nse')
        esw_lbl.grid(row=8, column=0, sticky='nsw')
        esw_e.grid(row=8, column=1, sticky='nse')
        eswd_lbl.grid(row=9, column=0, sticky='nsw')
        ssw_lbl.grid(row=10, column=0, sticky='nsw')
        ssw_e.grid(row=10, column=1, sticky='nse')
        sswd_lbl.grid(row=11, column=0, sticky='nsw')
        exm_lbl.grid(row=12, column=0, sticky='nsw')
        exm_e.grid(row=12, column=1, sticky='nse')
        
        
        
        
        """
        def stop_experiment(self):
            self.running = False
            self.spectro_start_button['state'] = 'normal'
    
        def start_experiment(self):
    
            self.stop_button['state'] = 'normal'
            self.start_button['state'] = 'disabled'
            self.running = True
        """
            
        def connect_mono(self):
            self.cons_b['state'] = 'disabled'
            
            name='ihr32'
            config={'port':2,
                    'out_of_limits':'closest',
                    'gratings':{'grating 1; 600 lines per mm':{'lines_per_mm':600,'index':0},
                                'grating 2; 150 lines per mm':{'lines_per_mm':150,'index':1},
                                'grating 3; 120 lines per mm':{'lines_per_mm':120,'index':2}
                                },
                    'limits':[0,15800]

                    }

            config_path = ''
            self.mono = HoribaIHR320(name,config,config_path)
            messagebox.showinfo(title="Monochromator", message="Horiba iHR320 is connected")
            #messagebox.showinfo(title="Monochromator", message=f"{self.mono._state}")
            
        
        self.cons_b = tk.Button(frame, text='Connect monochromator', command=lambda: connect_mono(self))
        self.cons_b.grid(row=13, column=0, columnspan=2, sticky='nsew')

        pos_e.bind('<Return>', lambda e: self.mono.set_position(self.pos_var.get()))
        gra_e.bind('<Return>', lambda e: self.mono.set_turret(self.gra_var.get()))
        esw_e.bind('<Return>', lambda e: self.mono.set_front_entrance_slit(self.esw_var.get()))
        ssw_e.bind('<Return>', lambda e: self.mono.set_front_exit_slit(self.ssw_var.get()))





class Boxcar:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.Zurich = mainf.Frame[1].Zurich
        
    def create_frame(self, frame):
        # Define labels
                # Delay line
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
#        min_lbl = tk.Label(frame, text = 'Min. duration [s]:')
        max_lbl = tk.Label(frame, text = 'Duration duration [s]:')
        step_lbl = tk.Label(frame, text = 'Number of steps')
        
        # Define buttons and their action
               
        # Define variables
                # PI stage
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        self.wait_var = tk.IntVar()
#        min_var.set(1)
        max_var.set(1)
        step_var.set(5)
        
        self.directory_var=tk.StringVar()
        
        
        self.directory_var.set('E:/Marco/Raw_data/Boxcar/')
        
        
        # Define entry boxes
                # PI stage
#        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)

        # Define position of all objects on the grid
                # PI stage
        param_lbl.grid(row=6, column=0, columnspan=2, sticky='nsew')
#        min_lbl.grid(row=7, column=0, sticky='nsw')
#        min_e.grid(row=7, column=1, sticky='nse')
        max_lbl.grid(row=8, column=0, sticky='nsw')
        max_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=13, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='normal', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, step=step_var, progress=p_bar))
        self.start_button.grid(row=12, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')   
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save())
        self.save_button.grid(row=20, column=0, columnspan=2, sticky='nsew')
        
    def save(self):
        
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez(self.directory_var.get() + timeStamp+'_Boxcar_measurement',time = self.t,signal = self.S)
        

    
    def Zurich_acquire(self):
        path = '/' + '{}'.format(self.Zurich.info['device'])+'/boxcars/0/sample'
        self.Zurich.info['daq'].subscribe(path)
        data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)

        
        try:
            data = data_set[path]['value']
#            print(data)
#            print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data
    
    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None):
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'

        self.running = True

            # Parameters initialisation
        max_pos = max_pos.get()
#        min_pos = min_pos.get()        
        step = int(step.get())
        
        if (max_pos is None):
            return

            # Getting the max and min possible value of the device
        maxp = 20*60
        minp = 1

            # This is a fail safe in case you don't know your device
        if not(max_pos >= minp and max_pos <= maxp):
            messagebox.showinfo(title='Error', message='You are either over or under the maximum or lower duration limit of '+
                                'this experiment')
            return

            # Steps and position vector initialisation
#        nsteps = int(np.ceil((max_pos - min_pos)/step))
        nsteps = step
#        iteration = np.linspace(0, nsteps, nsteps+1)
        b=[]
        time_tracker=[]
        self.S = np.zeros(nsteps+1)
        self.t= np.zeros(nsteps+1)

        # Variables for the graph update
        
            # Variables for the graph update
        last_gu = time.time_ns()
        duration = 0
        current_i= 1
            # Main scanning and measurements
#        for i in range(nsteps):
#            # Measure signal
#            self.t[i] = time.time_ns()
#            self.S[i] = np.mean(self.Zurich_acquire())*1000
#            
#            # Actualise progress bar
#            if progress:
#                progress['value'] = (i)/(nsteps)
#                progress.update()
#           
#            if not self.running:
#                break
            
        while duration<max_pos:
            if duration>((current_i*max_pos/nsteps)-150e-3):
                time_tracker.append((time.time_ns()-last_gu)*1e-9)
                b.append(np.mean(self.Zurich_acquire()))
                
                if progress:
                    progress['value'] = current_i/nsteps
                    progress.update()
                current_i+=1
                
            if current_i>nsteps:
                break
            
            if not self.running:
                break
            duration=(time.time_ns()-last_gu)*1e-9
            
        self.S = np.asarray(b)
        self.t = np.asarray(time_tracker)
        
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(5)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(5)
            messagebox.showinfo(title='INFO', message='Measurements is done.')
        

        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'








class Horiba_spectrum:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.Zurich = mainf.Frame[1].Zurich
        self.plotRefSignal = False
        self.refSignal =[]
        self.refTime =[]
        self.refExists = False
        self.LogSpec = False
        self.phaseExists = False
        self.mono= None
    
    def create_frame(self, frame):
        # Define labels
                # Delay line
        sli_lbl = tk.Label(frame, text = 'Input slit width (mm):')
        sle_lbl = tk.Label(frame, text = 'Output sit width (mm):')
        pos_lbl = tk.Label(frame, text = 'Go to wavelength (nm):')
        gra_lbl = tk.Label(frame, text = 'Set grating (g/mm):')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. wavelength. (nm):')
        max_lbl = tk.Label(frame, text = 'Max. wavelength. (nm):')
        step_lbl = tk.Label(frame, text = 'Step size (nm):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        
        def connect_mono(self):
            self.con_b['state'] = 'disabled'
            
            name='ihr32'
            config={'port':2,
                    'out_of_limits':'closest',
                    'gratings':{'grating 1; 600 lines per mm':{'lines_per_mm':600,'index':0},
                                'grating 2; 150 lines per mm':{'lines_per_mm':150,'index':1},
                                'grating 3; 120 lines per mm':{'lines_per_mm':120,'index':2}
                                },
                    'limits':[0,15800]

                    }

            config_path = ''
            self.mono = HoribaIHR320(name,config,config_path)
            messagebox.showinfo(title="Monochromator", message="Horiba iHR320 is connected")
            #messagebox.showinfo(title="Monochromator", message=f"{self.mono._state}")
            self.start_button['state'] = 'normal'
        
        # Define buttons and their action
                # Pi Stage
        self.con_b = tk.Button(frame, text='Connect monochromator', command=lambda: connect_mono(self))

        # Define variables
                # PI stage
        sli_var = tk.DoubleVar()
        sle_var = tk.DoubleVar()
        self.pos_var = tk.DoubleVar()
        gra_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        self.wait_var = tk.IntVar()
        sli_var.set(1)
        sle_var.set(0.5)
        self.pos_var.set(1000)
        gra_var.set(150)
        min_var.set(1000)
        max_var.set(2000)
        step_var.set(100)
        utime_var.set(1)
        self.wait_var.set(1)
        
        # Define entry boxes
                # PI stage
        sli_e = tk.Entry(frame, width = 6, textvariable = sli_var)
        sle_e = tk.Entry(frame, width = 6, textvariable = sle_var)
        pos_e = tk.Entry(frame, width = 6, textvariable = self.pos_var)
        gra_e = tk.Entry(frame, width = 6, textvariable = gra_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
                # PI stage
        self.con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        sli_lbl.grid(row=2, column=0, sticky='nsw')
        sli_e.grid(row=2, column=1, sticky='nse')
        sle_lbl.grid(row=3, column=0, sticky='nsw')
        sle_e.grid(row=3, column=1, sticky='nse')
        pos_lbl.grid(row=4, column=0, sticky='nsw')
        pos_e.grid(row=4, column=1, sticky='nse')
        gra_lbl.grid(row=5, column=0, sticky='nsw')
        gra_e.grid(row=5, column=1, sticky='nse')
        param_lbl.grid(row=6, column=0, columnspan=2, sticky='nsew')
        min_lbl.grid(row=7, column=0, sticky='nsw')
        min_e.grid(row=7, column=1, sticky='nse')
        max_lbl.grid(row=8, column=0, sticky='nsw')
        max_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')
        utime_lbl.grid(row=11, column=0, sticky='nsw')
        utime_e.grid(row=11, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=13, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.mono.set_position(self.pos_var.get()))
        gra_e.bind('<Return>', lambda e: self.mono.set_turret(gra_var.get()))
        sli_e.bind('<Return>', lambda e: self.mono.set_front_entrance_slit(sli_var.get()))
        sle_e.bind('<Return>', lambda e: self.mono.set_front_exit_slit(sle_var.get()))



        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=12, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')   
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save())
        self.RefSignal_button = tk.Button(frame, text='Signal reference', state='disabled', command=lambda: self.SignalRef())
        self.RefSignal_button.grid(row=15, column=0, sticky='nsw')
        self.RefOff_button = tk.Button(frame, text='Ref ON/OFF', state='disabled',command=lambda: self.RemoveRef())
        self.RefOff_button.grid(row=15, column=1, sticky='nse')
        self.save_button.grid(row=20, column=0, columnspan=2, sticky='nsew')
        self.wait = tk.Checkbutton(frame,text='Settling wait time', variable=self.wait_var)   
        self.wait.grid(row=10, column=0, columnspan=2, sticky='nsew')
    def save(self):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        np.savez('E:/GitHub/femtoQ-Intruments/Labo_Env/ultrafastGUI/measurements/' + timeStamp + '_spectrum',lamda = self.L,signal = self.S)

    def SignalRef(self):
        if self.refExists is False:
            self.graph_dict['Signal'].LineRef, =  self.graph_dict['Signal'].axes.plot([], [])
            self.graph_dict['Spectrum'].LineRef, = self.graph_dict['Spectrum'].axes.plot([],[])
            self.refExists = True
        self.refSignal = self.S
        self.refTime = self.L
        self.refFreq = self.v
        self.refSpec = self.AA
        if self.plotRefSignal is False:
            self.plotRefSignal = True
        return
    def RemoveRef(self):
        if self.refExists is True:
            if self.plotRefSignal is True:    
                self.plotRefSignal = False
                self.graph_dict['Signal'].LineRef.set_xdata([])
                self.graph_dict['Signal'].LineRef.set_ydata([])
                self.graph_dict['Spectrum'].LineRef.set_xdata([])
                self.graph_dict['Spectrum'].LineRef.set_ydata([])
            elif self.plotRefSignal is False:
                self.plotRefSignal = True
                self.graph_dict['Signal'].LineRef.set_xdata(self.refTime)
                self.graph_dict['Signal'].LineRef.set_ydata(self.refSignal)
                self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
                if self.LogSpec is True:
                    self.graph_dict['Spectrum'].LineRef.set_ydata(np.log(self.refSpec))
                else:
                    self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Signal'].update_graph()
            self.graph_dict['Spectrum'].update_graph()
        return
    
    def Zurich_acquire(self):
        import time
        path = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/sample'
        path2 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/timeconstant'
        path3 = '/' + '{}'.format(self.Zurich.info['device'])+'/demods/0/order'
        tc= self.Zurich.info['daq'].getDouble(path2)
        order= self.Zurich.info['daq'].getDouble(path3)
        if self.wait_var.get() == 1:
            # Times for 99% settling. Source : https://www.zhinst.com/americas/resources/principles-lock-detection
            if order == 1:
                Settling_time = 4.61*tc
            elif order == 2:
                Settling_time = 6.64*tc
            elif order == 3:
                Settling_time = 8.41*tc
            elif order == 4:
                Settling_time = 10.05*tc
            time.sleep(Settling_time)
        self.Zurich.info['daq'].subscribe(path)
        data_set = self.Zurich.info['daq'].poll(0.01,100,0,True)


        try:
            data = data_set[path]['x']
#            print(data)
#            print(len(data))
        except:
            pass
        self.Zurich.info['daq'].unsubscribe(path)
        return  data
    
    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None):
        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.RefSignal_button['state'] = 'disabled'
        self.RefOff_button['state'] = 'disabled'
        self.running = True

        # Imports
        from pipython import pitools
        import time
        import scipy
        import femtoQ.tools as fQ
        c = scipy.constants.c
        # Main experiment

            # Parameters initialisation
        max_pos = max_pos.get()
        min_pos = min_pos.get()
        step = step.get()
        update_time = update_time.get()

            # Verification

        if (max_pos is None) or (min_pos is None):
            return



            # Steps and position vector initialisation
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(min_pos, max_pos, nsteps+1)
        pos = np.zeros(nsteps+1)
        self.S = np.zeros(nsteps+1)
        self.L = np.zeros(nsteps+1)

        # Variables for the graph update
        
            # Variables for the graph update
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()
        EOS_graph = self.graph_dict['Signal']
        EOS_graph.axes.set_ylim([-10,10])
        EOS_graph.axes.set_xlim([min_pos,max_pos])
        EOS_graph.Line.set_xdata([])
        EOS_graph.Line.set_ydata([])
        if self.plotRefSignal is True:
            EOS_graph.LineRef.set_xdata(self.refTime)
            EOS_graph.LineRef.set_ydata(self.refSignal)
            EOS_graph.LineRef.set_linestyle('--')
            self.graph_dict['Spectrum'].LineRef.set_xdata([self.refFreq])
            self.graph_dict['Spectrum'].LineRef.set_ydata([self.refSpec])
            self.graph_dict['Spectrum'].LineRef.set_linestyle('--')
        EOS_graph.update_graph()
        self.graph_dict['Spectrum'].update_graph()
            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.mono.set_position(move[i])
            # Measure real position
            pos[i] = move[i]
            # Measure signal
            self.L[i] = pos[i]
            self.S[i] = np.mean(self.Zurich_acquire())*1000
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                EOS_graph.Line.set_xdata(self.L[:i])
                EOS_graph.Line.set_ydata(self.S[:i])
                EOS_graph.axes.set_ylim([np.min(self.S),np.max(self.S)])
                EOS_graph.update_graph()
                
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            self.mono.set_position(self.pos_var.get())
        else:
            self.mono.set_position(self.pos_var.get())
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
            EOS_graph.Line.set_xdata(self.L)
            EOS_graph.Line.set_ydata(self.S)
            EOS_graph.axes.set_ylim([np.min(self.S),np.max(self.S)])
            EOS_graph.update_graph()
            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')
        
            # Display spectrum graph
            spec_t = self.L
            t_sort, indices = np.unique(spec_t,return_index=True)
            S_sort = self.S[indices]
            func = interp.interp1d(t_sort, S_sort,kind='quadratic')
            t_interp = np.linspace(t_sort.min(),t_sort.max(),len(t_sort))
            E_interp = func(t_interp)
            self.v,self.A = fQ.ezfft(t_interp,E_interp)
            self.AA = np.abs(self.A)**2
            self.AA = self.AA/np.max(self.AA)
            self.v = self.v/1e12
            Spectrum_graph = self.graph_dict['Spectrum']
            Spectrum_graph.axes.set_ylim([0, 1.1*np.max(self.AA)])
            Spectrum_graph.axes.set_xlim([np.min(self.v), np.max(self.v)])
            Spectrum_graph.Line.set_xdata([self.v])
            Spectrum_graph.Line.set_ydata([self.AA])
            
            if self.phaseExists is False:
                        self.Phase_graph_ax = Spectrum_graph.axes.twinx()
                        self.LinePhase, = self.Phase_graph_ax.plot([],[],'m')
                        self.phaseExists = True
            phi = np.arctan2(self.A.imag,self.A.real)
            phi = np.unwrap(phi)
            a,b = np.polyfit(self.v,phi,deg=1,w=self.AA)
            slope = a*self.v+b
            phi = phi - slope
            self.Phase_graph_ax.set_ylim([-2*np.pi,2*np.pi])
            self.LinePhase.set_xdata(self.v)
            self.LinePhase.set_ydata([phi])
            self.LinePhase.set_linestyle(':')
            Spectrum_graph.update_graph()
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.RefSignal_button['state'] = 'normal'
        self.RefOff_button['state'] = 'normal'





class interferenceStability:
    # This class is implicitly called in the main frame
    """
    This is a class to create the user interface required to run a FROG experiment.
    It allows to control and read a spectrometer, control a PI stage, and then
    run an experiment synchronizing the movement of the stage and the spectra acquisition.
    
    Attributes:
        
        
    """
        
    def __init__(self, mainf = None):
        """
        This is the constructor for the FROG class.
        Parameters:
            
        """
        self.empty_var = []
        self.graph_dict = {}
        self.Spectro = mainf.Frame[3].Spectro
        
    def create_frame(self, frame):
        """
        The frame is created here, i.e. the labels, boxes and buttons are
        defined here.
        """
        # Define labels
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
                # 
        
        self.directory_var=tk.StringVar()
        
        
        self.directory_var.set('E:/Marco/Raw_data/Interference_stability/')
           
                
        # Define variables
                # PI stage
        pos_var = tk.DoubleVar()
        #vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(0)
        #vel_var.set(1)
        min_var.set(-20)
        max_var.set(20)
        step_var.set(1)
        utime_var.set(1)
        
        # Define entry boxes
        # Define position of all objects on the grid
                # PI stage
        #self.con_b.grid(row=1, column=0, columnspan=2, sticky='nsew')
        param_lbl.grid(row=4, column=0, columnspan=2, sticky='nsew')
        
        numDark_lbl = tk.Label(frame, text = 'Average how many dark spectra?')
        numSpec_lbl = tk.Label(frame, text = 'Save how may spectra?')
        numFile_lbl = tk.Label(frame, text = 'Save into how many files?')
        numSpec_var = tk.IntVar()
        numFile_var = tk.IntVar()
        numDark_var = tk.IntVar()
        numSpec_var.set(100)
        numFile_var.set(1)
        numDark_var.set(1)
        
        numSpec_e = tk.Entry(frame, width = 6, textvariable = numSpec_var)
        numFile_e = tk.Entry(frame, width = 6, textvariable = numFile_var)
        numDark_e = tk.Entry(frame, width = 6, textvariable = numDark_var)
        numDark_lbl.grid(row=5, column=0, sticky='nsw')
        numDark_e.grid(row=5, column=1, sticky='nse')
        
        numSpec_lbl.grid(row=6, column=0, sticky='nsw')
        numSpec_e.grid(row=6, column=1, sticky='nse')
        numFile_lbl.grid(row=7, column=0, sticky='nsw')
        numFile_e.grid(row=7, column=1, sticky='nse')
        
        
        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=15, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        
        def connect_spectrometer(self):
            self.Spectro.connect(exp_dependencie=True)
            self.spectro_start_button['state'] = 'normal'
            self.cons_b['state'] = 'disabled'
        
        
        
        def get_average_dark_spectrum(self,numDark):
            numDark = numDark.get()
            self.Spectro.measure_average_darkspectrum(numDark)
            self.sub_dark_button['state']='normal'
        
        
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectrometer']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        # Temporary Spectrometer things
        self.cons_b = tk.Button(frame, text='Connect spectrometer', command=lambda: connect_spectrometer(self))
        self.cons_b.grid(row=8, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(10)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=9, column=0, sticky='nsw')
        inte_e.grid(row=9, column=1,sticky='nse')
        
        totTime_lbl = tk.Label(frame, text = 'Total time of the measurement (s):')
        totTime_var = tk.IntVar()
        totTime_var.set(30)
        totTime_e = tk.Entry(frame, width = 6, textvariable = totTime_var)
        totTime_lbl.grid(row=16, column=0, sticky='nsw')
        totTime_e.grid(row=16, column=1,sticky='nse')
        
        interTime_lbl = tk.Label(frame, text = 'How much time between each spectra (s):')
        interTime_var = tk.IntVar()
        interTime_var.set(1)
        interTime_e = tk.Entry(frame, width = 6, textvariable = interTime_var)
        interTime_lbl.grid(row=17, column=0, sticky='nsw')
        interTime_e.grid(row=17, column=1,sticky='nse')
        
        
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_average_dark_spectrum(self,numDark = numDark_var))
        self.dark_button.grid(row=10,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=11,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=12,column=0,sticky='nsew')
        
        # Start & stop buttons :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, numSpec=numSpec_var, numFile=numFile_var,totalTime=totTime_var,intervalTime=interTime_var))
        self.start_button.grid(row=13, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=2, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=3, column=0, sticky='nsew')
        
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.running = True
        
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
        
        
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'  
        self.start_button['state'] = 'normal'
        

    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, progress=None, update_time=None,
                         inte_time=None, numSpec=None, numFile=None,totalTime=None,intervalTime=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        #self.update_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True
        
            # Parameters initialisation
        # numSpec = numSpec.get()
        numFile = numFile.get()
        update_time = update_time.get()
        
        totalTime = totalTime.get()
        intervalTime = intervalTime.get()
        
        
        numSpec=int(totalTime/intervalTime+1)
        
        
        # Spectro
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectrometer']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        
        # Create folder to save
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        # folderPath = 'measurements/Batch acquisition - ' + timeStamp
        folderPath = self.directory_var.get() + timeStamp+'_spectra'
        os.mkdir(folderPath)
        
        
        
        # np.savez(self.directory_var.get() + timeStamp+'_EOS_measurement',time = self.t,signal = self.S)
        
        
        # Save wavelengths vector
        np.save(folderPath + '/Wavelengths.npy', wl)
        
        # Determine how to split spectra
        if numFile<2:
            numFile = 1
            lastFileNum = numSpec
            mainFileNum = numSpec
        else:
            if numSpec%(numFile) == 0:
                mainFileNum = round(numSpec/numFile)
                lastFileNum = round(numSpec/numFile)
                
            elif  numSpec%(numFile-1) == 0:
                mainFileNum = round(numSpec/(numFile-1))-1
                lastFileNum = numFile-1
            else:
                lastFileNum = numSpec%(numFile-1)
                mainFileNum = round((numSpec - lastFileNum)/(numFile-1))
        
            # Main scanning and measurements
        for ii in range(numFile):
            
            if ii == numFile-1:
                savSpecArray = np.zeros((lastFileNum, len(wl)))
                
            else:
                savSpecArray = np.zeros((mainFileNum, len(wl)))
            
            for jj in range(numSpec):
                savSpecArray[jj,:] = self.Spectro.get_intensities()
                time.sleep(intervalTime)
                # Actualise progress bar
                if progress:
                    progress['value'] = (jj+1)/(numSpec)
                    progress.update()
                
                
            fileName = 'spectra - ' + str(ii) + '.npy'
            np.save(folderPath + '/' + fileName, savSpecArray)
            
            
            if not self.running:
                break       
            
            
        if not self.running:
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            messagebox.showinfo(title='INFO', message='Measurements is done.')
        
        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        #self.update_button['state'] = 'normal'  
        
        
class D_Scan:
    def __init__(self, mainf=None):
        """
        The constructor for your Experiment.

        Parameters:
            mainf : This is the Mainframe, it cannot be anything else.
        """
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.Spectro = mainf.Frame[3].Spectro

    def create_frame(self, frame):
        """
        This function is used to create the free frame mentionned in the
        CreateLayout.This is where you place all of the widget you desire to
        have in your experiment.

        Parameters:
            frame : This is the section attributed to your widget in the big
            Experiment frame.
        """
        # Define variables
                # PI stage
        intTime_var = tk.DoubleVar()
        disp_var = tk.StringVar()
        name_var = tk.StringVar()
        dir_var = tk.StringVar()
        intTime_var.set(1)
        disp_var.set("0, 1, 2, 3, 4, 5, 6, 7")
        name_var.set('_D_Scan_Measurement')
        dir_var.set("C:/Users/jlauz/OneDrive/Bureau/Data FemtoQ/Julien/")
        
        
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        intTime_lbl = tk.Label(frame, text = 'Integration time [ms]:')
        disp_lbl = tk.Label(frame, text = 'Sequence of dispersion')
        name_lbl = tk.Label(frame, text = 'File Name')
        dir_lbl = tk.Label(frame, text = 'Save Directory')
        
        
        # Define entry boxes
        intTime_e = tk.Entry(frame, width = 6, textvariable = intTime_var)
        disp_e = tk.Entry(frame, width = 18, textvariable = disp_var)
        intTime_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(intTime_var))
        name_e = tk.Entry(frame, width=30, textvariable = name_var)
        dir_e = tk.Entry(frame, width=30, textvariable = dir_var)
        
        # Define position of all objects on the grid
        
        param_lbl.grid(row=0, column=0, columnspan=2, sticky='nsew')
        intTime_lbl.grid(row=1, column=0, sticky='nsw')
        intTime_e.grid(row=1, column=1, sticky='nse')
        disp_lbl.grid(row=3, column=0, sticky='nsw')
        disp_e.grid(row=3, column=1, sticky='nse')
        name_lbl.grid(row=23, column=0, sticky='nsw')
        name_e.grid(row=23, column=1, sticky='nse')
        dir_lbl.grid(row=25, column=0, sticky='nsw')
        dir_e.grid(row=25, column=1, sticky='nse')
        
        step1_lbl = tk.Label(frame, text = '')
        step1_lbl.grid(row=16, column=1, sticky='nsw')
        
        step2_lbl = tk.Label(frame, text = '')
        step2_lbl.grid(row=22, column=1, sticky='nsw')
        
        #i put these before the buttons because putting them after creates an error for some reason
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectro']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=11,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=13,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=15,column=0,sticky='nsew')

        self.start_button = tk.Button(frame, text='Start Experiment', state='normal', width=18,
                                      command=lambda: self.start_experiment(window_array=disp_var, intTime=intTime_var))
        self.start_button.grid(row=17, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=19, column=0, columnspan=2, sticky='nsew')
        
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save(directory=dir_var, name=name_var))
        self.save_button.grid(row=27, column=0, columnspan=2, sticky='nsew')
        
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=intTime_var))
        self.spectro_start_button.grid(row=7, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=9, column=0, sticky='nsew')
        
        self.spectro_connect_button = tk.Button(frame, text='Connect Spectrometer', state='normal', width=18,
                                                command=lambda: self.connect_spectrometer())
        self.spectro_connect_button.grid(row=5, column=0, columnspan=2, sticky='nsew')

        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        
        self.retrieve_button = tk.Button(frame, text='Fast retrieval', state='disabled',width=18,
                                        command=lambda: self.fast_retrieve())
        self.retrieve_button.grid(row=21,column=0,columnspan=2, sticky='nsew')

    def stop_experiment(self):
        self.running = False
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, window_array=None, intTime=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True
        self.window_array = np.fromstring(window_array.get(),dtype=float, sep=', ')
        try:
            self.wl=self.Spectro.spectro.wavelengths()
        except:
            self.wl=np.arange(1,513,1)
        
        #creating empty data matrix
        #try: 
        self.data_matrix = np.zeros((len(self.window_array), len(self.wl)))
            
        #except:
         #   self.data_matrix = np.zeros((len(self.window_array), 512))
        
        #measurement loop
        for i in range(len(self.window_array)):
            if not messagebox.askokcancel(title='INFO', message='Take measurement with ' + str(self.window_array[i]) +' mm of dispersion'):
                self.stop_experiment()
                break
            #take measurement from spectrometer
            ###############################################
            self.data_matrix[i] = self.Spectro.get_intensities()
            if np.isnan(self.data_matrix[i][0]):
                self.data_matrix[i] = 0.2*np.random.rand(len(self.wl))+np.exp(-((self.wl-(250+10*self.window_array[i]))/(120/(1+0.5*self.window_array[i])))**2)
                #for j in range(len(self.data_matrix[0])):
                 #   self.data_matrix[i][j] = np.random.rand()
           ############################################
           
            self.adjust_2dgraph()

        self.trace=self.data_matrix.copy()
        self.retrieve_button['state'] = 'normal'
        self.stop_experiment()
            
            
        
    def connect_spectrometer(self):
        self.Spectro.connect(exp_dependencie=True)
        self.spectro_start_button['state'] = 'normal'       
    
    def save(self, directory=None, name=None):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        try: np.savez(directory.get() + timeStamp + name.get() ,data = self.data_matrix ,dispersion = self.window_array, wavelengths=self.wl)
        except:
            messagebox.showerror("Error", "Error while saving, might be wrong directory.")
            
        # Going back to initial state
        self.running = False
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'

    def fast_retrieve(self):
        wavelengths = self.wl*1e-9
        delay = self.window_array                                     # Here delay is actually insertion
        trace = self.trace.copy()
        
        pulseRetrieved, pulseFrequencies = fqpr.shgDscan(filename='', inputDelays = delay, inputWavelengths = wavelengths, inputTrace = trace, makeFigures = False)
        
        
        
        t = timeRetrieved
        E = pulseRetTime
        
        pulseTime = np.abs(E)**2
        pulseTime /= pulseTime.max()
        pulseFreq = np.abs(pulseRetrieved)**2
        pulseFreq /= pulseFreq.max()
        pulsePhase = np.unwrap(np.angle(pulseRetrieved))
        
        
        iiOverHM = np.argwhere(pulseTime>=0.5).flatten()
        
        t00 = t[iiOverHM[0]-1]
        t01  = t[iiOverHM[0]]
        s00 = pulseTime[iiOverHM[0]-1]
        s01  = pulseTime[iiOverHM[0]]
        
        t10 = t[iiOverHM[-1]]
        t11  = t[iiOverHM[-1]+1]
        s10 = pulseTime[iiOverHM[-1]]
        s11  = pulseTime[iiOverHM[-1]+1]
        
        a0 = (s01-s00)/(t01-t00)
        b0 = s00-a0*t00
        t0 = (0.5-b0) / a0 * 1e15
        
        a1 = (s11-s10)/(t11-t10)
        b1 = s10-a1*t10
        t1 = (0.5-b1) / a1 * 1e15
        
        self.fwhm_var.set(round(abs(t1-t0),1))
        
        
        pulse_time_graph = self.graph_dict['Retrieved pulse (time)']
        pulse_time_graph.axes.set_xlim([t[0]*1e15,t[-1]*1e15])
        pulse_time_graph.axes.set_ylim([0,1])
        
        pulse_time_graph.Line.set_xdata(t*1e15)
        pulse_time_graph.Line.set_ydata(pulseTime/np.max(pulseTime))
        pulse_time_graph.update_graph()
        
        v0 = np.trapz(pulseFreq*pulseFrequencies,pulseFrequencies) / np.trapz(pulseFreq,pulseFrequencies)
        deltaV = np.sqrt( np.trapz(pulseFreq*(pulseFrequencies-v0)**2,pulseFrequencies) / np.trapz(pulseFreq,pulseFrequencies) )
        
        pulse_freq_graph = self.graph_dict['Retrieved pulse (frequency)']
        
        
        if self.phaseExists is False:
            self.pulse_spectralPhase_graph = pulse_freq_graph.axes.twinx()
            self.LinePhase, = self.pulse_spectralPhase_graph.plot([],[],'--k')
            self.pulse_spectralPhase_graph.set_ylabel('Spectral phase [rad]')
            self.phaseExists = True
        
        
        pulse_freq_graph.axes.set_xlim([(v0-3*deltaV)/1e12,(v0+3*deltaV)/1e12])
        pulse_freq_graph.axes.set_ylim([0,1])
        
        pulse_freq_graph.Line.set_xdata(pulseFrequencies/1e12)
        pulse_freq_graph.Line.set_ydata(pulseFreq/np.max(pulseFreq))
        
        
        IIplot = pulseFreq > pulseFreq.max()/100
        
        pulsePhase -= np.average(pulsePhase[IIplot],weights = np.abs(pulseFreq[IIplot])**2)
       
        phasemax = pulsePhase[IIplot].max()
        phasemin = pulsePhase[IIplot].min()
        self.pulse_spectralPhase_graph.set_ylim(phasemin,phasemax)

        self.LinePhase.set_xdata(pulseFrequencies[IIplot]/1e12)
        self.LinePhase.set_ydata(pulsePhase[IIplot])
        pulse_freq_graph.update_graph()


    def adjust_2dgraph(self):#, step=None):
# =============================================================================
#         step = step.get()
#         if step == 0:
#             step=1
# =============================================================================
        #try:
         #    wl = len(self.Spectro.spectro.wavelengths())
        #except:
         #   return
        
        parent2d = self.graph_dict["D-Scan trace"].parent
        self.graph_dict["D-Scan trace"].destroy_graph()
        #print(wl, step)
        self.graph_dict["D-Scan trace"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size= self.data_matrix.shape)
       #trace = (self.data_matrix-np.min(self.data_matrix))
       #trace = trace/np.max(trace)
        trace = np.flipud(self.data_matrix/self.data_matrix.max())
        aspectRatio = len(self.data_matrix[0])/(2*len(self.data_matrix[:, 0]))
        
        self.graph_dict["D-Scan trace"].axes.set_aspect(aspectRatio)
       
        self.graph_dict["D-Scan trace"].change_data(trace,False)
        self.graph_dict["D-Scan trace"].im.set_extent((self.wl[0], self.wl[-1], self.window_array[0], self.window_array[-1]))
        #aspectRatio = abs((self.timeDelay[-1]-self.timeDelay[0])/(self.wl_crop[0]-self.wl_crop[-1]))
        
        #Setting tick positions and labels
        disp_ticks = []
        step = (self.window_array[-1]-self.window_array[0])/(len(self.window_array)-1)
        i=self.window_array[0]
        while i<self.window_array[-1]:
            disp_ticks.append(i)
            i += step
        disp_ticks.append(self.window_array[-1])
        #messagebox.showinfo("bfobf", disp_ticks)
        #wl_ticks = []
        #i=self.wl[0]
        #while i<self.wl[-1]:
        #    wl_ticks.append(i)
        #    i += 100
        
        #self.graph_dict["D-Scan trace"].axes.set_xticks(ticks = wl_ticks)
        self.graph_dict["D-Scan trace"].axes.set_yticks(ticks = disp_ticks, labels = self.window_array)
        
        self.graph_dict["D-Scan trace"].axes.set_xlabel('Wavelengths [nm]')
        self.graph_dict["D-Scan trace"].axes.set_ylabel('Dispersion  Length [mm]')
        cbar = self.graph_dict["D-Scan trace"].Fig.colorbar(self.graph_dict["D-Scan trace"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["D-Scan trace"].update_graph()
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.sub_dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.spectro_connect_button['state'] = 'disabled'
        self.running = True
        
        #self.Spectro.set_trigger(0)         #Setting an external hardware edge trigger
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'disabled'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'
        self.start_button['state'] = 'normal'
        self.spectro_connect_button['state'] = 'normal'

class PUMA:
    def __init__(self, mainf=None):
        """
        The constructor for your Experiment.

        Parameters:
            mainf : This is the Mainframe, it cannot be anything else.
        """
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.Spectro = mainf.Frame[3].Spectro

    def create_frame(self, frame):
        """
        This function is used to create the free frame mentionned in the
        CreateLayout.This is where you place all of the widget you desire to
        have in your experiment.

        Parameters:
            frame : This is the section attributed to your widget in the big
            Experiment frame.
        """
        # Define variables
                # PI stage
        intTime_var = tk.DoubleVar()
        gdd_var = tk.DoubleVar()
        tod_var = tk.DoubleVar()
        fod_var = tk.DoubleVar()
        scg_var = tk.StringVar()
        pump_var = tk.StringVar()
        name_var = tk.StringVar()
        dir_var = tk.StringVar()
        intTime_var.set(1)
        gdd_var.set(0)
        tod_var.set(0)
        fod_var.set(0)
        scg_var.set('Documents/GitHub/femtoQ-Intruments/Labo_Env/ultrafastGUI/measurements/Reference_SCG_Spectrum.npy')
        pump_var.set('Documents/GitHub/femtoQ-Intruments/Labo_Env/ultrafastGUI/measurements/Reference_Pump_Spectrum.npy')
        name_var.set('_PUMA_Measurement')
        dir_var.set("C:/Users/jlauz/OneDrive/Bureau/Data FemtoQ/Julien/")
        

        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        intTime_lbl = tk.Label(frame, text = 'Integration time [ms]:')
        gdd_lbl = tk.Label(frame, text = 'Group delay dispersion')
        tod_lbl = tk.Label(frame, text = 'Third order dispersion')
        fod_lbl = tk.Label(frame, text = 'Fourth order dispersion')
        scg_lbl = tk.Label(frame, text = 'Reference SCG spectrum')
        pump_lbl = tk.Label(frame, text = 'Reference pump spectrum')
        name_lbl = tk.Label(frame, text = 'File Name')
        dir_lbl = tk.Label(frame, text = 'Save Directory')
        
        
        
        # Define entry boxes
        intTime_e = tk.Entry(frame, width = 6, textvariable = intTime_var)
        gdd_e = tk.Entry(frame, width = 6, textvariable = gdd_var)
        tod_e = tk.Entry(frame, width = 6, textvariable = tod_var)
        fod_e = tk.Entry(frame, width = 6, textvariable = fod_var)
        scg_e = tk.Entry(frame, width = 30, textvariable = scg_var)
        pump_e = tk.Entry(frame, width = 30, textvariable = pump_var)
        intTime_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(intTime_var))
        name_e = tk.Entry(frame, width=30, textvariable = name_var)
        dir_e = tk.Entry(frame, width=30, textvariable = dir_var)
        
        # Define position of all objects on the grid
        
        param_lbl.grid(row=0, column=0, columnspan=2, sticky='nsew')
        intTime_lbl.grid(row=1, column=0, sticky='nsw')
        intTime_e.grid(row=1, column=1, sticky='nse')
        gdd_lbl.grid(row=3, column=0, sticky='nsw')
        gdd_e.grid(row=3, column=1, sticky='nse')
        tod_lbl.grid(row=5, column=0, sticky='nsw')
        tod_e.grid(row=5, column=1, sticky='nse')
        fod_lbl.grid(row=7, column=0, sticky='nsw')
        fod_e.grid(row=7, column=1, sticky='nse')
        scg_lbl.grid(row=9, column=0, sticky='nsw')
        scg_e.grid(row=9, column=1, sticky='nse')
        pump_lbl.grid(row=11, column=0, sticky='nsw')
        pump_e.grid(row=11, column=1, sticky='nse')
        name_lbl.grid(row=31, column=0, sticky='nsw')
        name_e.grid(row=31, column=1, sticky='nse')
        dir_lbl.grid(row=33, column=0, sticky='nsw')
        dir_e.grid(row=33, column=1, sticky='nse')
        
        step1_lbl = tk.Label(frame, text = '')
        step1_lbl.grid(row=24, column=1, sticky='nsw')
        
        step2_lbl = tk.Label(frame, text = '')
        step2_lbl.grid(row=30, column=1, sticky='nsw')
        
        #i put these before the buttons because putting them after creates an error for some reason
        def get_dark_spectrum(self):
            self.Spectro.measure_darkspectrum()
            self.sub_dark_button['state']='normal'
        
        def remove_dark(self):
            self.Spectro.dark_spectrum = not self.Spectro.dark_spectrum
        
        def rescale(self):
            S = self.Spectro.get_intensities()
            spectro_graph = self.graph_dict['Spectro']
            spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
            spectro_graph.update_graph()
        
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=19,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=21,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=23,column=0,sticky='nsew')

        self.start_button = tk.Button(frame, text='Start Experiment', state='normal', width=18,
                                      command=lambda: self.start_experiment(gdd=gdd_var, tod=tod_var, fod=fod_var, scg=scg_var, pump=pump_var, intTime=intTime_var))
        self.start_button.grid(row=25, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=27, column=0, columnspan=2, sticky='nsew')
        
        self.save_button = tk.Button(frame, text='Save measurement', state='disabled',width=18,
                                        command=lambda: self.save(directory=dir_var, name=name_var))
        self.save_button.grid(row=35, column=0, columnspan=2, sticky='nsew')
        
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=intTime_var))
        self.spectro_start_button.grid(row=15, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=17, column=0, sticky='nsew')
        
        self.spectro_connect_button = tk.Button(frame, text='Connect Spectrometer', state='normal', width=18,
                                                command=lambda: self.connect_spectrometer())
        self.spectro_connect_button.grid(row=13, column=0, columnspan=2, sticky='nsew')

        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        
        self.retrieve_button = tk.Button(frame, text='Fast retrieval', state='disabled',width=18,
                                        command=lambda: self.fast_retrieve())
        self.retrieve_button.grid(row=29,column=0,columnspan=2, sticky='nsew')

    def stop_experiment(self):
        self.running = False
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, gdd=None, tod=None, fod=None, scg=None, pump=None, intTime=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
        self.save_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'disabled'
        self.running = True
        self.scg_spectrum = np.load(scg)
        self.pump_spectrum = np.load(pump)
        try:
            self.wl=self.Spectro.spectro.wavelengths()
        except:
            self.wl=np.arange(1,513,1)
        
        #creating empty data matrix
        #try: 
        self.data_matrix = np.zeros(len(self.wl))
            
        #except:
         #   self.data_matrix = np.zeros((len(self.window_array), 512))
        
        #verification
        plt.plot(self.scg_spectrum[0],self.scg_spectrum[1])
        plt.title('Reference spectrum for supercontinuum')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (W/m²)')
        plt.show()
        plt.plot(self.pump_spectrum[0],self.pump_spectrum[1])
        plt.title('Reference spectrum for pump pulses')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (W/m²)')
        plt.show()
        if not messagebox.askokcancel(title='INFO', message='Take measurement with previously shown reference spectrums'):
            self.stop_experiment()

        #take measurement from spectrometer
        ###############################################
        self.data_matrix = self.Spectro.get_intensities()
        if np.isnan(self.data_matrix[0]):
            self.data_matrix = 0.2*np.random.rand(len(self.wl))+np.exp(-((self.wl-(250+10*self.window_array[i]))/(120/(1+0.5*self.window_array[i])))**2)
            #for j in range(len(self.data_matrix[0])):
             #   self.data_matrix[i][j] = np.random.rand()
           ###########################################
        
        self.adjust_2dgraph()

        self.trace=self.data_matrix.copy()
        self.retrieve_button['state'] = 'normal'
        self.stop_experiment()
            
            
        
    def connect_spectrometer(self):
        self.Spectro.connect(exp_dependencie=True)
        self.spectro_start_button['state'] = 'normal'       
    
    def save(self, directory=None, name=None):
        timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %Hh%M_%S")
        try: np.savez(directory.get() + timeStamp + name.get() ,data = self.data_matrix ,dispersion = self.window_array, wavelengths=self.wl)
        except:
            messagebox.showerror("Error", "Error while saving, might be wrong directory.")
            
        # Going back to initial state
        self.running = False
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.save_button['state'] = 'normal'

    def fast_retrieve(self):
        wavelengths = self.wl*1e-9
        delay = self.window_array    # Here delay is actually insertion
        trace = self.trace.copy()
        
        pulseRetrieved, pulseFrequencies = fqpr.shgDscan(filename='', inputDelays = delay, inputWavelengths = wavelengths, inputTrace = trace, makeFigures = False)
        
        
        
        t = timeRetrieved
        E = pulseRetTime
        
        pulseTime = np.abs(E)**2
        pulseTime /= pulseTime.max()
        pulseFreq = np.abs(pulseRetrieved)**2
        pulseFreq /= pulseFreq.max()
        pulsePhase = np.unwrap(np.angle(pulseRetrieved))
        
        
        iiOverHM = np.argwhere(pulseTime>=0.5).flatten()
        
        t00 = t[iiOverHM[0]-1]
        t01  = t[iiOverHM[0]]
        s00 = pulseTime[iiOverHM[0]-1]
        s01  = pulseTime[iiOverHM[0]]
        
        t10 = t[iiOverHM[-1]]
        t11  = t[iiOverHM[-1]+1]
        s10 = pulseTime[iiOverHM[-1]]
        s11  = pulseTime[iiOverHM[-1]+1]
        
        a0 = (s01-s00)/(t01-t00)
        b0 = s00-a0*t00
        t0 = (0.5-b0) / a0 * 1e15
        
        a1 = (s11-s10)/(t11-t10)
        b1 = s10-a1*t10
        t1 = (0.5-b1) / a1 * 1e15
        
        self.fwhm_var.set(round(abs(t1-t0),1))
        
        
        pulse_time_graph = self.graph_dict['Retrieved pulse (time)']
        pulse_time_graph.axes.set_xlim([t[0]*1e15,t[-1]*1e15])
        pulse_time_graph.axes.set_ylim([0,1])
        
        pulse_time_graph.Line.set_xdata(t*1e15)
        pulse_time_graph.Line.set_ydata(pulseTime/np.max(pulseTime))
        pulse_time_graph.update_graph()
        
        v0 = np.trapz(pulseFreq*pulseFrequencies,pulseFrequencies) / np.trapz(pulseFreq,pulseFrequencies)
        deltaV = np.sqrt( np.trapz(pulseFreq*(pulseFrequencies-v0)**2,pulseFrequencies) / np.trapz(pulseFreq,pulseFrequencies) )
        
        pulse_freq_graph = self.graph_dict['Retrieved pulse (frequency)']
        
        
        if self.phaseExists is False:
            self.pulse_spectralPhase_graph = pulse_freq_graph.axes.twinx()
            self.LinePhase, = self.pulse_spectralPhase_graph.plot([],[],'--k')
            self.pulse_spectralPhase_graph.set_ylabel('Spectral phase [rad]')
            self.phaseExists = True
        
        
        pulse_freq_graph.axes.set_xlim([(v0-3*deltaV)/1e12,(v0+3*deltaV)/1e12])
        pulse_freq_graph.axes.set_ylim([0,1])
        
        pulse_freq_graph.Line.set_xdata(pulseFrequencies/1e12)
        pulse_freq_graph.Line.set_ydata(pulseFreq/np.max(pulseFreq))
        
        
        IIplot = pulseFreq > pulseFreq.max()/100
        
        pulsePhase -= np.average(pulsePhase[IIplot],weights = np.abs(pulseFreq[IIplot])**2)
       
        phasemax = pulsePhase[IIplot].max()
        phasemin = pulsePhase[IIplot].min()
        self.pulse_spectralPhase_graph.set_ylim(phasemin,phasemax)

        self.LinePhase.set_xdata(pulseFrequencies[IIplot]/1e12)
        self.LinePhase.set_ydata(pulsePhase[IIplot])
        pulse_freq_graph.update_graph()


    def adjust_2dgraph(self):#, step=None):
# =============================================================================
#         step = step.get()
#         if step == 0:
#             step=1
# =============================================================================
        #try:
         #    wl = len(self.Spectro.spectro.wavelengths())
        #except:
         #   return
        
        parent2d = self.graph_dict["D-Scan trace"].parent
        self.graph_dict["D-Scan trace"].destroy_graph()
        #print(wl, step)
        self.graph_dict["D-Scan trace"] = Graphic.TwoDFrame(parent2d, axis_name=["New name", "New name2"],
                                                       figsize=[2,2], data_size= self.data_matrix.shape)
       #trace = (self.data_matrix-np.min(self.data_matrix))
       #trace = trace/np.max(trace)
        trace = np.flipud(self.data_matrix/self.data_matrix.max())
        aspectRatio = len(self.data_matrix[0])/(2*len(self.data_matrix[:, 0]))
        
        self.graph_dict["D-Scan trace"].axes.set_aspect(aspectRatio)
       
        self.graph_dict["D-Scan trace"].change_data(trace,False)
        self.graph_dict["D-Scan trace"].im.set_extent((self.wl[0], self.wl[-1], self.window_array[0], self.window_array[-1]))
        #aspectRatio = abs((self.timeDelay[-1]-self.timeDelay[0])/(self.wl_crop[0]-self.wl_crop[-1]))
        
        #Setting tick positions and labels
        disp_ticks = []
        step = (self.window_array[-1]-self.window_array[0])/(len(self.window_array)-1)
        i=self.window_array[0]
        while i<self.window_array[-1]:
            disp_ticks.append(i)
            i += step
        disp_ticks.append(self.window_array[-1])
        #messagebox.showinfo("bfobf", disp_ticks)
        #wl_ticks = []
        #i=self.wl[0]
        #while i<self.wl[-1]:
        #    wl_ticks.append(i)
        #    i += 100
        
        #self.graph_dict["D-Scan trace"].axes.set_xticks(ticks = wl_ticks)
        self.graph_dict["D-Scan trace"].axes.set_yticks(ticks = disp_ticks, labels = self.window_array)
        
        self.graph_dict["D-Scan trace"].axes.set_xlabel('Wavelengths [nm]')
        self.graph_dict["D-Scan trace"].axes.set_ylabel('Dispersion  Length [mm]')
        cbar = self.graph_dict["D-Scan trace"].Fig.colorbar(self.graph_dict["D-Scan trace"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["D-Scan trace"].update_graph()
        
    def start_spectro(self, inte_time=None):
        self.dark_button['state'] = 'normal'
        self.sub_dark_button['state'] = 'normal'
        self.rescale_button['state'] = 'normal'
        self.spectro_stop_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'disabled'
        self.start_button['state'] = 'disabled'
        self.spectro_connect_button['state'] = 'disabled'
        self.running = True
        
        #self.Spectro.set_trigger(0)         #Setting an external hardware edge trigger
        self.Spectro.adjust_integration_time(inte_time)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)*1.1])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        
        while self.running is True:            
            wl = self.Spectro.spectro.wavelengths()
            S = self.Spectro.get_intensities()
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)     
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(S)
            spectro_graph.update_graph()
            
    def stop_spectro(self):
        self.running = False
        self.dark_button['state'] = 'disabled'
        self.sub_dark_button['state'] = 'disabled'
        self.rescale_button['state'] = 'disabled'
        self.spectro_stop_button['state'] = 'disabled'
        self.spectro_start_button['state'] = 'normal'
        self.start_button['state'] = 'normal'
        self.spectro_connect_button['state'] = 'normal'