#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for setting up and using the data recorder of a PI device."""

from __future__ import print_function
from logging import debug, warning
from time import sleep, time

from ..common.gcscommands_helpers import isdeviceavailable
from .gcs2commands import GCS2Commands

__signature__ = 0x34b50792a0c61f3d4953a7248186832

# Invalid class attribute name pylint: disable=C0103
# Too few public methods pylint: disable=R0903
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class RecordOptions(object):
    """Defines for the kind of data to be recorded."""
    NOTHING_0 = 0
    COMMANDED_POSITION_1 = 1
    ACTUAL_POSITION_2 = 2
    POSITION_ERROR_3 = 3
    PIO_VALUE_4 = 4
    DIO_VALUE_5 = 5
    COMEDI_VALUE_6 = 6
    PIEZO_VOLTAGE_7 = 7
    TIMESTAMP_8 = 8
    INDEX_9 = 9
    TICKS_10 = 10
    DDL_OUTPUT_13 = 13
    OPENLOOP_INPUT_14 = 14
    PID_OUTPUT_15 = 15
    ANALOG_OUTPUT_16 = 16
    SENSOR_NORMALIZED_17 = 17
    SENSOR_FILTERED_18 = 18
    SENSOR_ELEC_LIN_19 = 19
    SENSOR_MECH_LIN_20 = 20
    TARGET_SLEWRATE_LIM_22 = 22
    TARGET_VELOCITY_23 = 23
    TARGET_ACCELERATION_24 = 24
    TARGET_JERK_25 = 25
    DI_VALUE_26 = 26
    DO_VALUE_27 = 27
    CTV_TARGET_VALUE_28 = 28
    CCV_CONTROL_VALUE_29 = 29
    CAV_ACTUAL_VALUE_30 = 30
    CCV_CURRENT_VALUE_31 = 31
    DRIFT_COMP_OFFSET_32 = 32
    HYBRID_MOTOR_VOLTAGE_33 = 33
    HYBRID_PIEZO_VOLTAGE_34 = 34
    SYSTEM_TIME_44 = 44
    COMMANDED_VELOCITY_70 = 70
    COMMANDED_ACCELERATION_71 = 71
    ACTUAL_VELOCITY_72 = 72
    MOTOR_OUTPUT_73 = 73
    KP_OF_AXIS_74 = 74
    KI_OF_AXIS_75 = 75
    KD_OF_AXIS_76 = 76
    SIGNAL_STATUS_REGISTER_80 = 80
    ANALOG_INPUT_81 = 81
    ACTIVE_PARAMETERSET_90 = 90
    ACTUAL_FREQUENCY_91 = 91
    P0_92 = 92
    DIA_93 = 93
    CURRENT_PHASE_A_100 = 100
    CURRENT_PHASE_B_101 = 101
    CURRENT_PHASE_C_102 = 102
    CURRENT_PHASE_D_103 = 103
    FIELD_ORIENTED_CONTROL_UD_105 = 105
    FIELD_ORIENTED_CONTROL_UQ_106 = 106
    FIELD_ORIENTED_CONTROL_ID_107 = 107
    FIELD_ORIENTED_CONTROL_IQ_108 = 108
    FIELD_ORIENTED_CONTROL_U_ALPHA_109 = 109
    FIELD_ORIENTED_CONTROL_U_BETA_110 = 110
    FIELD_ORIENTED_CONTROL_V_PHASE_111 = 111
    FIELD_ORIENTED_CONTROL_ANGLE_112 = 112
    FIELD_ORIENTED_CONTROL_ANGLE_FROM_POS_113 = 113
    FIELD_ORIENTED_CONTROL_ERROR_D_114 = 114
    FIELD_ORIENTED_CONTROL_ERROR_Q_115 = 115
    POSITION_CONTROL_OUT_120 = 120
    VELOCITY_CONTROL_OUT_121 = 121
    PILOT_CONTROL_OUT_122 = 122
    ACCELERATION_CONTROL_OUT_123 = 123
    LOW_PASS_FILTERED_VELOCITY_140 = 140
    ANALOG_IN_VALUE_141 = 141
    LOW_PASS_FILTERED_VELOCITY_ERROR_142 = 142
    ACTUAL_ACCELERATION_143 = 143
    LOW_PASS_FILTERED_ACCELERATION_ERROR_144 = 144
    TW8_SINE_REGISTER_145 = 145
    TW8_COSINE_REGISTER_146 = 146
    FAST_ALIGNMENT_INPUT_CHANNEL_150 = 150
    FAST_ALIGNMENT_PROCESS_REGISTER_151 = 151
    FAST_ALIGNMENT_GS_RESULT_ROUTINE_152 = 152
    FAST_ALIGNMENT_GS_WEIGHT_ROUTINE_153 = 153
    FAST_ALIGNMENT_GS_AMPLITUDE_ROUTINE_154 = 154
    FAST_ALIGNMENT_FINISHED_FLAG_155 = 155
    FAST_ALIGNMENT_GRADIENT_SCAN_PHASE_ROUTINE_156 = 156


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class TriggerSources(object):  # Too few public methods pylint: disable=R0903
    """Defines for sources that can trigger data recording."""
    DEFAULT_0 = 0
    POSITION_CHANGING_COMMAND_1 = 1
    NEXT_COMMAND_WITH_RESET_2 = 2
    EXTERNAL_TRIGGER_3 = 3
    TRIGGER_IMMEDIATELY_4 = 4
    DIO_CHANNEL_5 = 5
    POS_CHANGING_WITH_RESET_6 = 6
    SMO_COMMAND_WITH_RESET_7 = 7
    COMEDI_CHANNEL_8 = 8
    WAVE_GENERATOR_9 = 9

def __getopt(name, enumclass):
    """Return item of 'enumclass' which name parts start with 'name'.
     @param name : Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
     @param enumclass : Class name that contains enums.
     @return : According enum value as integer.
     """
    for item in dir(enumclass):
        match = []
        for i, itempart in enumerate(item.split('_')):
            if itempart.isdigit():
                continue
            try:
                namepart = name.split('_')[i]
            except IndexError:
                continue
            match.append(__isabbreviation(namepart.upper(), itempart.upper()))
        if all(match):
            return getattr(enumclass, item)
    raise KeyError('invalid name %r' % enumclass)


def __isabbreviation(abbrev, item):
    """Return True if first char of 'abbrev' and 'item' match and all chars of 'abbrev' occur in 'item' in this order.
    @param abbrev : Case sensitive string.
    @param item : Case sensitive string.
    @return : True if 'abbrev' is an abbreviation of 'item'.
    """
    if not abbrev:
        return True
    if not item:
        return False
    if abbrev[0] != item[0]:
        return False
    return any(__isabbreviation(abbrev[1:], item[i + 1:]) for i in range(len(item)))


def getrecopt(name):
    """Return record option value according to 'name'.
    @param name: Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
    @return : According enum value as integer.
    """
    return __getopt(name, RecordOptions)


def gettrigsources(name):
    """Return trigger option value according to 'name'.
    @param name: Short name of item, e.g. "CUR_POS". Case insensitive, separated by "_".
    @return : According enum value as integer.
    """
    return __getopt(name, TriggerSources)

# seconds
SERVOTIMES = {
    'C-663.11': 50E-6,
    'C-663.12': 50E-6,
    'C-702.00': 100E-6,
    'C-843': 410E-6,
    'C-863.11': 50E-6,
    'C-863.12': 50E-6,
    'C-867.160': 50E-6,  # verified
    'C-867.260': 50E-6,  # verified
    'C-867.262': 50E-6,  # verified
    'C-867.B0017': 100E-6,
    'C-867.B0019': 100E-6,
    'C-867.B024': 100E-6,
    'C-867.OE': 50E-6,
    'C-877': 100E-6,
    'C-880': 4096E-6,
    'C-884.4D': 50E-6,
    'C-884.4DB': 50E-6,
    'C-887': 100E-6,
    'E-710': 200E-6,
    'E-755': 200E-6,
    'E-861': 50E-6,
    'E-861.11C885': 50E-6,
    'E-871.1A1': 50E-6,
    'E-871.1A1N': 50E-6,
    'E-873': 50E-6,
    'E-873.1A1': 50E-6,
    'E-873.3QTU': 50E-6,
    'E-873.10C885': 50E-6,
}

MAXNUMVALUES = {
    'C-663.10C885': 1024,
    'C-663.11': 1024,
    'C-663.12': 1024,
    'C-702.00': 262144,
    'C-863.11': 1024,
    'C-863.12': 1024,
    'C-867.160': 8192,  # verified
    'C-867.1U': 8192,  # verified
    'C-867.260': 8192,  # verified
    'C-867.262': 8192,  # verified
    'C-867.2U': 8192,  # verified
    'C-867.2U2': 8192,  # verified
    'C-867.B0017': 8192,
    'C-867.B0019': 8192,
    'C-867.B024': 8192,
    'C-867.OE': 1024,
    'C-877': 1024,
    'C-877.1U11': 1024,  # verified
    'C-877.2U12': 1024,  # verified
    'C-884.4D': 8192,
    'C-884.4DB': 8192,
    'E-761': 8192,
    'E-861': 1024,
    'E-861.11C885': 1024,
    'E-871.1A1': 1024,
    'E-871.1A1N': 1024,
    'E-873': 1024,
    'E-873.1A1': 1024,
    'E-873.3QTU': 8192,
    'E-873.10C885': 8192,
}

PI_HDR_ADDITIONAL_INFO_NOT_AVAILABLE = 'No additional info available'


def getservotime(gcs, usepreset=True):
    """Return current servo cycle time in seconds as float.
    @type gcs : pipython.gcscommands.GCSCommands
    @param usepreset : If True, use SERVOTIMES preset if controller could not provide the value.
    @return : Current servo cycle time in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands], gcs):
        raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

    servotime = None
    if gcs.devname in ['C-702.00']:
        servotime = SERVOTIMES[gcs.devname]
    if servotime is None:
        servotime = gcs.getparam(0x0E000200)  # SERVO_UPDATE_TIME
    if servotime is None and usepreset:
        if gcs.devname in SERVOTIMES:
            servotime = SERVOTIMES[gcs.devname]
    if servotime is None:
        raise NotImplementedError('servo cycle time for %r is unknown' % gcs.devname)
    return float(servotime)


# Too many nested blocks (6/5) pylint: disable=R1702
# Too many branches (18/12) pylint: disable=R0912
# 'getmaxnumvalues' is too complex. The McCabe rating is 21 pylint: disable=R1260
def getmaxnumvalues(gcs, usepreset=True, hdr_additional_info=None):
    """Return maximum possible number of data recorder values as integer.
    @type gcs : pipython.gcscommands.GCSCommands
    @param usepreset : If True, use MAXNUMVALUES preset if controller could not provide the value.
    @param hdr_additional_info : List with the lines of the additional infomation section of the 'HDR?' answer.
                                 if 'hdr_additional_info' is an empty list or 'None'.
                                 'HDR?' is called and the list is filled
                                 if 'hdr_additional_info' is not an empty list, the content of the list is returned.
    @return : Maximum possible number of data recorder values as integer.
    """
    if not isdeviceavailable([GCS2Commands], gcs):
        raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

    if hdr_additional_info is None:
        hdr_additional_info = []

    # getparam() can return string if param id is not available in qHPA answer
    maxnumvalues = None
    if gcs.devname in ['C-702.00']:
        maxnumvalues = MAXNUMVALUES[gcs.devname]
    if not maxnumvalues:
        # E-517, E-518, E-852
        maxnumvalues = gcs.getparam(0x16000201)  # DATA REC SET POINTS
    if not maxnumvalues:
        # E-709, E-712, E-725, E-753.1CD, E-727, E-723K001
        maxpoints = gcs.getparam(0x16000200)  # DATA_REC_MAX_POINTS
        numtables = gcs.getparam(0x16000300)  # DATA_REC_CHAN_NUMBER
        if maxpoints and numtables:
            maxnumvalues = int(int(maxpoints) / int(numtables))
    if not maxnumvalues:
        # C-843
        maxpoints = gcs.getparam(0x16000200)  # DATA_REC_MAX_POINTS
        if maxpoints:
            maxnumvalues = int(int(maxpoints) / gcs.qTNR())
    if not maxnumvalues:
        # Mercury, etc.
        maxnumvalues = gcs.getparam(0x16000001)  # RECORDCYCLES_PER_TRIGGER
    if not maxnumvalues:
        _recopts, _trigopts = [], []
        if not hdr_additional_info:
            if gcs.HasqHDR():
                _recopts, _trigopts, hdr_additional_info = get_hdr_options(gcs, return_additional_info=True)
        if hdr_additional_info:
            for info in hdr_additional_info:
                if info.find('datapoints per table') != -1:
                    try:
                        maxnumvalues = int(info.split()[0])
                    except ValueError:
                        pass
    if not maxnumvalues and usepreset:
        if gcs.devname in MAXNUMVALUES:
            maxnumvalues = MAXNUMVALUES[gcs.devname]
    if not maxnumvalues:
        raise NotImplementedError('maximum number of data recorder values for %r is unknown' % gcs.devname)
    return int(maxnumvalues)


# Too many instance attributes pylint: disable=R0902
# Too many public methods pylint: disable=R0904
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class GCS2Datarecorder(object):
    """Set up and use the data recorder of a PI device."""

    def __init__(self, gcs):
        """Set up and use the data recorder of a PI device connected via 'gcs'.
        @type gcs : pipython.gcscommands.GCSCommands
        """
        debug('create an instance of Datarecorder(gcs=%s)', gcs)

        if not isdeviceavailable([GCS2Commands], gcs):
            raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

        self._gcs = gcs
        self._cfg = {
            'servotime': None,
            'numvalues': None,
            'offset': None,
            'maxnumvalues': None,
            'samplerate': None,
            'sources': None,
            'options': None,
            'trigsources': None,
            'rectables': [],
        }
        self._header = None
        self._data = None
        self._recopts = []
        self._trigopts = []
        self._additional_info = []

    @property
    def recopts(self):
        """Return supported record options as list of integers."""
        if not self._recopts:
            self._get_hdr_options()
        return self._recopts

    @property
    def trigopts(self):
        """Return supported trigger options as list of integers."""
        if not self._trigopts:
            self._get_hdr_options()
        return self._trigopts

    @property
    def additional_info(self):
        """Return supported trigger options as list of integers."""
        if not self._additional_info:
            self._get_hdr_options()
        return self._additional_info

    def _get_hdr_options(self):
        """Call qHDR comamnd and set self._recopts and self._trigopts accordingly."""
        self._recopts, self._trigopts, self._additional_info = get_hdr_options(self._gcs, return_additional_info=True)

        # There is not always an additional information available in 'HDR?'.
        if not self._additional_info:
            self._additional_info.append(PI_HDR_ADDITIONAL_INFO_NOT_AVAILABLE)

    @property
    def gcs(self):
        """Access to GCS commands of controller."""
        return self._gcs

    @property
    def servotime(self):
        """Return current servo cycle time in seconds as float.
        @rtype: float
        """
        if self._cfg['servotime'] is None:
            self._cfg['servotime'] = getservotime(self._gcs)
            debug('Datarecorder.servotime is %g secs', self._cfg['servotime'])
        return self._cfg['servotime']

    @servotime.setter
    def servotime(self, value):
        """Set current servo cycle time in seconds as float."""
        value = float(value)
        self._cfg['servotime'] = value
        debug('Datarecorder.servotime set to %g secs', self._cfg['servotime'])

    @property
    def numvalues(self):
        """Return number of data recorder values to record as integer.
        @rtype: int
        """
        if self._cfg['numvalues'] is None:
            self.numvalues = self.maxnumvalues
        return self._cfg['numvalues']

    @numvalues.setter
    def numvalues(self, value):
        """Set number of data recorder values to record to 'value' as integer."""
        value = int(value)
        if value > self.maxnumvalues:
            raise ValueError('%d exceeds the maximum number of data recorder values %d' % int(value, self.maxnumvalues))
        self._cfg['numvalues'] = value
        debug('Datarecorder.numvalues: set to %d', self._cfg['numvalues'])

    @property
    def offset(self):
        """Return start point in the record table as integer, starts with index 1.
        @rtype: int
        """
        if self._cfg['offset'] is None:
            if self.numvalues:
                return 1
        return self._cfg['offset']

    @offset.setter
    def offset(self, value):
        """Set start point in the record table as integer, starts with index 1."""
        value = int(value)
        self._cfg['offset'] = value
        debug('Datarecorder.offset: set to %d', self._cfg['offset'])

    @property
    def maxnumvalues(self):
        """Return maximum possible number of data recorder values as integer.
        @rtype: int
        """
        if self._cfg['maxnumvalues'] is None:
            self._cfg['maxnumvalues'] = getmaxnumvalues(self._gcs, hdr_additional_info=self._additional_info)
            debug('Datarecorder.maxnumvalues is %d', self._cfg['maxnumvalues'])
        return self._cfg['maxnumvalues']

    @maxnumvalues.setter
    def maxnumvalues(self, value):
        """Set maximum possible number of data recorder values as integer."""
        value = int(value)
        self._cfg['maxnumvalues'] = value
        debug('Datarecorder.maxnumvalues: set to %d', self._cfg['maxnumvalues'])

    @property
    def samplerate(self):
        """Return current sampling rate in multiples of servo cycle time as integer.
        @rtype: int
        """
        if self._cfg['samplerate'] is None:
            if self._gcs.HasqRTR():
                self._cfg['samplerate'] = self._gcs.qRTR()
            else:
                warning('device %r does not support the RTR? command', self._gcs.devname)
                self._cfg['samplerate'] = 1
        return self._cfg['samplerate']

    @samplerate.setter
    def samplerate(self, value):
        """Set current sampling rate to 'value' in multiples of servo cycle time as integer.
        @rtype: int
        """
        value = max(1, int(value))
        if self._gcs.HasRTR():
            self._gcs.RTR(value)
            self._cfg['samplerate'] = value
        else:
            warning('device %r does not support the RTR command', self._gcs.devname)
            self._cfg['samplerate'] = 1
        debug('Datarecorder.samplerate: set to %d servo cycles', self._cfg['samplerate'])

    @property
    def sampletime(self):
        """Return current sampling time in seconds as float.
        @rtype: float
        """
        return self.samplerate * self.servotime

    @sampletime.setter
    def sampletime(self, value):
        """Set current sampling time to 'value' in seconds as float."""
        self.samplerate = int(float(value) / self.servotime)
        debug('Datarecorder.sampletime: set to %g s', self.sampletime)

    @property
    def samplefreq(self):
        """Return current sampling frequency in Hz as float.
        @rtype: float
        """
        return 1. / self.sampletime

    @samplefreq.setter
    def samplefreq(self, value):
        """Set current sampling frequency to 'value' in Hz as float.
        @rtype: float
        """
        self.sampletime = 1. / float(value)
        debug('Datarecorder.samplefreq: set to %.2f Hz', self.samplefreq)

    @property
    def rectime(self):
        """Return complete record time in seconds as float.
        @rtype: float
        """
        return self.numvalues * self.sampletime

    @rectime.setter
    def rectime(self, value):
        """Set number of values to record according to 'value' as complete record time in seconds as float.
        @rtype: float
        """
        self.numvalues = float(value) / self.sampletime
        debug('Datarecorder.frequency: set to %.2f Hz', self.samplefreq)

    @property
    def rectimemax(self):
        """Return complete record time in seconds as float.
        @rtype: float
        """
        return self.maxnumvalues * self.sampletime

    @rectimemax.setter
    def rectimemax(self, value):
        """Set sample time to record for 'value' seconds (float) with max. number of points."""
        self.numvalues = self.maxnumvalues
        self.sampletime = float(value) / self.numvalues
        debug('Datarecorder.rectimemax: %d values with sampling %g s', self.numvalues, self.sampletime)

    @property
    def sources(self):
        """Return current record source IDs as list of strings, defaults to first axis."""
        self._cfg['sources'] = self._cfg['sources'] or self._gcs.axes[0]
        if isinstance(self._cfg['sources'], (list, set, tuple)):
            return self._cfg['sources']
        return [self._cfg['sources']] * len(self.rectables)

    @sources.setter
    def sources(self, value):
        """Set record source IDs as string convertible or list of them."""
        self._cfg['sources'] = value
        debug('Datarecorder.sources: set to %r', self._cfg['sources'])

    @sources.deleter
    def sources(self):
        """Reset record source IDs."""
        self._cfg['sources'] = None
        debug('Datarecorder.sources: reset')

    @property
    def options(self):
        """Return current record source IDs as list of integers, defaults to RecordOptions.ACTUAL_POSITION_2."""
        self._cfg['options'] = self._cfg['options'] or RecordOptions.ACTUAL_POSITION_2
        if isinstance(self._cfg['options'], (list, set, tuple)):
            return self._cfg['options']
        return [self._cfg['options']] * len(self.rectables)

    @options.setter
    def options(self, value):
        """Set record source IDs as integer convertible or list of them."""
        self._cfg['options'] = value
        debug('Datarecorder.options: set to %r', self._cfg['options'])

    @options.deleter
    def options(self):
        """Reset record source IDs."""
        self._cfg['options'] = None
        debug('Datarecorder.options: reset')

    @property
    def trigsources(self):
        """Return current trigger source as int or list, defaults to TriggerSources.NEXT_COMMAND_WITH_RESET_2."""
        self._cfg['trigsources'] = self._cfg['trigsources'] or TriggerSources.NEXT_COMMAND_WITH_RESET_2
        return self._cfg['trigsources']

    @trigsources.setter
    def trigsources(self, value):
        """Set trigger source IDs. If single integer then "DRT 0" is used. If list
        of integers then list size can be 1 or must match the length of self.rectables.
        """
        if isinstance(value, tuple):
            value = list(value)
        self._cfg['trigsources'] = value
        debug('Datarecorder.trigsources: set to %r', self._cfg['trigsources'])

    @trigsources.deleter
    def trigsources(self):
        """Reset trigger source IDs."""
        self._cfg['trigsources'] = None
        debug('Datarecorder.trigsources: reset')

    @property
    def rectables(self):
        """Return the record tables as list of integers."""
        if isinstance(self._cfg['sources'], (list, set, tuple)):
            numtables = len(self._cfg['sources'])
        elif isinstance(self._cfg['options'], (list, set, tuple)):
            numtables = len(self._cfg['options'])
        elif isinstance(self._cfg['trigsources'], (list, set, tuple)):
            numtables = len(self._cfg['trigsources'])
        else:
            numtables = 1
        self._cfg['rectables'] = list(range(1, numtables + 1))
        return self._cfg['rectables']

    def wait(self, timeout=0):
        """Wait for end of data recording.
        @param timeout : Timeout in seconds, is disabled by default.
        """
        if not self.rectables:
            raise SystemError('rectables are not set')
        numvalues = self.numvalues or self.maxnumvalues
        if self._gcs.HasqDRL():
            maxtime = time() + timeout
            while min([self._gcs.qDRL(table)[table] for table in self.rectables]) < numvalues:
                if timeout and time() > maxtime:
                    raise SystemError('timeout after %.1f secs while waiting on data recorder' % timeout)
        else:
            waittime = 1.2 * self.rectime
            debug('Datarecorder.wait: wait %.2f secs for data recording', waittime)
            sleep(waittime)

    def read(self, offset=None, numvalues=None, verbose=False):
        """Read out the data and return it.
        @param offset : Start point in the table as integer, starts with index 1, overwrites self.offset.
        @param numvalues : Number of points to be read per table as integer, overwrites self.numvalues.
        @param verbose : If True print a line that shows how many values have been read out already.
        @return : Tuple of (header, data), see qDRR command.
        """
        if not self.rectables:
            raise SystemError('rectables are not set')
        header = self._gcs.qDRR(self.rectables, offset or self.offset, numvalues or self.numvalues)
        while self._gcs.bufstate is not True:
            if verbose:
                print(('\rread data {:.1f}%...'.format(self._gcs.bufstate * 100)), end='')
            sleep(0.05)
        if verbose:
            print(('\r%s\r' % (' ' * 20)), end='')
        data = self._gcs.bufdata
        return header, data

    def getdata(self, timeout=0, offset=None, numvalues=None):
        """Wait for end of data recording, start reading out the data and return the data.
        @param timeout : Timeout in seconds, is disabled by default.
        @param offset : Start point in the table as integer, starts with index 1, overwrites self.offset.
        @param numvalues : Number of points to be read per table as integer, overwrites self.numvalues.
        @return : Tuple of (header, data), see qDRR command.
        """
        self.wait(timeout)
        self._header, self._data = self.read(offset, numvalues)
        return self._header, self._data

    @property
    def header(self):
        """Return header from last controller readout."""
        if self._header is None:
            self.getdata()
        return self._header

    @property
    def data(self):
        """Return data from last controller readout."""
        if self._data is None:
            self.getdata()
        return self._data

    def arm(self):
        """Ready the data recorder with given options and activate the trigger.
        If TriggerSources.NEXT_COMMAND_WITH_RESET_2 is used then the error check will be disabled.
        """
        self._header = None
        self._data = None
        if self._gcs.HasDRC():
            for i in range(len(self.rectables)):
                self._gcs.DRC(self.rectables[i], self.sources[i], self.options[i])
        else:
            warning('device %r does not support the DRC command', self._gcs.devname)
        if self._gcs.HasDRT():
            errcheck = None
            if isinstance(self.trigsources, (list, set, tuple)):
                if TriggerSources.NEXT_COMMAND_WITH_RESET_2 in self.trigsources:
                    errcheck = self._gcs.errcheck
                    self._gcs.errcheck = False
                if len(self.trigsources) == 1:
                    self.trigsources = [self.trigsources[0]] * len(self.rectables)
                for i in range(len(self.rectables)):
                    self._gcs.DRT(self.rectables[i], self.trigsources[i])
            else:
                if TriggerSources.NEXT_COMMAND_WITH_RESET_2 == self.trigsources:
                    errcheck = self._gcs.errcheck
                    self._gcs.errcheck = False
                self._gcs.DRT(0, self.trigsources)
            if errcheck is not None:
                self._gcs.errcheck = errcheck
        else:
            warning('device %r does not support the DRT command', self._gcs.devname)

    @property
    def timescale(self):
        """Return list of values for time scale of recorded data."""
        return [self.sampletime * x for x in range(self.numvalues)]


# 'get_hdr_options' is too complex. The McCabe rating is 11 pylint: disable=R1260
# Too many branches (14/12) pylint: disable=R0912
def get_hdr_options(pidevice, return_additional_info=False):
    """Call qHDR comamnd and return record and trigger options of connected device.
    @type pidevice : pipython.gcscommands.GCSCommands
    @type return_additional_info: bool
    @return : Tuple of record, trigger and additional_info options as lists of integers.
              additional_info is only returned if return_additional_info = 'True'
    """
    if not isdeviceavailable([GCS2Commands], pidevice):
        raise TypeError('Type %s is not supported!' % type(pidevice).__name__)

    state = 0  # 0: NONE, 1: RECOPTS, 2: TRIGOPTS
    recopts, trigopts, additional_info = [], [], []
    for line in pidevice.qHDR().splitlines():
        line = line.strip()
        if line.startswith('#'):
            if line.startswith('#RecordOptions'):
                state = 1
            elif line.startswith('#TriggerOptions'):
                state = 2
            elif line.startswith('#Additional information'):
                state = 3
            else:
                state = 0
            continue
        if state == 0:
            continue

        if state != 3:
            try:
                option = int(line.split('=')[0].strip())
            except ValueError:
                warning('could not parse qHDR line %r', line)
                continue

        if state == 1:
            recopts.append(option)
        elif state == 2:
            trigopts.append(option)
        elif state == 3:
            additional_info.append(line)

    if return_additional_info:
        return recopts, trigopts, additional_info

    return recopts, trigopts
