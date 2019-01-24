import tkinter as tk
from pathlib import Path
import seabreeze
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb
from tkinter import messagebox
import Graphic


class Spectro:
    def __init__(self, graphic=None, parent=None):
        self.spectro = None
        self.wv_graphic = graphic
        self.fft_graphic = None
        self.dual = None
        self.parent = parent
        self.max_intensitie = 0
        self.dark_spectrum = False

    def connect(self, exp_dependencie=False):

        def device_popup(items=None):
            device = PopUp(values=items).mainloop()
            device = device.value
            return device

        devices = sb.list_devices()
        if type(devices) == list and devices:
            if len(devices) > 1:
                device = device_popup(devices)
            else:
                device = devices[0]
        else:
            return

        self.spectro = sb.Spectrometer(device)
        self.adjust_wavelength_range()
        self.spectro.integration_time_micros(1000)

        if exp_dependencie:
            experiments = self.parent.Frame[4].experiment_dict
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
        self.wv_graphic.update_graph()

    def adjust_integration_time(self, variable):
        if not self.spectro:
            return
        time = variable.get()
        self.spectro.integration_time_micros(time)

    # Message to PATRICK
    # ICI doit être modifié pour accomoder les différents options ie les manipualtions/fonction peuvent être écrit
    # ailleur mais il va être nécessaire de changer cette fonction explicitement pour accomoder les deux possibilités
    # de graphic. Ce que je propose est de créer différent "style" de mesure qui collecterais les données différements
    #  selon les options à toi de voir ce qui te plait
    def extract_intensities(self):
        if not self.spectro:
            return
        intensities = self.spectro.intensities()
        if self.max_intensitie < max(intensities):
            self.max_intensitie = max(intensities)
            self.wv_graphic.Line.set_ylim([0, self.max_intensitie])
        self.wv_graphic.Line.set_ydata(intensities)
        self.wv_graphic.update_graph()

    def enable_darkspectrum(self, variable):
        if not self.spectro:
            messagebox.showinfo(title='Error', message='No spectrometer connected')
            variable.set('disable')
        state = variable.get()
        if state == 'enable':
            print('do stuff')

    def switch_graphics(self, variable, frame):
        #if not self.spectro:
        #    messagebox.showinfo(title='Error', message='No spectrometer connected')
        #    variable.set('disable')
        state = variable.get()
        if state == 'enable':
            self.wv_graphic.destroy_graph()
            self.dual = Graphic.SubGraphFrame(parent=frame, subplots={'FFT': ['A', 'B'], 'WV': ['C', 'D']})
            self.fft_graphic = self.dual.graph[0]
            self.wv_graphic = self.dual.graph[1]
        elif state == 'disable':
            if not self.dual:
                return
            self.dual.destroy_graph()
            self.dual = None
            self.wv_graphic = Graphic.GraphicFrame(frame, axis_name=['Wavelength', 'Intensity'], figsize=[9, 6])
            self.fft_graphic = None


class PopUp(tk.Tk):
    def __init__(self, values=None, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        listbox_val = self.find_id(values)
        self.value = {}
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
            spec_id = spec_id + (sb.Spectrometer(value).serial_number, )
            self.value[spec_id] = value
        return spec_id
