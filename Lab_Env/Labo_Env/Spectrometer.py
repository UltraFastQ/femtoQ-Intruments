import tkinter as tk
from pathlib import Path
import seabreeze
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb


class Spectro:
    def __init__(self, graphic=None, parent=None):
        self.spectro = None
        self.graphic = graphic
        self.parent = parent
        self.max_intensitie = 0

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
        self.graphic.axes.set_xlim([min_wave, max_wave])
        self.graphic.Line.set_xdata(wavelengths)
        self.graphic.update_graph()

    def extract_intensities(self):
        if not self.spectro:
            return
        intensities = self.spectro.intensities()
        if self.max_intensitie < max(intensities):
            self.max_intensitie = max(intensities)
            self.graphic.Line.set_ylim([0, self.max_intensitie])
        self.graphic.Line.set_ydata(intensities)
        self.graphic.update_graph()


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
