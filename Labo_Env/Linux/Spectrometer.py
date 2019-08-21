import tkinter as tk
import numpy as np
from femtoQ import tools as fQ
import scipy.constants as sc
from pathlib import Path
from tkinter import messagebox
import Graphic


class Spectro:
    def __init__(self, graphic=None, mainf=None):
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

        def device_popup(items=None):
            device = PopUp(values=items).mainloop()
            device = device.value
            return device

        import seabreeze
        seabreeze.use('pyseabreeze')
        import seabreeze.spectrometers as sb
        devices = sb.list_devices()
        if type(devices) == list and devices:
            if len(devices) > 1:
                device = device_popup(value=devices, lib_=sb)
            else:
                device = devices[0]
        else:
            messagebox.showinfo(title='Error', message='It seems like no devices are connected')
            return

        self.spectro = sb.Spectrometer(device)
        self.adjust_wavelength_range()
        self.spectro.integration_time_micros(1000)
        if exp_dependencie:
            experiments = self.mainf.Frame[4].experiment_dict
            for experiment in experiments:
                experiments[experiment].update_options('Spectrometer')

    def adjust_wavelength_range(self):
        if not self.spectro:
            return
        wavelengths = self.spectro.wavelengths()
        min_wave = min(wavelengths)
        max_wave = max(wavelengths)
        self.wv_graphic.axes.set_xlim([min_wave, max_wave])
        self.wv_graphic.Line.set_xdata(wavelengths)
        self.wv_graphic.Line.set_ydata(np.zeros(len(wavelengths)))
        self.wv_graphic.update_graph()

    def adjust_integration_time(self, variable):
        if not self.spectro:
            return
        time = variable.get()
        self.spectro.integration_time_micros(time*1000)

    # Message to PATRICK
    # ICI doit être modifié pour accomoder les différents options ie les manipualtions/fonction peuvent être écrit
    # ailleur mais il va être nécessaire de changer cette fonction explicitement pour accomoder les deux possibilités
    # de graphic. Ce que je propose est de créer différent "style" de mesure qui collecterais les données différements
    #  selon les options à toi de voir ce qui te plait
    def extract_intensities(self, ave, fwhm, save_current=False):
        if not self.spectro:
            return
        if type(ave) is not int:
            try:
                ave = ave.get()
            except:
                ave = 1
        if ave == 0:
            ave = 1
        intensities = np.zeros((ave, len(self.spectro.wavelengths())))

        for i in range(ave):
            intensities[i, :] = self.spectro.intensities()
        intensities = np.mean(intensities, axis=0)
        if self.dark_spectrum:
            intensities -= self.dark_array

        if self.eff_divider:
            intensities = np.divide(intensities, self.eff_array)

        if self.fft_graphic:
            self.calculate_fft(intensities, fwhm)
        else:
            fwhm.set(0)

        if self.max_intensitie < max(intensities):
            self.max_intensitie = max(intensities)
            self.wv_graphic.axes.set_ylim([0, 1.05*self.max_intensitie])

        if self.normalizing:
            intensities = np.abs(intensities)**2
            intensities = np.divide(intensities, np.max(intensities))
            self.max_intensitie = 1
            self.wv_graphic.axes.set_ylim([0, 1.15*self.max_intensitie])

        if save_current:
            return intensities

        self.wv_graphic.Line.set_ydata(intensities)
        self.wv_graphic.update_graph()

    def enable_darkspectrum(self, variable, dark_button):
        if not self.spectro:
            messagebox.showinfo(title='Error', message='No spectrometer connected')
            variable.set('disable')
        state = variable.get()
        if state == 'enable':
            self.dark_spectrum = True
            answ = messagebox.askyesno(title='INFO',
                                       message='Is there any incident beam'+
                                               'towards the spectrometer?')
            if not answ:
                self.measure_darkspectrum()
                messagebox.showinfo(title='Dark Spectrum',
                                    message='Dark spectrum completed.')
                dark_button['state'] = 'normal'
            else:
                messagebox.showinfo(title='Dark Spectrum',
                                    message='Block the beam and try again')
                variable.set('disable')
                self.dark_spectrum = False
        elif state == 'disable':
            self.dark_spectrum = False
            self.dark_array = None

    def measure_darkspectrum(self):
        self.dark_array = self.spectro.intensities()

    def enable_eff(self, variable):

        if not self.spectro:
            variable.set('disable')
            return

        name = self.spectro.model
        state = variable.get()

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
        wavelengths = self.spectro.wavelengths()
        frequencies = np.divide(sc.c, wavelengths*1e-9)
        frequencies = np.flip(frequencies)
        intensities = np.flip(intensities)
        resolution = 0.1e-15
        max_freq = 1/(2*resolution)
        max_f = np.max(frequencies)
        min_f = np.min(frequencies)
        pad_freq = np.append(frequencies, np.linspace(max_f, max_freq,
                                                      len(frequencies)))
        lin_freq = np.linspace(np.min(pad_freq), np.max(pad_freq),
                               len(pad_freq))
        intensities = np.pad(intensities, (0, len(frequencies)), mode='constant',
		 	                 constant_values=(0, 0))
        intensities = np.interp(lin_freq, pad_freq, intensities)
        intensities[intensities < 0] = 0
        sig_time, sig = fQ.ezifft(lin_freq, np.sqrt(intensities))
        sig = np.fft.fftshift(sig)
        sig = np.absolute(sig)**2
        sig = sig/np.max(sig)
        fwhm = fQ.ezfindwidth(sig_time, sig)
        sig_time = sig_time/1e-15
        fwhm = fwhm/1e-15

        if not(np.isnan(fwhm) or np.isinf(fwhm)):
            fwhm_v.set(np.round(fwhm, decimals=2))
        else:
            fwhm = 10
            fwhm_v.set(0)

        self.fft_graphic.Line.set_xdata(sig_time)
        self.fft_graphic.Line.set_ydata(sig)
        if self.fft_autoupdate:
            self.fft_graphic.axes.set_xlim([-10*fwhm, 10*fwhm])
            self.fft_graphic.axes.set_ylim([1.15*np.min(sig), 1.15*np.max(sig)])

        self.fft_graphic.update_graph()

    def switch_graphics(self, variable, frame):
        state = variable.get()
        if state == 'enable':
            self.wv_graphic.destroy_graph()
            self.dual = Graphic.SubGraphFrame(parent=frame,
                                              subplots={'WV':['Wavelength [nm]','Intensities [counts]'],
                                                        'FFT':['Time [fs]','Intensities [counts]']},
                                             figsize=[9,6])
            self.fft_graphic = self.dual.graph[1]
            self.wv_graphic = self.dual.graph[0]
            self.adjust_wavelength_range()
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
        state = variable.get()
        if state == 'enable':
            self.wv_graphic.axes.set_yscale('symlog')
        elif state == 'disable':
            self.wv_graphic.axes.set_yscale('linear')

    def normalized(self, variable):
        state = variable.get()
        if state == 'enable':
            self.normalizing = True
        elif state == 'disable':
            self.normalizing = False

    def save_data(self, ave):
        Iarray = self.extract_intensities(ave, save_current=True)
        Warray = self.spectro.wavelengths()
        array = np.array([Warray, Iarray])
        from datetime import datetime
        now = datetime.now()
        dt = now.strftime('%d_%m_%Y__%H_%M_%S')
        try:
            np.save('measurements/'+'Spectre_' +dt, array)
        except:
            messagebox.showinfo(title='ERROR', message='Create a folder'+
                                ' named measurement inside this folder')

    def auto_update_fft(self, variable):
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
