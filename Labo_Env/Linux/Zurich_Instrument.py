from tkinter import messagebox
import Graphic
import re
import numpy as np
import time


class Zurich:
    def __init__(self, parent):
        self.parent = parent
        self.info = None
        self.default = None
        self.num = 1
        self.paths = {}
        self.subscribed = {}
        self.node_branch = None
        self.state = {}
        self.in_use = False
        self.subscribing = False
        poll_length = 0.1 # Time of the aquisition in second
        poll_timeout = 500 # [ms]
        poll_flags = 0
        poll_return_dict = True # This is how the data is returned
        self.poll_set = [poll_length, poll_timeout, poll_flags, poll_return_dict]

    def connect_device(self, devicename, required_options=None, required_err_msg='', exp_dependencie=False):
        import zhinst.utils as utils
        import zhinst.ziPython as ziPython

        # This function finds and connect the zurich device with serial number : devicename
        api_level = 6
        dev_type = 'UHFLI'
        # Create an instance of the ziDiscovery class.
        d = ziPython.ziDiscovery()
        # Determine the device identifier from it's ID.
        device_id = d.find(devicename).lower()
        # Get the device's connectivity properties.
        props = d.get(device_id)
        if not props['discoverable']:
            messagebox.showinfo(message= "The specified device `{}` is not discoverable  ".format(devicename) +
                           "from the API. Please ensure the device is powered-on and visible using the LabOne User" +
                           "Interface or ziControl.", title='Information')
        else:
            if not re.search(dev_type, props['devicetype']):
                messagebox.showinfo(message="Required device type not satisfied. Device type `{}` does not match the" +
                                           "required device type:`{}`. {}".format(props['devicetype'], dev_type,
                                                                                  required_err_msg))

            if required_options:
                assert isinstance(required_options, list), "The keyword argument must be a list of string each entry" \
                                                           "specifying a device option."

                def regex_option_diff(required_options, device_options):
                    """Return the options in required_options (as regex) that are not found in the
                    device_options list.

                    """
                    missing_options = []
                    for option in required_options:
                        if not re.search(option, '/'.join(device_options)):
                            missing_options += required_options
                    return missing_options

                if props['devicetype'] == 'UHFAWG':
                    # Note(16.12): This maintains backwards compatibility of this function.
                    installed_options = props['options'] + ['AWG']
                else:
                    installed_options = props['options']
                missing_options = regex_option_diff(required_options, installed_options)
                if missing_options:
                    raise Exception("Required option set not satisfied. The specified device `{}` has the `{}` options "
                                    "installed but is missing the required options `{}`. {}".
                                    format(device_id, props['options'], missing_options, required_err_msg))
            # The maximum API level supported by the device class, e.g., MF.
            apilevel_device = props['apilevel']

            # Ensure that we connect on an compatible API Level (from where create_api_session() was called).
            apilevel = min(apilevel_device, api_level)
            # Creating a Daq server for the device with the parameters found
            daq = ziPython.ziDAQServer(props['serveraddress'], props['serverport'], apilevel)
            messagebox.showinfo(message='Zurich Instrument device {} is connected'.format(device_id),
                                title='Information')
            self.info = {'daq': daq, 'device': device_id, 'prop': props}
            self.default = utils.default_output_mixer_channel(self.info['prop'])
            self.node_branch = daq.listNodes('/%s/' % device_id, 0)
            reset_settings = [
                ['/%s/demods/*/enable' % device_id, 0],
                ['/%s/demods/*/trigger' % device_id, 0],
                ['/%s/sigout/*/enables/*' % device_id, 0],
                ['/%s/scopes/*/enable' % device_id, 0]
            ]

            daq.set(reset_settings)
            daq.sync()

            if exp_dependencie:
                experiments = self.parent.Frame[4].experiment_dict
                for experiment in experiments:
                    experiments[experiment].update_options('Zurich')

    # This function has a lot to work on it should work properly but it is really only a patched up function
    def update_settings(self, value=None, type_=None, setting_line=None):

        if not self.info:
            messagebox.showinfo(title='Error', message='There is no device connected yet, please connect the device ' +
                                'before changing any device settings.')
            return

        if 'oscs' in setting_line:
            state = self.info['daq'].getInt('/{}{}'.format(self.info['device'], setting_line))
            if state == 1:
                messagebox.showinfo(title='Error', message='This option is unavailable until the external reference' +
                                    'is unconnected.')
                return

        tension_unit = {'V': 1, 'mV': .001, 'uV': 10 ^ (-6)}
        sample_unit = {'n': 10 ^ (-9), 'u': 10 ^ (-6), 'm': 10 ^ (-3), 'k': 10 ^ 3, 'M': 10 ^ 6}
        factor = 1
        setting = []
        if not value:
            setting = ['/{}{}'.format(self.info['device'], setting_line), 1]
        elif value:
            if type(value) == list:
                if type_ == 'tension':
                    if value[1].get() not in tension_unit:
                        value[1].set('V')
                    factor = tension_unit[value[1].get()]
                    value = value[0].get()
                elif type_ == 'sample':
                    value = value[0].get()
                    if value[1].get() not in sample_unit:
                        value[1].set('M')
                    factor = sample_unit[value[1].get()]
                elif type_ == 'double_bw2tc':
                    import zhinst.utils as utils
                    value = utils.bw2tc(bandwidth=value[0].get(), order=value[1].get())
                value = value*factor
            else:
                if type_ == 'double' or type_ == 'int':
                    value = value.get()
                elif type_ == 'double_str2db':
                    found = False
                    str_tot_value = value.get()
                    for unit in sample_unit:
                        if unit in str_tot_value:
                            factor = sample_unit[unit]
                            str_value = str_tot_value.split(unit)
                            value_float = round(float(str_value[0]), len(str_value[0])) * factor
                            found = True
                        elif found:
                            pass

                    if not found:
                        str_value = str_tot_value
                        try:
                            value_float = round(float(str_value), len(str_value))
                        except ValueError:
                            value.set('1.717k')
                            value_float = 1717
                    value = value_float
                elif type_ == 'T_F':
                    if 'enable' in setting_line:
                        self.default_demod(setting_line, value)
                    if value.get() == 'Enabled':
                        value = True
                    else:
                        value = False

            if type(setting_line) == str:
                if type_ == 'combobox':
                    setting = ['/{}{}'.format(self.info['device'], setting_line), value.current()]
                elif type_ == 'combobox_external':
                    selected = value.current()
                    state = self.info['daq'].getInt('/{}{}/enable'.format(self.info['device'], setting_line))
                    mode = self.info['daq'].getInt('/{}{}/automode'.format(self.info['device'], setting_line))
                    if selected == 0:
                        setting = ['/{}{}/enable'.format(self.info['device'], setting_line), 0]
                    elif selected == 1:
                        if state == 1:
                            if mode == 2 or mode == 3:
                                setting = ['/{}{}/automode'.format(self.info['device'], setting_line), 4]
                            else:
                                return
                        elif state == 0:
                            setting = ['/{}{}/enable'.format(self.info['device'], setting_line), 1]
                    elif selected == 2:
                        if state == 1:
                            setting = ['/{}{}/automode'.format(self.info['device'], setting_line), 2]
                        elif state == 0:
                            setting = [['/{}{}/enable'.format(self.info['device'], setting_line), 1],
                                       ['/{}{}/automode'.format(self.info['device'], setting_line), 2]]
                    elif selected == 3:
                        if state == 1:
                            setting = ['/{}{}/automode'.format(self.info['device'], setting_line), 3]
                        elif state == 0:
                            setting = [['/{}{}/enable'.format(self.info['device'], setting_line), 1],
                                       ['/{}{}/automode'.format(self.info['device'], setting_line), 3]]
                else:
                    # Value has to be defined
                    setting = ['/{}{}'.format(self.info['device'], setting_line), value]
            else:
                if setting_line[0] == 'output':
                    setting = ['/{}{}'.format(self.info['device'], setting_line[1]), value]
                    setting.append(['/{}{}/{}'.format(self.info['device'], setting_line[2][0], self.default), value])
                    # I have to find a way to get the input amplitude or output... I am not sure just yet
                    setting.append(['/{}{}/{}'.format(self.info['device'], setting_line[2][1], self.default), 2])

        setting = [setting]
        # This sets the item in the Zurich server
        self.info['daq'].set(setting)
        self.info['daq'].sync()

    def default_demod(self, path, variable):
        value = None
        if variable.get() == 'Enabled':
            self.state['Plotter'] = True
            value = 1
        elif variable.get() == 'Disabled':
            self.state['Plotter'] = False
            value = 0

        # This set the default demodulator parameter for initialization purpuses
        index = path.split('/demods/')
        index = index[1].split('/enable')[0]
        import zhinst.utils as utils
        basics = [['/%s/demods/%s/enable' % (self.info['device'], index), value],
                  ['/%s/demods/%s/phaseshift' % (self.info['device'], index), 0],
                  ['/%s/demods/%s/rate' % (self.info['device'], index), int(1.717e3)],
                  ['/%s/demods/%s/adcselect' % (self.info['device'], index), 0],
                  ['/%s/demods/%s/order' % (self.info['device'], index), 1],
                  ['/%s/demods/%s/timeconstant' % (self.info['device'], index), utils.bw2tc(100, 1)],
                  ['/%s/demods/%s/oscselect' % (self.info['device'], index), 0],
                  ['/%s/demods/%d/harmonic' % (self.info['device'], 0), 1]]
        self.info['daq'].set(basics)
        self.info['daq'].sync()
        self.paths['/{}/demods/{}/sample'.format(self.info['device'], index)] = True

    def add_subscribed(self, path, child_class, graph_class):
        # path is the path associated with the object.
        # object : The class associated with the path to mesure
        if not self.info:
            return
        if not path:
            return
        while self.in_use:
            time.sleep(0.1)
        for element in self.paths:
            if self.paths[element]:
                if path in element:
                    self.subscribing = True
                    self.info['daq'].subscribe(element)
                    self.subscribed[element] = [child_class, graph_class]
        self.subscribing = False

    def unsubscribed_path(self, path):
        # Same input as the add_subscribed
        if not self.info:
            return
        for element in self.paths:
            if self.paths[element]:
                if path in element:
                    self.subscribing = True
                    self.info['daq'].unsubscribe(element)
                    del self.subscribed[element]
        self.subscribing = False

    def measure_guide(self):
        t = 1000
        if not self.info:
            self.parent.after(t, self.measure_guide)
            return
        if not self.state:
            self.parent.after(t, self.measure_guide)
            return
        if not self.state:
            return
        i = 0
        for item in self.state:
            if not self.state[item] and i == 3:
                self.parent.after(t, self.measure_guide)
                return
            elif not self.state[item]:
                i += 1
            elif self.state[item]:
                t = 100
        while self.subscribing:
            time.sleep(0.1)

        if self.in_use:
            return
        subscribed = self.subscribed
        data_set = self.info['daq'].poll(self.poll_set[0], self.poll_set[1], self.poll_set[2], self.poll_set[3])
        for path in subscribed:
            self.in_use = True
            subscribed[path][0].extract_data(data=data_set, path=path)
            subscribed[path][1].update_graph()
        self.in_use = False
        self.parent.after(t, self.measure_guide)


class Scope:

    def __init__(self, zurich=None, line=None, axes=None, fig=None):
        # format will be #1 : device id when connected
        #                #2 : scope taken to read the data
        # line : matplotlib Line issued when you plot axis
        self.path = '/{}/scopes/{}/wave'
        self.line = line
        self.axes = axes
        self.fig = fig
        self.zurich = zurich

    def enable_scope(self, scope, variable):
        if not self.zurich.info:
            messagebox.showinfo(title='Error', message='There is no device connected')
            variable.set('disable')
            return
        value = None
        device = self.zurich.info['device']
        if variable.get() == 'enable':
            self.zurich.state['Scope'] = True
            value = 1
        elif variable.get() == 'disable':
            self.zurich.state['Scope'] = False
            self.zurich.paths[self.path.format(device, scope)] = False
            value = 0
        setting = [['/{}/scopes/{}/enable'.format(device, scope), value],
                   ['/{}/scopes/{}/length'.format(device, scope), int(1e4)],
                   ['/{}/scopes/{}/channel'.format(device, scope), 1]]
        # This assigned path is now allowed to be plotted. The Zurich instrument can now subscribe a designed path

        self.zurich.paths[self.path.format(device, scope)] = True
        self.zurich.info['daq'].set(setting)
        self.zurich.info['daq'].sync()

    def enable_trigger(self, scope, trigger, variable_):
        if not self.zurich.info:
            messagebox.showinfo(title='Error', message='There is no device connected')
            variable_.set('disable')
            return
        trigger = trigger.get()
        device = self.zurich.info['device']
        Trig_Settings = [['/{}/scopes/{}/trigenable'.format(device, scope), 1],
                         ['/{}/scopes/{}/trigchannel'.format(device, scope), trigger]]
        # Trigger on rising edge ?
        Trig_Settings.append(['/{}/scopes/{}/trigrising'.format(device, scope), 1])
        # Trigger on falling edge ?
        Trig_Settings.append(['/{}/scopes/{}/trigfalling' .format(device, scope), 0])
        # Trigger on threshold level
        Trig_Settings.append(['/{}/scopes/{}/triglevel' .format(device, scope), 0.00])
        # Set hysteresis triggering threshold to avoid triggering on noise
        # 'trighysteresis/mode' :
        #  0 - absolute, use an absolute value ('scopes/{}/trighysteresis/absolute')
        #  1 - relative, use a relative value ('scopes/{}/trighysteresis/relative') of the trigchannel's input range
        #  (0.1=10%).
        Trig_Settings.append(['/{}/scopes/{}/trighysteresis/mode' .format(device, scope), 1])
        Trig_Settings.append(['/{}/scopes/{}/trighysteresis/relative' .format(device, scope), 0.1])
        # Set the trigger hold-off mode of the scope. After recording a trigger event, this specifies when the scope should
        # become re-armed and ready to trigger, 'trigholdoffmode':
        #  {} - specify a hold-off time between triggers in seconds ('scopes/{}/trigholdoff'),
        #  1 - specify a number of trigger events before re-arming the scope ready to trigger ('scopes/{}/trigholdcount').
        Trig_Settings.append(['/{}/scopes/{}/trigholdoffmode' .format(device, scope), 0])
        Trig_Settings.append(['/{}/scopes/{}/trigholdoff' .format(device, scope), 0.025])
        # Set trigdelay to {}.: Start recording from when the trigger is activated.
        Trig_Settings.append(['/{}/scopes/{}/trigdelay' .format(device, scope), 0.0])
        # Disable trigger gating.
        Trig_Settings.append(['/{}/scopes/{}/triggate/enable' .format(device, scope), 0])
        # Disable segmented data recording.
        Trig_Settings.append(['/{}/scopes/{}/segments/enable' .format(device, scope), 0])
        # External Trigger
        # I need to learn more about the external ref format
        Trig_Settings.append(['/{}/extrefs/{}/enable' .format(device, 0), 1])

        self.zurich.info['daq'].set(Trig_Settings)
        self.zurich.info['daq'].sync()

    def extract_data(self, data, path):
        if not(self.zurich.paths[path]):
            return
        try:
            scope_data = data[path]
        except KeyError:
            print('we avoided trouble')
            return
        # This takes the wave data stored in the daq and push them into the  it in the assigned figure
        scope_data = data[path]
        for index, shot in enumerate(scope_data):
            Nb_Smple = shot['totalsamples']
            time = np.linspace(0, shot['dt'] * Nb_Smple, Nb_Smple)
            # Scope Input channel is 0 but we can add up to 3 if im correct
            wave = shot['channeloffset'][0] + shot['channelscaling'][0] * shot['wave'][:, 0]
            self.axes.set_ylim([min(wave) - abs(min(wave) * 15 / 100), max(wave) + max(wave) * 15 / 100])
            self.axes.set_xlim(
                [min(1e6 * time) - abs(min(1e6 * time) * 15 / 100), max(1e6 * time) + max(1e6 * time) * 15 / 100])
            if (not shot['flags']) and (len(wave) == Nb_Smple):
                self.line.set_xdata(1e6 * time)
                self.line.set_ydata(wave)


class Plotter:

    def __init__(self, zurich=None, line=None, axes=None, fig=None):

        # format will be #1 : device id when connected
        #                #2 : scope taken to read the data
        # line : matplotlib Line issued when you plot axis
        self.path = ''
        self.line = line
        self.axes = axes
        self.fig = fig
        self.window_time = 100
        self.axes.set_xlim([0, 100])
        self.zurich = zurich

    def change_axislim(self, variable):
        t = variable.get()
        t = t.split('s')[0]
        units = {'n': 1e-09, 'u': 1e-06, 'm': 1e-03, 'k': 1e3}
        factor = 1
        found = False
        time_float = 100
        for unit in units:
            str_value = t.split(unit)
            if len(str_value) == 1:
                pass
            elif found:
                pass
            elif len(str_value[1]) == 0:
                factor = units[unit]
                time_float = round(float(str_value[0]), len(str_value[0])) * factor
                found = True
        if not found:
            try:
                time_float = round(float(t), len(t))
            except ValueError:
                variable.set('100s')
        t = time_float
        self.axes.set_xlim([0, t])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def choose_option(self, variable, displayed_state, graph):
        if not self.zurich.info:
            return
        if not variable.curselection():
            return

        index = variable.curselection()[0]
        option = variable.get(index)
        option_list = {'Enable Demods R': '/demods/{}/sample', 'Enable Demods Cart.': None, 'Enable Demods Polar': None,
                       'Boxcars': '/boxcars/{}/wave', 'Arithmetic Units': None, 'Unpopulated': None, 'Manual': None}
        text = ['/demods/', '/boxcars/']
        for item in text:
            if item in option_list[option]:
                if item == '/demods/':
                    for i in range(0, 7):
                        if '{}'+option_list[option].format(self.zurich.info['device'], i) in self.zurich.paths:
                            self.path['{}'+option_list[option].format(self.zurich.info['device'], i)] = True
                elif item == '/boxcars/':
                    for j in range(0, 1):
                        if '{}'+option_list[option].format(self.zurich.info['device'], j) in self.zurich.paths:
                            self.path['{}'+option_list[option].format(self.zurich.info['device'], j)] = True
            else:
                if item == '/demods/':
                    for i in range(0, 7):
                        if '{}'+option_list[option].format(self.zurich.info['device'], i) in self.zurich.paths:
                            self.path['{}'+option_list[option].format(self.zurich.info['device'], i)] = False
                elif item == '/boxcars/':
                    for j in range(0, 1):
                        if '{}'+option_list[option].format(self.zurich.info['device'], j) in self.zurich.paths:
                            self.path['{}'+option_list[option].format(self.zurich.info['device'], j)] = False

        if displayed_state.get() == 'enable':
            self.update_plotter(graph, displayed_state)

    def update_plotter(self, graph, variable):
        if variable.get() == 'enable':
            self.zurich.state['Plotter'] = True
        elif variable.get() == 'disable':
            self.zurich.state['Plotter'] = False
        for element in self.path:
            if self.path[element]:
                self.add_subscribed(path=self.path[element], child_class=self, graph_class=graph)
            elif not self.path[element]:
                self.unsubscribed_path(element)

    # This function need work I haven't found the proper way to make the data collection dependent of the
    # BoxCar and the demodulator... To be continued
    def extract_data(self, data, path):
        if not(self.zurich.paths[path]):
            return
        clockbase = float(self.zurich.info['daq'].getInt('/%s/clockbase' % self.zurich.info['device']))
        # self.Value = np.append(self.Value['vals']['phi'], np.angle(Sample['x'] +1j*Sample['y']))
        amplitude = []
        t = []
        if 'demods' in path:
            if not t:
                amplitude.append(np.abs(data['x'] + 1j * data['y']))
                t.append(((data['timestamp'] - data['timestamp'][0]) / clockbase))
            else:
                amplitude[0] = np.append(amplitude[0], np.abs(data['x'] + 1j * data['y']))
                t[0] = np.append(t[0], ((data['timestamp'] - data['timestamp'][0]) / clockbase) +
                                         max(t[0]))
        elif 'boxcars' :
            if not t:
                amplitude.append(data['value'])
                t.append(((data['timestamp'] - data['timestamp'][0]) / clockbase))
            else:
                amplitude[0] = np.append(self.Value['vals'][0], data['value'])
                # Work needs to be done to optimize the offset
                t[0] = np.append(self.Value['t'][0], ((data['timestamp'] - data['timestamp'][0]) / clockbase) +
                                                       max(t[0]))
        self.axes.set_ylim([min(amplitude) - abs(min(amplitude) * 15 / 100),
                            max(amplitude) + max(amplitude) * 15 / 100])
        self.axes.set_xlim([min(1e6 * t) - abs(min(1e6 * t) * 15 / 100),
                            max(1e6 * t) + max(1e6 * t) * 15 / 100])
        self.line.set_ydata(amplitude)
        self.line.set_xdata(time)


class Boxcar:

    def __init__(self, zurich=None, line=None, axes=None, fig=None):
        # format will be #1 : device id when connected
        #                #2 : scope taken to read the data
        # line : matplotlib Line issued when you plot axis
        self.path = '/{}/inputpwas/{}/wave'
        self.path2 = '/{}/boxcars/{}/wave'
        self.line = line
        self.axes = axes
        self.fig = fig
        self.zurich = zurich
        self.xfactor = 360/(2*np.pi)
        self.frequency = None
        self.line_list = []
        self.line_list.append(Graphic.VerticalDraggableLine(self, axes=self.axes))
        self.line_list.append(Graphic.VerticalDraggableLine(self, axes=self.axes, x=150))
        self.window_start = min(self.line_list[0].x, self.line_list[1].x)
        self.window_length = abs(self.line_list[1].x - self.line_list[1].x)

    def enable_boxcar(self, pwa_input, box_input, variable):
        pwa_input = pwa_input.get()
        box_input = box_input.get()
        if not self.zurich.info:
            messagebox.showinfo(title='Error', message='There is no device connected')
            variable.set('disable')
            return
        value = None
        device = self.zurich.info['device']
        inputpwa_index = 0
        boxcar_index = 0
        if variable.get() == 'enable':
            self.zurich.state['Boxcar'] = True
            value = 1
        elif variable.get() == 'disable':
            self.zurich.state['Boxcar'] = False
            self.zurich.paths[self.path.format(device, inputpwa_index)] = False
            value = 0
        BOX_Settings = [['/%s/inputpwas/%d/oscselect' % (device, inputpwa_index), 0],
                        ['/%s/inputpwas/%d/inputselect' % (device, inputpwa_index), pwa_input],
                        ['/%s/inputpwas/%d/mode' % (device, inputpwa_index), 1],
                        ['/%s/inputpwas/%d/shift' % (device, inputpwa_index), 0.0],
                        ['/%s/inputpwas/%d/harmonic' % (device, inputpwa_index), 1],
                        ['/%s/inputpwas/%d/enable' % (device, inputpwa_index), value],
                        ['/%s/boxcars/%d/oscselect' % (device, boxcar_index), 0],
                        ['/%s/boxcars/%d/inputselect' % (device, boxcar_index), box_input],
                        ['/%s/boxcars/%d/windowstart' % (device, boxcar_index), self.window_start],
                        ['/%s/boxcars/%d/windowsize' % (device, boxcar_index), self.window_length],
                        ['/%s/boxcars/%d/limitrate' % (device, boxcar_index), 1e6],
                        ['/%s/boxcars/%d/periods' % (device, boxcar_index), 1],
                        ['/%s/boxcars/%d/enable' % (device, boxcar_index), value],
                        ]
        self.zurich.info['daq'].set(BOX_Settings)
        self.zurich.info['daq'].sync()
        self.zurich.paths[self.path.format(device, inputpwa_index)] = True
        #self.zurich.paths[self.path2.format(device, boxcar_index)] = True

    def phase_and_time(self, variable):
        if not self.zurich.info:
            messagebox.showinfo(title='Error', message='There is no device connected')
            return
        if not self.frequency:
            self.frequency = self.zurich.info['daq'].getDouble('/{}/oscs/{}/freq'.format(self.zurich.info['device'], 0))
        current = variable.current()
        if current == 0:
            self.xfactor = 1/(2*np.pi*360*self.frequency)
        else:
            self.xfactor = 360/(2*np.pi)

    def refresh(self, path):
        frequency_set = self.zurich.info['daq'].getDouble('/{}/oscs/{}/freq'.format(self.zurich.info['device'], 0))
        self.window_start = min(self.line_list[0].x, self.line_list[1].x)
        self.window_length = abs(self.line_list[0].x - self.line_list[1].x) / (2 * np.pi * 360 * frequency_set)
        self.zurich.info['daq'].unsubscribe(path)
        boxwindow = [['/%s/boxcars/%d/windowstart' % (self.zurich.info['device'], 0), self.window_start],
                     ['/%s/boxcars/%d/windowsize' % (self.zurich.info['device'], 0), self.window_length]]
        self.zurich.info['daq'].set(boxwindow)
        self.zurich.info['daq'].sync()
        self.zurich.info['daq'].subscribe(path)

    def extract_data(self, data=None, path=None):
        if not(self.zurich.paths[path]):
            return

        if (not (self.window_start != min(self.line_list[0].x, self.line_list[1].x)) or not (
                self.window_length != abs(self.line_list[0].x - self.line_list[1].x))):
            self.refresh(path=path)
        # This takes the wave data stored in the daq and push them into the  it in the assigned figure
        boxcar_data = data[path][-1]
        self.axes.axhline(0, color='k')
        boxcar_data['binphase'] = boxcar_data['binphase'] * self.xfactor
        phase = boxcar_data['binphase']
        amplitude = boxcar_data['x']
        # The inputpwa waveform is stored in 'x', currently 'y' is unused.
        self.axes.set_ylim([min(amplitude) - abs(min(amplitude) * 15 / 100),
                            max(amplitude) + max(amplitude) * 15 / 100])
        self.axes.set_xlim([min(phase) - abs(min(phase) * 15 / 100),
                            max(phase) + max(phase) * 15 / 100])
        self.line.set_ydata(amplitude)
        self.line.set_xdata(phase)
