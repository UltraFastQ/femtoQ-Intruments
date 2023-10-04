"Python Seabreeze wrapper for the program"
import tkinter as tk
import numpy as np
from femtoQ import tools as fQ
import scipy.constants as sc
from pathlib import Path
from tkinter import messagebox
import Graphic


class Spectro:
    """
    This class is used to wrap the Seabreeze open source package into the
    tkinter window. It uses different function of the seabreeze package to
    collect data and display the right information on the graphic. It contains
    various function available to the user in the tkinter window.

    Attributes:
        spectro : This object is a Seabreeze reprensenting the device connected
        wv_graphic : This is an instance of the GraphicFrame class of
        SubGraphFrame depending if you are using wavelength of both
        wavelengths and fft.
        fft_graphic : This is an instance of the SubGraphFrame class but is
        only available when dual display is selected.
        dual : This is the instance of subGraphFrame containing both
        fft_graphic and wv_graphic when you select the FFT + Wavelength
        graph.
        mainf : This is a window that reprensent the MainFrame if it exist when
        sent it is used to update the experiment window when used within the
        MainFrame.
        max_intensitie : This is a value used to update the graphic in the
        tkinter window so all intensities in the graph are always visible.
        dark_spectrum : Boolean value used to know if you need to substarct the
        dark spectrum.
        dark_array : Array calculated with one measurement of the spectrum when
        you select the dark spectrum box.
        eff_divider : Boolean value used to know if you need to divide the
        effeciency divider.
        eff_array : Array extracted from the folder with a same name. This is
        suppose to be a way to obtain measured value that are not dependent of
        the efficiency of the spectrometer.
        fft_autoupdate : This is a variable to autoupdate the limites of the
        fft graphic at every iteration so you see only what is necessary.
        normalizing : Boolean value to make the graphics normalized.
    """
    def __init__(self, graphic=None, mainf=None):
        """
        The constructor for the Spectro Class.

        Parameters:
            graphic : Graphic class or equivalent to have at minimum the
            wavelength graphic.
            mainf : MainFrame object to be only passed if you have the
            Mainwindow and you want to update the experiment window
        """
        self.spectro = None
        self.wv_graphic = graphic
        self.fft_graphic = None
        self.dual = None
        self.mainf = mainf
        self.max_intensitie = 0
        self.dark_spectrum = False
        self.dark_array = None
        self.eff_divider = False
        self.eff_array = None
        self.fft_autoupdate = False
        self.normalizing = False

    def connect(self, exp_dependencie=False):
        """
        This function is to connect the Spectrometer.

        Parameters:
            exp_dependencie : This is a boolean value that tells the user if
            the user wants to update the experiment window
        """
        # This function is to open a window if you have more than one device
        # connected. This function is still untested. How it works is that it
        # creates a window that will ask you to select one device to be
        # connected.
        def device_popup(items=None):
            device = PopUp(values=items).mainloop()
            device = device.value
            return device
        # Uses of Seabreeze to connect the device and retain it's information
        # in memory.
        import seabreeze
        seabreeze.use('cseabreeze')
        import seabreeze.spectrometers as sb
        devices = sb.list_devices()
        if type(devices) == list and devices:
            if len(devices) > 1:
                device = device_popup(value=devices, lib_=sb)
            else:
                device = devices[0]
            self.spectroType = 'ocean'
            self.spectro = sb.Spectrometer(device)
            self.spectro.integration_time_micros(1000)
            #return 1
        else:
            import avaspec
            ret = avaspec.AVS_Init(-1)
            ret = avaspec.AVS_UpdateUSBDevices()
            ret = avaspec.AVS_GetList()
            if ret:
                self.spectroType = 'avantes'
                self.spectro = avaspec.AVS_Activate(ret[0])
                config = avaspec.DeviceConfigType
                ret = avaspec.AVS_GetParameter(self.spectro)
                ret = avaspec.AVS_UseHighResAdc(self.spectro, True)
                self.spectroconfig = avaspec.MeasConfigType
                self.spectroconfig.m_StartPixel = 0
                self.spectroconfig.m_StopPixel = avaspec.AVS_GetNumPixels(self.spectro) - 1
                self.spectroconfig.m_IntegrationTime = 1 #in milliseconds
                self.spectroconfig.m_IntegrationDelay = 0 #in FPGA clock cycles
                self.spectroconfig.m_NrAverages = 1
                self.spectroconfig.m_CorDynDark_m_Enable = 0  # nesting of types does NOT work!!
                self.spectroconfig.m_CorDynDark_m_ForgetPercentage = 100
                self.spectroconfig.m_Smoothing_m_SmoothPix = 0
                self.spectroconfig.m_Smoothing_m_SmoothModel = 0
                self.spectroconfig.m_SaturationDetection = 0
                self.spectroconfig.m_Trigger_m_Mode = 0
                self.spectroconfig.m_Trigger_m_Source = 0
                self.spectroconfig.m_Trigger_m_SourceType = 0
                self.spectroconfig.m_Control_m_StrobeControl = 0
                self.spectroconfig.m_Control_m_LaserDelay = 0
                self.spectroconfig.m_Control_m_LaserWidth = 0
                self.spectroconfig.m_Control_m_LaserWaveLength = 0.0
                self.spectroconfig.m_Control_m_StoreToRam = 0
                ret = avaspec.AVS_PrepareMeasure(self.spectro, self.spectroconfig)
                scans = -1
                avaspec.AVS_Measure(self.spectro, 0, scans)
                #return 1
            else:
                messagebox.showinfo(title='Error', message='It seems like no devices are connected')
                return 0
        
        
        
        self.adjust_wavelength_range()
        # Set basic integration time
        #self.adjust_integration_time(1)
        # Display message of successful connection
        messagebox.showinfo(title='Spectrometer', message='Spectrometer is connected.')
        # Update of the Experimental window
        if self.mainf:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Spectrometer')

        if exp_dependencie:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Spectrometer')

        return 1

    def get_wavelengths(self):
        if not self.spectro:
            return
        # Extract the spectral range of the device and put it as limits of the
        # wavelength graphic.
        if self.spectroType == 'ocean':
            wavelengths = self.spectro.wavelengths()
        elif self.spectroType == 'avantes':
            import avaspec
            pixels = avaspec.AVS_GetNumPixels(self.spectro)
            lamb = avaspec.AVS_GetLambda(self.spectro)
            wavelengths = np.array(lamb[0:pixels])
        return wavelengths    
        
    def adjust_wavelength_range(self):
        """
        This function is used to adjust the xaxis to be fitting the wavelength
        range of the spectrometer.

        """
        if not self.spectro:
            return
        # Extract the spectral range of the device and put it as limits of the
        # wavelength graphic.
        if self.spectroType == 'ocean':
            wavelengths = self.spectro.wavelengths()
            min_wave = min(wavelengths)
            max_wave = max(wavelengths)
        elif self.spectroType == 'avantes':
            import avaspec
            pixels = avaspec.AVS_GetNumPixels(self.spectro)
            lamb = avaspec.AVS_GetLambda(self.spectro)
            wavelengths = np.array(lamb[0:pixels])
            min_wave = min(wavelengths)
            max_wave = max(wavelengths)
            
        self.wv_graphic.axes.set_xlim([min_wave, max_wave])
        self.wv_graphic.Line.set_xdata(wavelengths)
        self.wv_graphic.Line.set_ydata(np.zeros(len(wavelengths)))
        # update function of the GraphicFrame class
        self.wv_graphic.update_graph()
    def overlay_spectrum(self,ref):
        """
        Plots an overlay reference spectrum
        """
        if not self.spectro:
            return
        ref = ref.get()
        Overlay = fQ.ezcsvload(ref)
        self.wv_graphic.LineRef, =  self.wv_graphic.axes.plot([], [])
        self.wv_graphic.LineRef.set_xdata(Overlay[0])
        self.wv_graphic.LineRef.set_ydata(Overlay[1])
        
    def adjust_integration_time(self, variable):
        """
        This function is to adjust the integration time of the device each
        device has a minimum integration time. It is directly linked to the
        update time of the Graphics.

        Parameters:
            variable : This is a tkinter IntVar that represents the time in
            microseconds.
        """
        if not self.spectro:
            return
        time = variable.get()
        if time == 0:
            time = 1
        if self.spectroType == 'ocean':
            self.spectro.integration_time_micros(time*1000)
        elif self.spectroType == 'avantes':
            import avaspec
            avaspec.AVS_StopMeasure(self.spectro)
            self.spectroconfig.m_IntegrationTime = time
            avaspec.AVS_PrepareMeasure(self.spectro, self.spectroconfig)
            avaspec.AVS_Measure(self.spectro, 0, -1)

    def set_trigger(self, mode):
        """
        Function that sets the trigger mode of the sectro (see manual for description)
        Mode=0 : Free running
        Mode=1 : Software trigger
        Mode=2 : External hardware level trigger
        Mode=3 : External synchronization trigger
        Mode=4 : External hardware edge trigger
        """
        if not self.spectro:
            return
        self.spectro.trigger_mode(mode)


    def extract_intensities(self, ave, fwhm, save_current=False):
        """
        Function that extract the intensities from the device and then
        manipulates the values to accomodate the options selected.

        Parameters:
            ave : This is a tkinter IntVar that dictates the number of
            averaging periods.
            fwhm : This is a tkinter DoubleVar that is updated when fft_graphic
            is computed. It is available in the spectrometer frame.
            save_current : Boolean value that allow to save the intensities
            with every option selected.
        """
        if not self.spectro:
            return
        if type(ave) is not int:
            try:
                ave = ave.get()
            except:
                ave = 1
        if ave == 0:
            ave = 1
        intensities = np.zeros((ave, len(self.get_wavelengths())))
        # Calculating the average and computing the mean value
        for i in range(ave):
            intensities[i, :] = self.get_intensities()
        intensities = np.mean(intensities, axis=0)
        # Substracting the dark spectrum from the intensities
# =============================================================================
#         if self.dark_spectrum:
#             intensities -= self.dark_array
# =============================================================================
        # Dividing efficiency from the intensities
        if self.eff_divider:
            intensities = np.divide(intensities, self.eff_array)
        # Calculating the fft if the graphic is available
        if self.fft_graphic:
            self.calculate_fft(intensities, fwhm)
        else:
            fwhm.set(0)
        # Updating maximum value of the graph
        if self.max_intensitie < max(intensities):
            self.max_intensitie = max(intensities)
            self.wv_graphic.axes.set_ylim([0, 1.05*self.max_intensitie])
        # Normalizing value in the graphic
        if self.normalizing:
            intensities = np.abs(intensities)**2
            intensities = np.divide(intensities, np.max(intensities))
            self.max_intensitie = 1
            self.wv_graphic.axes.set_ylim([0, 1.15*self.max_intensitie])
        # Save the current intensities with every option selected.
        if save_current:
            return intensities
        # Changing ydata and update the Graphic
        self.wv_graphic.Line.set_ydata(intensities)
        self.wv_graphic.update_graph()
        

    def get_intensities(self):
        """
        Added by Étienne: Simpler version of extract_intensities
        Function that extract and returns the intensities after removing the dark
        spectrum if needed.
        """
        if not self.spectro:
            return
        if self.spectroType == 'ocean':
            intensities = self.spectro.intensities()
        elif self.spectroType == 'avantes':
            import avaspec
# =============================================================================
#             dataready = False
#             import time
#             while not dataready:
#                 dataready = avaspec.AVS_PollScan(self.spectro)
#                 time.sleep(self.spectroconfig.m_IntegrationTime/1000)
# =============================================================================
            pixels = avaspec.AVS_GetNumPixels(self.spectro)
            intensities = np.zeros(pixels)
            for ii in range(40):
                timestamp, scopedata = avaspec.AVS_GetScopeData(self.spectro)
                intensities += np.array(scopedata[0:pixels])/40
        if self.dark_spectrum is True:
            intensities = intensities - self.dark_array
            
        return intensities

    def enable_darkspectrum(self, variable, dark_button):
        """
        Function that extract the dark_spectrum from the device and then
        saves it in a array to be substracted when manipulating the data.

        Parameters:
            variable : Tkinter StringVar that is dependant of the checkbox
            linked to the dark_spectrum.
            dark_button : Tkinter Button his state is modified during the
            function.
        """
        # verifing that the is a spectrometer connected
        if not self.spectro:
            messagebox.showinfo(title='Error', message='No spectrometer connected')
            variable.set('disable')
        # Getting the state of the Chekbox
        state = variable.get()
        if state == 'enable':
            # Asking if there is something in front of the spectro
            answ = messagebox.askyesno(title='INFO',
                                       message='Is there any incident beam'+
                                               'towards the spectrometer?')
            # If there is nothing : calculates the darkspectrum else it ask to
            # do it the repress the button
            if not answ:
                self.measure_darkspectrum()
                messagebox.showinfo(title='Dark Spectrum',
                                    message='Dark spectrum completed.')
                dark_button['state'] = 'normal'
                self.dark_spectrum = True
            else:
                messagebox.showinfo(title='Dark Spectrum',
                                    message='Block the beam and try again')
                variable.set('disable')
                self.dark_spectrum = False
        # if the option is not disabled reset everything
        elif state == 'disable':
            self.dark_spectrum = False
            self.dark_array = None

    def measure_darkspectrum(self):
        """
        Function that extract a simple intensity with the integration time
        asked and save it in the dark_array attribute
        """
        if not self.spectro:
            return
        if self.spectroType == 'ocean':
            intensities = self.spectro.intensities()
        elif self.spectroType == 'avantes':
            import avaspec
            timestamp, scopedata = avaspec.AVS_GetScopeData(self.spectro)
            pixels = avaspec.AVS_GetNumPixels(self.spectro)
            intensities = np.array(scopedata[0:pixels])
        self.dark_array = intensities
        
        
    def measure_average_darkspectrum(self,numDark = 1):
        """
        Function that extract a simple intensity with the integration time
        asked and save it in the dark_array attribute
        """
        tmp = self.get_intensities()
        
        for ii in range(numDark-1):
            tmp += self.get_intensities()
        self.dark_array = tmp / numDark
        

    def enable_eff(self, variable):
        """
        Function that extract the eff_divider from a file and then
        saves it in a array to be divided when manipulating the data.

        Parameters:
            variable : Tkinter StringVar that is dependant of the checkbox
            linked to the eff_divider.
        """

        if not self.spectro:
            variable.set('disable')
            return
        # Gets the model of the spectrometer to find the file
        name = self.spectro.model
        state = variable.get()
        # Load the data with a numpy array found in the folder spectro divider
        # dependant of the name of the device
        if state == 'disable':
            self.eff_divider = False
        else:
            if not self.eff_array:
                try:
                    self.eff_array = np.load('spectro_divider/' + name + '.npy')
                except:
                    self.eff_array = None

            if self.eff_array:
                self.eff_divider = True
            else:
                variable.set('disable')
                messagebox.showinfo(title='Error', message='There is no file'
                                    + ' related to this device')

    def calculate_fft(self, intensities, fwhm_v):
        """
        Function that computes the fft of the signal using the femtoQ package.
        This is then plotted within the second graphic (fft_graphic).
        Parameters:
            intensities : Intensity vector computed and modified in the other
            section extract_intensities.
            fwhm_v : This is tkinter DoubleVar that will be updated. It allows
            the tkinter Entry to be updated in real time.
        """
        # Manipulation to prepare for the fft
        wavelengths = self.get_wavelengths()
        frequencies = np.divide(sc.c, wavelengths*1e-9)
        frequencies = np.flip(frequencies)
        intensities = np.flip(intensities)
        resolution = 0.1e-15
        max_freq = 1/(2*resolution)
        max_f = np.max(frequencies)
        min_f = np.min(frequencies)
        pad_freq = np.append(frequencies, np.linspace(max_f, max_freq,
                                                      len(frequencies)))
        lin_freq = np.linspace(-np.max(pad_freq), np.max(pad_freq),
                               2*len(pad_freq)+1)
        intensities = np.pad(intensities, (0, len(frequencies)), mode='constant',
		 	                 constant_values=(0, 0))
        intensities = np.interp(lin_freq, pad_freq, intensities/pad_freq**2,left= 0,right = 0)
        intensities = fQ.ezsmooth(intensities,window = 'hanning')
        intensities[intensities < np.max(intensities)/100] = 0
        # Calculate the ezifft of the signal.
        sig_time, sig = fQ.ezifft(lin_freq, np.sqrt(intensities), amplitudeSpectrumRecentering = True)
        sig = np.absolute(sig)**2
        sig = sig/np.max(sig)
        fwhm = fQ.ezfindwidth(sig_time, sig)
        sig_time = sig_time/1e-15
        fwhm = fwhm/1e-15
        # Update the full with half max
        if not(np.isnan(fwhm) or np.isinf(fwhm)):
            fwhm_v.set(np.round(fwhm, decimals=2))
        else:
            fwhm = 10
            fwhm_v.set(0)
        # Sets the graphic and update the graph
        self.fft_graphic.Line.set_xdata(sig_time)
        self.fft_graphic.Line.set_ydata(sig)
        if self.fft_autoupdate:
            self.fft_graphic.axes.set_xlim([-10*fwhm, 10*fwhm])
            self.fft_graphic.axes.set_ylim([1.15*np.min(sig), 1.15*np.max(sig)])

        self.fft_graphic.update_graph()

    def switch_graphics(self, variable, frame):
        """
        Change the graphic disposition to allow to pass from one to two
        graphics. Thus it allows you to go from wavelengths to wavelengths +
        fft.
        Parameters:
            variable : This is linked to the FFT+Wave checkbox it is updated
            when you check it.
            frame : Tkinter frame that contains the frame.
        """
        state = variable.get()
        # Destroy all the element unwanted and create the double graph
        if state == 'enable':
            self.wv_graphic.destroy_graph()
            self.dual = Graphic.SubGraphFrame(parent=frame,
                                              subplots={'WV':['Wavelength [nm]','Intensities [counts]'],
                                                        'FFT':['Time [fs]','Intensities [counts]']},
                                             figsize=[9,6])
            self.fft_graphic = self.dual.graph[1]
            self.wv_graphic = self.dual.graph[0]
            self.adjust_wavelength_range()
        # Destroy all the element unwanted from the dual graph and recreate the
        # wv_graphic
        elif state == 'disable':
            if not self.dual:
                return
            self.dual.destroy_graph()
            self.dual = None
            self.wv_graphic = Graphic.GraphicFrame(frame,
                                                   axis_name=['Wavelength [nm]',
                                                              'Intensity [counts]'],
                                                   figsize=[9, 6])
            self.fft_graphic = None
            self.fft_centered = False

    def enable_logscale(self, variable):
        """
        Change the graphic yaxis to be logarithmic.

        Parameters:
            variable : This is linked to the Logarithmic scale checkbox it is updated
            when you check it.
        """
        state = variable.get()
        if state == 'enable':
            self.wv_graphic.axes.set_yscale('symlog')
        elif state == 'disable':
            self.wv_graphic.axes.set_yscale('linear')

    def normalized(self, variable):
        """
        Change the graphic yaxis to be normalized. It updates the Boolean
        value.

        Parameters:
            variable : This is linked to the Logarithmic scale checkbox it is updated
            when you check it.
        """
        state = variable.get()
        if state == 'enable':
            self.normalizing = True
        elif state == 'disable':
            self.normalizing = False

    def save_data(self, ave):
        """
        Save the data with the number of averaging periods. This allows to save
        the data with all the manipulation asked.

        Parameters:
            ave : Number of averaging periods.
        """
        Iarray = self.get_intensities()
        Warray = self.spectro.wavelengths()
        array = np.array([Warray, Iarray])
        from datetime import datetime
        now = datetime.now()
        dt = now.strftime('%d_%m_%Y__%H_%M_%S')
        try:
            np.save('measurements/'+'Spectre_' +dt, array)
        except:
            messagebox.showinfo(title='ERROR', message='Create a folder'+
                                ' named measurements inside this folder')

    def auto_update_fft(self, variable):
        """
        This function update the boolean fft_autoupdate. It is linked to the
        variable.

        Parameters:
            variable : This is a StringVar linked to the checkbox. It is
            updated when the checkbox is locked or not.
        """
        state = variable.get()
        if state == 'enable':
            self.fft_autoupdate = True
        elif state == 'disable':
            self.fft_autoupdate = False

class PopUp(tk.Tk):
    def __init__(self, values=None, lib_=None, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        listbox_val = self.find_id(values)
        self.value = {}
        self.lib_ = lib_
        # Mini Image and Mainframe title
        directory = Path.cwd()
        image = tk.PhotoImage(file=directory / 'FMQ3.gif')
        tk.Tk.wm_title(self, "Femtoq Lab")
        tk.Tk.wm_iconphoto(self, '-default', image)
        label = tk.Label(self, text='Choose the desired device:')
        label.grid(row=0, column=0, columnspan=2, sticky='nw')
        listbox = tk.Listbox(self, height=4, listvariable=listbox_val)
        listbox.grid(row=1, column=0, sticky='nsew')
        enter = tk.Button(self, text='Enter', command=lambda: self.destruct(lstvariable=listbox), width=6)
        enter.grid(row=1, column=1, sticky='nsew')

    def destruct(self, lstvariable):
        index = lstvariable.curselection()[0]
        dev_id = lstvariable.get(index)
        self.value = self.value[dev_id]

    def find_id(self, values):
        spec_id = ()
        for value in values:
            spec_id = spec_id + (self.lib_.Spectrometer(value).serial_number, )
            self.value[spec_id] = value
        return spec_id
