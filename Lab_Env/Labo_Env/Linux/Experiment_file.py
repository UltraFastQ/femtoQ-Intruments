import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import Graphic


# Create a basic layont for every experiment
class CreateLayout:

    def __init__(self, function_class=None, main=None, window=None, graph_names={}, tools_names=[]):
        # function_class : This argument is the class of which you stored the experiment so it should be call as self,
        # window is the tkinter Frame in which this layout will be put into: should be the experiment Frame called in
        # the Main_Frame program
        if not window:
            pass
        # graph_names : This has to contain every graphic names. We could have for the withelight a delay induced for a
        # designed wavelength format should be : { 'Wavelength' : [datax, datay], ... } this can be called in the
        # class experiment if needed
        # tools_names : This argument should be a list of the item necessary : [ 'Monochromator', ...] the possible
        # options are : 'Monochromator', 'Spectrometer', 'Physics_Linear_Stage', 'Zurich'
        self.dependant_function = function_class(main=main)

        self.tools_names = tools_names

        def grid_options(dict_, tools_):

            rw = 0
            for tool in tools_:
                clm = 0
                for tk_module in dict_[tool]:
                    tk_module.grid(row=rw, column=clm, sticky='nsew')
                    clm += 1

                rw += 1

        def frame_switch(dict_, new):

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

        for item in graph_names:
            values.append(item)
            graph_possible[item] = tk.Frame(self.graph_frame)
            self.dependant_function.graph_dict[item] = Graphic.GraphicFrame(graph_possible[item],
                                                                            axis_name=graph_names[item])
            graph_possible[item].bind('<Configure>', self.dependant_function.graph_dict[item].change_dimensions)

        graph_available['value'] = tuple(values)
        graph_available.current(0)
        frame_switch(graph_possible, graph_available.get())

        graph_available.bind('<<ComboboxSelected>>', lambda x: frame_switch(graph_possible, graph_available.get()))
        option_window = ttk.LabelFrame(self.containing_frame, text='Needed Option')
        option_window.grid(row=0, column=0, sticky='nsew')

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

        for i in range(1, 4):
            for j in range(1, 3):
                self.containing_frame.grid_columnconfigure(i, weight=1)
                self.containing_frame.grid_rowconfigure(j, weight=1)
        for i in range(1):
            for j in range(1):
                self.graph_frame.grid_columnconfigure(0, weight=1)
                self.graph_frame.grid_rowconfigure(0, weight=1)

    def update_options(self, tool):

        current_state = self.state_dict[tool].get()
        if current_state == 'disconnected':
            self.state_dict[tool].set('ready')
        if current_state == 'ready':
            self.state_dict[tool].set('disconnected')

        all_state = []

        for tool in self.state_dict:
            state = self.state_dict[tool].get()
            all_state.append(state)

        if all(all_state) == 'ready':
            self.dependant_function.start_button.state(['normal'])


# Here is the template for the experiement
class TemplateForExperiment:

    # This class is implicitly called in the main frame
    def __init__(self, main=None):
        # here are the initiation of the item that will be called throughout the program as self
        self.empty_var = []
        self.graph_dict = {}

    def create_frame(self, frame):

        # this function contains at minimum :
        self.start_button = tk.Button(frame, text='Start Experiment', state='disabled', width=18,
                                      command=lambda: self.start_experiment())
        self.start_button.grid(row=10, column=0, columnspan=2, sticky='nsew')
        # The other lines are required option you would like to change before an experiment with the correct binding
        # and/or other function you can see the WhiteLight for more exemple.

    def start_experiment(self):

        # Here should be all of your experiment for here we have a huge program where we print literally nothing
        print(self.empty_var)


class WhiteLight:

    def __init__(self, ZiData = None, PiData = None, main=None):

        # Variables Initialization
        self.main = main
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

        print('hello')

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

