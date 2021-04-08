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
import serial
import os

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

















class LaserCooling:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage
        self.Spectro = mainf.Frame[3].Spectro
        
    def pos_2_delay(self,zero,pos):
            return  2*(zero-pos)*1e9/(299792458)
        
    def delay_2_pos(self,delay):
            return (299792458)*delay/(2e6)
        
    def create_frame(self, frame):
        # Define labels
                # Delay line
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        filename_lbl = tk.Label(frame, text = 'File name:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        zero_lbl = tk.Label(frame, text = 'Pos. Zero Delay (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
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
        max_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        zero_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        # delay_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        self.pos_var.set(0)
        self.vel_var.set(1)
        self.filename_var.set("2021-MM-JJ_Test_1")
        self.vel_disp.set(2)
        min_var.set(38.75)
        max_var.set(45)
        zero_var.set(-30.025)
        step_var.set(3)
        # delay_var.set(-1*self.pos_2_delay(0,step_var.get()/1000))
        # step_var.set(self.delay_2_pos(delay_var.get()))
        utime_var.set(1)

        # Define entry boxes
                # PI stage
        pos_e = tk.Entry(frame, width = 6, textvariable = self.pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = self.vel_var)
        filename_e = tk.Entry(frame, width = 18, textvariable = self.filename_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        zero_e = tk.Entry(frame, width = 6, textvariable = zero_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
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
        min_e.grid(row=6, column=1, sticky='nse')
        max_lbl.grid(row=7, column=0, sticky='nsw')
        max_e.grid(row=7, column=1, sticky='nse')
        zero_lbl.grid(row=8, column=0, sticky='nsw')
        zero_e.grid(row=8, column=1, sticky='nse')
        step_lbl.grid(row=9, column=0, sticky='nsw')
        step_e.grid(row=9, column=1, sticky='nse')
        # delay_lbl.grid(row=9, column=0, sticky='nsw')
        # delay_e.grid(row=9, column=1, sticky='nse')
        utime_lbl.grid(row=10, column=0, sticky='nsw')
        utime_e.grid(row=10, column=1, sticky='nse')

        p_bar = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
        p_bar.grid(row=13, column=0, sticky='nsew', columnspan=2)
        p_bar['maximum'] = 1
        # Select a key and its effect when pressed in an entry box
            # PI stage
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(self.pos_var))
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
        cons_b.grid(row=15, column=0, columnspan=2, sticky='nsew')
        
        inte_lbl = tk.Label(frame, text = 'Integration time (ms):')
        inte_var = tk.IntVar()
        inte_var.set(1)
        inte_e = tk.Entry(frame, width = 6, textvariable = inte_var)
        inte_lbl.grid(row=16, column=0, sticky='nsw')
        inte_e.grid(row=16, column=1,sticky='nse')
        int_period_lbl = tk.Label(frame, text = 'Integration period (ms):')
        int_period_var = tk.IntVar()
        int_period_var.set(60000)
        int_period_e = tk.Entry(frame, width = 6, textvariable = int_period_var)
        int_period_lbl.grid(row=17, column=0, sticky='nsw')
        int_period_e.grid(row=17, column=1,sticky='nse')

        minwl_lbl = tk.Label(frame, text = 'min wl for integration(nm)')
        maxwl_lbl = tk.Label(frame, text = 'max wl for integration(nm)')
        minwl_var = tk.DoubleVar()
        maxwl_var = tk.DoubleVar()
        minwl_var.set(950)
        maxwl_var.set(1050)
        minwl_e = tk.Entry(frame, width = 6, textvariable = minwl_var)
        maxwl_e = tk.Entry(frame, width = 6, textvariable = maxwl_var)
        minwl_lbl.grid(row=18, column=0, sticky='nsw')
        maxwl_lbl.grid(row=19, column=0, sticky='nsw')
        minwl_e.grid(row=18, column=1, sticky='nse')
        maxwl_e.grid(row=19, column=1, sticky='nse')
        
        inte_e.bind('<Return>', lambda e: self.Spectro.adjust_integration_time(inte_var))
        
        self.dark_button = tk.Button(frame, text='Get dark spectrum', state='disabled',width=18,
                           command=lambda: get_dark_spectrum(self))
        self.dark_button.grid(row=22,column=0,sticky='nsew')
        
        self.sub_dark_button = tk.Button(frame, text='Substract dark spectrum', state='disabled',width=18,
                                    command=lambda: remove_dark(self))
        self.sub_dark_button.grid(row=23,column=0,sticky='nsew')
        
        self.rescale_button = tk.Button(frame, text='Rescale spectrum graph', state='disabled',width=18,
                                        command=lambda: rescale(self))
        self.rescale_button.grid(row=24,column=0,sticky='nsew')
        
        # Start & stop buttons :

        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, zero=zero_var, step=step_var, progress=p_bar, update_time=utime_var,
                                            inte_time=inte_var, int_period=int_period_var, minwl=minwl_var, maxwl=maxwl_var))
        self.start_button.grid(row=12, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=14, column=0, columnspan=2, sticky='nsew')

            # For spectrometer :
        self.spectro_start_button = tk.Button(frame, text='Start Spectrometer', state='disabled',width=18,
                                        command=lambda: self.start_spectro(inte_time=inte_var))
        self.spectro_start_button.grid(row=20, column=0, sticky='nsew')
        self.spectro_stop_button = tk.Button(frame, text='Stop Spectrometer', state='disabled', width=18,
                                             command=lambda: self.stop_spectro())
        self.spectro_stop_button.grid(row=21, column=0, sticky='nsew')
        

      


        
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
        


    def adjust_2dgraph(self):#, step=None):
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
                                                       figsize=[2,2], data_size= np.transpose(self.trace).shape)
        self.graph_dict["Pump_Probe"].change_data(np.transpose(self.trace),False)
        self.graph_dict["Pump_Probe"].im.set_extent((self.timeDelay[0],self.timeDelay[-1],self.wl_crop[-1],self.wl_crop[0]))
        aspectRatio = abs((self.timeDelay[-1]-self.timeDelay[0])/(self.wl_crop[0]-self.wl_crop[-1]))
        self.graph_dict["Pump_Probe"].axes.set_aspect(aspectRatio)
        self.graph_dict["Pump_Probe"].axes.set_xlabel('Delay [ps]')
        self.graph_dict["Pump_Probe"].axes.set_ylabel('Wavelengths [nm]')
        cbar = self.graph_dict["Pump_Probe"].Fig.colorbar(self.graph_dict["Pump_Probe"].im)
        cbar.set_label('Normalized intensity')
        self.graph_dict["Pump_Probe"].update_graph()

        
        
    def stop_experiment(self):
        self.running = False
        self.spectro_start_button['state'] = 'normal'

    def start_experiment(self, min_pos=None, max_pos=None, zero=None, step = None, progress=None, update_time=None,
                         inte_time=None, int_period=None, minwl=None, maxwl=None):

        filename_final=self.filename_var.get()
        try:
            os.mkdir("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final))        
        except OSError:
            l=1
        else:
            l=0

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
        zero=zero.get()
        step = step.get()/1000
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
        nsteps = int(np.ceil((max_pos - min_pos)/step))
        iteration = np.linspace(0, nsteps, nsteps+1)
        move = np.linspace(max_pos, min_pos, nsteps+1)
        pos = np.zeros(nsteps+1)

        self.PI.set_velocity(vel=self.vel_disp)
        self.PI.go_2position(move[0]-0.001)
        self.PI.set_velocity(vel=self.vel_var)
        
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


        # Define Arduino
        # arduino=serial.Serial('COM9',115200,timeout=None)


            # Spectro
        self.Spectro.set_trigger(0)
        wl = self.Spectro.spectro.wavelengths()
        S = self.Spectro.get_intensities()
        self.Spectro.adjust_integration_time(inte_time)
        spectro_graph = self.graph_dict['Spectro']
        spectro_graph.axes.set_ylim([np.min(S),np.max(S)])
        spectro_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        spectro_graph.Line.set_xdata(wl)
        spectro_graph.Line.set_ydata(S)
        minwl = minwl.get()
        maxwl = maxwl.get()

        self.trace = np.zeros((nsteps+1,wl.shape[0]))
        signal_graph = self.graph_dict['Signal']
        signal_graph.axes.set_ylim([1,-1])
        signal_graph.axes.set_xlim([np.min(wl),np.max(wl)])
        signal_graph.Line.set_xdata(wl)
        signal_graph.Line.set_ydata(self.trace[0])


        
            # Main scanning and measurements
        for i in range(nsteps+1):
            
            try:
                os.mkdir("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\spectrum")
            except OSError:
                l=1
            else:
                l=0

            
            # Move stage to required position
            self.PI.go_2position(move[i])
            # Measure real position
            pos[i] = self.PI.get_position()
            

            spectra_brut=[]
            
            
            start_daq=time.time()
            while time.time()-start_daq < int_period/1000. :
                spectra_brut.append(np.array(self.Spectro.get_intensities()))

            
            spectra_brute=np.array(spectra_brut)
            
            spectra_brute[spectra_brute==0]=1
            
            # f1=open("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\spectrum\position" + str(i) + ".npy",'a')
            
            # f1.truncate(0)
            
            np.save("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\spectrum\position" + str(i) + ".npy",spectra_brute)

                  
            # trace_brut=np.average((np.array(spectra_brute[1])-np.array(spectra_brute[0]))/np.array(spectra_brute[0]),axis=0)
            # self.trace[i] = trace_brut


            scan_graph.Line.set_xdata(iteration[:i])
            scan_graph.Line.set_ydata(pos[:i])
            scan_graph.update_graph()
            # signal_graph.Line.set_xdata(wl)
            # signal_graph.Line.set_ydata(self.trace[i])
            # signal_graph.axes.set_ylim([np.min(self.trace[i])*1.1,np.max(self.trace[i])*1.1])
            # signal_graph.update_graph()            
            
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps) 
                progress.update()
                
            if not self.running:
                break
               
        # f1.close()
        
        # np.savetxt("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\_" + str(filename_final) + ".txt",self.trace, fmt="%s", delimiter=", ")
        np.save("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\_" + str(filename_final) + "_pos.npy",pos)
        np.save("E:\Gabriel\Laser_Cooling_Measurement\_" + str(filename_final) + "\_" + str(filename_final) + "_wl.npy",wl)
        
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
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
                #Spectro signal and integrated signal
            spectro_graph.Line.set_xdata(wl)
            spectro_graph.Line.set_ydata(self.trace[i])
            spectro_graph.update_graph()

            
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')



        # Final calculations
        self.timeDelay =self.pos_2_delay(zero,pos)
        


        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
        self.spectro_start_button['state'] = 'normal'
        # self.adjust_2dgraph()        




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
        
        
        



