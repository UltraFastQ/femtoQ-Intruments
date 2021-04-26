from collections import OrderedDict
import tkinter as tk
import numpy as np

class AcqOpts:
    def __init__(self):
        self.chan_a_enabled = tk.BooleanVar(value=True)
        self.chan_b_enabled = tk.BooleanVar(value=False)
        self.sample_rate_opts = OrderedDict([('2 GS/s', 2000), ('1.8 GS/s', 1800), ('1.5 GS/s', 1500), ('1.2 GS/s', 1200), ('1 GS/s', 1000), ('800 MS/s', 800), ('500 MS/s', 500), ('200 MS/s', 200), ('100 MS/s', 100), ('50 MS/s', 50), ('20 MS/s', 20), ('10 MS/s', 10), ('5 MS/s', 5), ('2 MS/s', 2), ('1 MS/s', 1), ('500 KS/s', 0.5), ('200 KS/s', 0.2), ('100 KS/s', 0.1), ('50 KS/s', 0.05), ('20 KS/s', 0.02), ('10 KS/s', 0.01), ('5 KS/s', 0.005), ('2 KS/s', 0.002), ('1 KS/s', 0.001)])
        self.sample_rate_var = tk.StringVar(value='2 GS/s')
        self.__sample_rate = self.sample_rate_opts[self.sample_rate_var.get()]
        self.trig_level = tk.DoubleVar(value=0.0)
        self.chan_a_offset = tk.DoubleVar(value=0.0)
        self.chan_b_offset = tk.DoubleVar(value=0.0)
        self.time_offset = tk.IntVar(value=0)
        self.time_offset_units_opts = {'ns' : 1e-9, 'μs': 1e-6, 'ms': 1e-3, 's': 1.0}
        self.time_offset_units_var = tk.StringVar(value='ns')
        self.__time_units = self.sample_rate_opts[self.sample_rate_var.get()]
        self.trigger_enabled = tk.BooleanVar(value=False)
        self.time_zoom_level = tk.IntVar(value=1)
        self.chan_a_zoom_level = tk.IntVar(value=1)
        self.chan_b_zoom_level = tk.IntVar(value=1)

    @property
    def sample_rate(self):
        return self.sample_rate_opts[self.sample_rate_var.get()]

    @property
    def time_units(self):
        return self.time_offset_units_opts[self.time_offset_units_var.get()]

class Alazar:
    def __init__(self, mainf, graph):
        self.mainf = mainf

        self.graph = graph
        self.init_graph()

        self.acq_opts = AcqOpts()
        self.acq = None
        self.acq_config = None
        self.acquiring = False

    def init_graph(self):
        self.graph.chan_a, = self.graph.axes.plot([], [], label='Chan A')
        self.graph.chan_b, = self.graph.axes.plot([], [], label='Chan b')
        self.graph.Fig.legend(loc='upper right')

    def _get_sample_rate(self, rate):
        from GPUAcquisition import ATS
        d = {
                2000 : ATS.SAMPLE_RATE_2000MSPS,
                1800 : ATS.SAMPLE_RATE_1800MSPS,
                1500 : ATS.SAMPLE_RATE_1500MSPS,
                1200 : ATS.SAMPLE_RATE_1200MSPS,
                1000 : ATS.SAMPLE_RATE_1000MSPS,
                800 : ATS.SAMPLE_RATE_800MSPS,
                500 : ATS.SAMPLE_RATE_500MSPS,
                200 : ATS.SAMPLE_RATE_200MSPS,
                100 : ATS.SAMPLE_RATE_100MSPS,
                50 : ATS.SAMPLE_RATE_50MSPS,
                20 : ATS.SAMPLE_RATE_20MSPS,
                10 : ATS.SAMPLE_RATE_10MSPS,
                5 : ATS.SAMPLE_RATE_5MSPS,
                2 : ATS.SAMPLE_RATE_2MSPS,
                1 : ATS.SAMPLE_RATE_1MSPS,
                0.5 : ATS.SAMPLE_RATE_500KSPS,
                0.2 : ATS.SAMPLE_RATE_200KSPS,
                0.1 : ATS.SAMPLE_RATE_100KSPS,
                0.05 : ATS.SAMPLE_RATE_50KSPS,
                0.02 : ATS.SAMPLE_RATE_20KSPS,
                0.01 : ATS.SAMPLE_RATE_10KSPS,
                0.005 : ATS.SAMPLE_RATE_5KSPS,
                0.002 : ATS.SAMPLE_RATE_2KSPS,
                0.001 : ATS.SAMPLE_RATE_1KSPS
            }
        return d[rate]

    def configure_acquisition(self):
        import os
        import sys

        ATS9373_LIB_PATH = 'C:/Users/femtoQLab/source/repos/GPUAcquisition/x64/Release/'
        ATS_GPU_LIB_PATH = 'C:/AlazarTech/ATS-GPU/3.7.0/base/library/x64'
        if ATS9373_LIB_PATH not in sys.path:
            sys.path.append(ATS9373_LIB_PATH)
        if ATS_GPU_LIB_PATH not in os.environ['PATH']:
            os.environ['PATH'] += f';{ATS_GPU_LIB_PATH};'

        from GPUAcquisition import Acquisition, ATS, config
        if self.acq is None:
            self.acq = Acquisition()
        
        self.acq_config = config.AcquisitionConfig({
            'capture_clock' : {
                'source' : ATS.INTERNAL_CLOCK,
                'sample_rate' : self._get_sample_rate(self.acq_opts.sample_rate),
                'egde' : ATS.CLOCK_EDGE_RISING,
                'decimation' : 0
            },
            'input_control' : [
                {
                    'channel' : ATS.CHANNEL_A,
                    'coupling' : ATS.DC_COUPLING,
                    'input_range' : ATS.INPUT_RANGE_PM_400_MV,
                    'impedance' : ATS.IMPEDANCE_50_OHM
                },
                {
                    'channel' : ATS.CHANNEL_B,
                    'coupling' : ATS.DC_COUPLING,
                    'input_range' : ATS.INPUT_RANGE_PM_400_MV,
                    'impedance' : ATS.IMPEDANCE_50_OHM
                }
            ],
            'trigger_operation' : {
                    'trigger_operation' : ATS.TRIG_ENGINE_OP_J,
                    'trigger_engine1' : ATS.TRIG_ENGINE_J,
                    'source1' : ATS.TRIG_DISABLE,
                    'slope1' : ATS.TRIGGER_SLOPE_POSITIVE,
                    'level1' : 128,
                    'trigger_engine2' : ATS.TRIG_ENGINE_K,
                    'source2' : ATS.TRIG_DISABLE,
                    'slope2' : ATS.TRIGGER_SLOPE_POSITIVE,
                    'level2' : 128
            },
            'external_trigger' : {
                'coupling' : ATS.AC_COUPLING,
                'range' : ATS.ETR_2V5,
            },
            'trigger_delay' : 0,
            'trigger_timeout_ticks' : 0,
            'aux_io' : {
                'mode' : ATS.AUX_OUT_PACER,
                'parameter' : 125
            },
            'acquisition_setup' : {
                'channels' : (ATS.CHANNEL_A if self.acq_opts.chan_a_enabled.get() else 0) | (ATS.CHANNEL_B if self.acq_opts.chan_b_enabled.get() else 0),
                'transfer_offset' : 0,
                'pre_trigger_samples' : 0,
                'post_trigger_samples' : 1<<23,
                'records_per_buffer' : 1,
                'records_per_acquisition' : 0x7FFFFFFF,
                'adma_flags' : ATS.ADMA_CONTINUOUS_MODE | ATS.ADMA_EXTERNAL_STARTCAPTURE | ATS.ADMA_INTERLEAVE_SAMPLES,
                'gpu_flags' : 0
            },
            'num_gpu_buffers' : 10,
            'data_writing' :  {
                'fname' : '',
                'num_buffs_to_write' : 0
            }
        })
        self.acq.configure_devices(self.acq_config)
        self.acq.set_ops([], [])

    def start_acquisition(self):
        self.stop_acquisition()
        self.acquiring = True
        self.acq.start()
        self.update_graph()

    def stop_acquisition(self):
        self.acquiring = False
        if self.acq is not None:
            self.acq.stop()
        else:
            self.configure_acquisition()

    def reset_acquisition(self):
        self.stop_acquisition()
        self.configure_acquisition()

    def update_graph(self):
        if not self.acquiring:
            return

        def get_data(chan):
            if not (self.acq_opts.chan_a_enabled if chan == 'A' else self.acq_opts.chan_b_enabled).get():
                return [], []
            data_size = 1 << (self.acq_opts.time_zoom_level.get() + 11)
            data = (self.acq.get_chan_a if chan == 'A' else self.acq.get_chan_b)(data_size).cast('f').tolist()
            if not data:
                return (self.graph.chan_a if chan == 'A' else self.graph.chan_b).get_xdata(), (self.graph.chan_a if chan == 'A' else self.graph.chan_b).get_ydata()
            
            data = np.asarray(data)
            idx = 0
            if self.acq_opts.trigger_enabled.get():
                idx = np.argwhere(data > self.acq_opts.trig_level.get())[0][0]
            time = idx / (self.acq_opts.sample_rate * 1e-3)
            start_time = time + self.acq_opts.time_offset.get() * 1e9
            start_idx = int(start_time * self.acq_opts.sample_rate * 1e-3)

            y_data = data[start_idx:] + (self.acq_opts.chan_a_offset if chan == 'A' else self.acq_opts.chan_b_offset).get()
            y_data *= (self.acq_opts.chan_a_zoom_level if chan == 'A' else self.acq_opts.chan_b_zoom_level).get()**2

            x_data = np.arange(y_data.size) * 1/(self.acq_opts.sample_rate*1e-3) + start_time

            return x_data, y_data

        x_data, y_data = get_data('A')
        if not isinstance(x_data, list):
            x_range = np.min(x_data), np.max(x_data)
            y_range = np.min(y_data), np.max(y_data)
        self.graph.chan_a.set_xdata(x_data)
        self.graph.chan_a.set_ydata(y_data)

        x_data, y_data = get_data('B')
        if not isinstance(x_data, list):
            x_range[0] = min(np.min(x_data), x_range[0]) * 0.9
            x_range[1] = min(np.max(x_data), x_range[1]) * 1.1
            y_range[0] = min(np.min(y_data), y_range[0]) * 0.9
            y_range[1] = min(np.max(y_data), y_range[1]) * 1.1
        self.graph.chan_b.set_xdata(x_data)
        self.graph.chan_b.set_ydata(y_data)

        self.graph.axes.set_xlim(x_range)
        self.graph.axes.set_ylim(y_range)

        self.graph.update_graph()
        self.mainf.after(1, self.update_graph)

    def cleanup(self):
        pass
