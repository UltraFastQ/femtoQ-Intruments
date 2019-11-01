"Python program used to combine all instrument functions"
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import matplotlib.pyplot as plt
import numpy as np
import Graphic


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
                file_data = np.array([abs_vals[:i,:], values[:i, :]])
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


class Electro_Optic_Sampling:

    # This class is implicitly called in the main frame
    def __init__(self, mainf = None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}
        self.PI = mainf.Frame[2].Linstage

    def create_frame(self, frame):
        # Define labels
        pos_lbl = tk.Label(frame, text = 'Go to position (mm):')
        vel_lbl = tk.Label(frame, text = 'Set velocity to:')
        param_lbl = tk.Label(frame, text = 'Experiment parameters')
        min_lbl = tk.Label(frame, text = 'Min. pos. (mm):')
        max_lbl = tk.Label(frame, text = 'Max. pos. (mm):')
        step_lbl = tk.Label(frame, text = 'Step size (um):')
        utime_lbl = tk.Label(frame, text='Update graph after [s]:')
        # Define buttons and their action
        con_b = tk.Button(frame, text='Connect PI linear stage',
                                      command=lambda: self.PI.connect_identification(dev_name='C-863.11',
                                                                                           exp_dependencie=True))
        # Define variables
        pos_var = tk.DoubleVar()
        vel_var = tk.DoubleVar()
        min_var = tk.DoubleVar()
        max_var = tk.DoubleVar()
        step_var = tk.DoubleVar()
        utime_var = tk.IntVar()
        pos_var.set(0)
        vel_var.set(1)
        min_var.set(-50)
        max_var.set(50)
        step_var.set(100)
        utime_var.set(1)

        # Define entry boxes
        pos_e = tk.Entry(frame, width = 6, textvariable = pos_var)
        vel_e = tk.Entry(frame, width = 6, textvariable = vel_var)
        min_e = tk.Entry(frame, width = 6, textvariable = min_var)
        max_e = tk.Entry(frame, width = 6, textvariable = max_var)
        step_e = tk.Entry(frame, width = 6, textvariable = step_var)
        utime_e = tk.Entry(frame, width=6, textvariable = utime_var)

        # Define position of all objects on the grid
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
        pos_e.bind('<Return>', lambda e: self.PI.go_2position(pos_var))
        vel_e.bind('<Return>', lambda e: self.PI.set_velocity(vel_var))

        # this function contains at minimum :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment(max_pos=max_var, min_pos=min_var, step=step_var, progress=p_bar, update_time=utime_var))
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.
        self.stop_button = tk.Button(frame, text='Stop Experiment', state='disabled', width=18,
                                     command=lambda: self.stop_experiment())
        self.stop_button.grid(row=12, column=0, columnspan=2, sticky='nsew')

    def stop_experiment(self):
        self.running = False

    def start_experiment(self, min_pos=None, max_pos=None, step = None, progress=None, update_time=None):

        self.stop_button['state'] = 'normal'
        self.start_button['state'] = 'disabled'
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

        if not max_pos and not min_pos:
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
        last_gu = time.time()
        scan_graph = self.graph_dict['Scanning']
        scan_graph.axes.set_ylim([min_pos, max_pos])
        scan_graph.axes.set_xlim([0, nsteps])
        scan_graph.Line.set_xdata([])
        scan_graph.Line.set_ydata([])
        scan_graph.Line.set_marker('o')
        scan_graph.Line.set_markersize(2)
        scan_graph.update_graph()

            # Main scanning and measurements
        for i in range(nsteps+1):
            # Move stage to required position
            self.PI.device.MOV(self.PI.axes,move[i])
            pitools.waitontarget(self.PI.device)
            # Measure real position
            pos[i] = self.PI.device.qPOS()['1']
            # Actualise progress bar
            if progress:
                progress['value'] = (i)/(nsteps)
                progress.update()
            # Actualise graph if required
            if (time.time() - last_gu) > update_time:
                scan_graph.Line.set_xdata(iteration[:i])
                scan_graph.Line.set_ydata(pos[:i])
                scan_graph.update_graph()
                last_gu = time.time()
            if not self.running:
                break
        if not self.running:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.device.MOV(self.PI.axes, 0)
            pitools.waitontarget(self.PI.device)
            messagebox.showinfo(title='Error', message='Experiment was aborted')
        else:
            return_vel = tk.IntVar()
            return_vel.set(10)
            self.PI.set_velocity(return_vel)
            self.PI.device.MOV(self.PI.axes, 0)
            pitools.waitontarget(self.PI.device)
            scan_graph.Line.set_xdata(iteration)
            scan_graph.Line.set_ydata(pos)
            scan_graph.update_graph()
            dp = np.std(pos-move)
            messagebox.showinfo(title='INFO', message='Measurements is done.' + str(nsteps) + ' Steps done with displacement repeatability of ' + str(round(dp*1000,2)) + ' micrometer')

        # Going back to initial state
        self.running = False
        progress['value'] = 0
        progress.update()
        self.stop_button['state'] = 'disabled'
        self.start_button['state'] = 'normal'
