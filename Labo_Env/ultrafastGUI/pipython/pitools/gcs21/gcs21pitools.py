#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of helpers for using a PI device."""

from logging import debug
from time import sleep, time

from pipython.pidevice import GCS21Commands
from pipython.pidevice.common.gcscommands_helpers import isdeviceavailable
from pipython.pidevice.gcs21.gcs21commands_helpers import PIAxisStatusKeys, PIContainerUnitKeys
from pipython.pitools.common.gcsbasepitools import GCSBaseDeviceStartup, GCSBaseTools

__signature__ = 0x72ea0c8fc2f31343d382c35ffed6c0a6


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class GCS21DeviceStartup(GCSBaseDeviceStartup):  # Too many instance attributes pylint: disable=R0902
    """Provide a "ready to use" PI device."""

    DEFAULT_SEQUENCE = (
        'stopall', 'enableaxes', 'referencewait', 'resetservo',)
    SPECIAL_SEQUENCE = {}

    def __init__(self, gcs21pitools, **kwargs):
        """Provide a "ready to use" PI device.
        @type gcs21pitools : GCS21Tools
        @param kwargs : Optional arguments with keywords that are passed to sub functions.
        """
        debug('create an instance of GCS21DeviceStartup(kwargs=%s)', gcs21pitools.itemstostr(kwargs))

        if not isdeviceavailable([GCS21Tools, ], gcs21pitools):
            raise TypeError('Type %s of pidevice is not supported!' % type(gcs21pitools).__name__)

        super(GCS21DeviceStartup, self).__init__(gcs21pitools, **kwargs)

        self.prop = {
            'devname': self._pidevice.devname, 'skipeax': False, 'skipref': False, 'forceref': False
        }

    def run(self):
        """Run according startup sequence to provide a "ready to use" PI device."""
        debug('GCS21DeviceStartup.run()')
        sequence = self.SPECIAL_SEQUENCE.get(self.prop['devname'], self.DEFAULT_SEQUENCE)
        for func in sequence:
            getattr(self, '%s' % func)()

    def referencewait(self):
        """Reference unreferenced axes if according option has been provided and wait on completion."""
        debug('GCS21DeviceStartup.referencewait()')
        if self.prop['skipref']:
            return

        axes_to_reference = []
        control_modes_before_ref = {}
        axes_status = self.pidevice.qSTV()
        refmodes = self._refmodes if self._refmodes else [None] * len(self._pidevice.allaxes)
        for i, refmode in enumerate(refmodes[:self._pidevice.numaxes]):
            if not refmode:
                continue

            axis = self._pidevice.axes[i]
            if not axes_status[axis][PIAxisStatusKeys.REFERENCE_STATE.value]:
                axes_to_reference.append(axis)
                control_modes_before_ref.update({axis:axes_status[axis][PIAxisStatusKeys.MOP.value]})
                self.pidevice.SAM(axis, '0x0')
                self._pidevice.FRF(axis)

        self._pitools.waitonreferencing(axes_to_reference, **self._kwargs)

        for axis in control_modes_before_ref:
            self.pidevice.SAM(axis, control_modes_before_ref[axis])

    def resetservo(self):
        """Reset servo if it has been changed during referencing."""
        debug('GCS21DeviceStartup.resetservo()')
        if self.servostates is not None:
            self._pitools.setservo(self.servostates)

    def enableaxes(self):
        """Enable all connected axes if appropriate."""
        debug('GCS21DeviceStartup.enableaxes()')
        if not self._pidevice.HasEAX() or self.prop['skipeax']:
            return

        for axis in self._pidevice.axes:
            self._pidevice.EAX(axis, True)

    def _isreferenced(self, axis):
        """Check if 'axis' has already been referenced with 'refmode'.
        @param axis : Name of axis to check as string.
        @return : False if 'axis' is not referenced or must be referenced.
        """
        if self.prop['forceref']:
            return False

        return self._pidevice.qFRF(axis)[axis]

    def stopall(self):
        """Stop all axes."""
        debug('GCS21DeviceStartup.stopall()')

        axes_state = self.pidevice.qSTV()
        self._pitools.stopall(**self._kwargs)
        affected_axes = [axis for axis in axes_state
                         if PIContainerUnitKeys.AXIS.value in axis
                         and axes_state[axis][PIAxisStatusKeys.AXIS_ENABLE.value] is True]

        for axis in affected_axes:
            self.pidevice.EAX(axis, axes_state[axis][PIAxisStatusKeys.AXIS_ENABLE.value])
            self.pidevice.SAM(axis, axes_state[axis][PIAxisStatusKeys.MOP.value])

        self._pidevice.checkerror()


class GCS21Tools(GCSBaseTools):  # Too  public methods pylint: disable=R0903
    """
    Provides a PI tool collection
    """

    PAMID_NEGATIVE_AXIS_LIMIT = '0x121'
    PAMID_POSITIVE_AXIS_LIMIT = '0x122'

    def __init__(self, pidevice):
        """Provide a "ready to use" PI device.
        @type pidevice : pipython.gcscommands.GCS21Commands
        """
        if not isdeviceavailable([GCS21Commands, ], pidevice):
            raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

        super(GCS21Tools, self).__init__(pidevice, )

    def startup(self, _stages=None, refmodes=None, servostates=True, **kwargs):
        assert not isinstance(refmodes, tuple), 'argument "refmodes" must not to be of type "tuple"'
        devstartup = GCS21DeviceStartup(self, **kwargs)

        devstartup.refmodes = refmodes
        devstartup.servostates = servostates
        devstartup.run()
        return devstartup

    def stopall(self, **kwargs):
        """Stops all axes an waits until the affected axes have finished their stop procedure.
        :param kwargs : Optional arguments with keywords that are passed to sub functions.
        """
        self._pidevice.StopAll(noraise=True)
        self._wait_on_stopall(**kwargs)

    def _wait_on_stopall(self, timeout=300, polldelay=0.1):
        """Wait until controller is on "ready" state and finally query controller error.
        @param timeout : Timeout in seconds as float.
        @param polldelay : Delay time between polls in seconds as float.
        """
        maxtime = time() + timeout
        while any(self._read_axis_status_flag(axes=[],
                                              flag=PIAxisStatusKeys.ERROR_STATE.value,
                                              defaultvalue=False,
                                              throwonaxiserror=False).values()):
            if time() > maxtime:
                raise SystemError('waitonready() timed out after %.1f seconds' % timeout)
            sleep(polldelay)

    def _move_to_middle(self, axes):
        targets = {}
        for axis in axes:
            rangemin = self._pidevice.qSPV('RAM', axis, '-', self.PAMID_NEGATIVE_AXIS_LIMIT)['RAM'][axis]['-'][
                self.PAMID_NEGATIVE_AXIS_LIMIT]
            rangemax = self._pidevice.qSPV('RAM', axis, '-', self.PAMID_POSITIVE_AXIS_LIMIT)['RAM'][axis]['-'][
                self.PAMID_POSITIVE_AXIS_LIMIT]
            targets[axis] = rangemin + (rangemax - rangemin) / 2.0
        self._pidevice.MOV(targets)

    def _get_servo_state(self, axes):
        axes = self.getaxeslist(axes)
        answer = dict(list(zip(axes, [False] * len(axes))))
        if self._pidevice.HasqSVO():

            if len(axes) == 1:
                axes_servo = self._pidevice.qSVO(axes)
            else:
                axes_servo = self._pidevice.qSVO()

            for axis in axes_servo:
                if not axis in axes:
                    continue

                answer[axis] = axes_servo[axis]

        return answer

    def _read_axis_status_flag(self, axes, flag, defaultvalue=False, throwonaxiserror=False):
        axes_status_flag = self._pidevice.get_axes_status_flag(axes, flag, throwonaxiserror)

        if not axes_status_flag:
            axes_status_flag = dict(list(zip(axes, [defaultvalue] * len(axes))))

        return axes_status_flag

    def _isreferenced(self, axes, throwonaxiserror=False):
        """Check if 'axes'  already have been referenced with.
        @param axes : List of axes.
        @return : dict {<Axis>: <bool>, } or {} if axis is .
        """
        axes = self.getaxeslist(axes)
        if not axes:
            return {}

        return self._read_axis_status_flag(axes=axes, flag=PIAxisStatusKeys.REFERENCE_STATE.value, defaultvalue=False,
                                           throwonaxiserror=throwonaxiserror)

    def _get_closed_loop_on_target(self, axes, throwonaxiserror=False):
        axes = self.getaxeslist(axes)
        if not axes:
            return {}

        return self._read_axis_status_flag(axes=axes, flag=PIAxisStatusKeys.ON_TARGET.value, defaultvalue=False,
                                           throwonaxiserror=throwonaxiserror)

    def _get_open_loop_on_target(self, axes):
        return dict(list(zip(axes, [True] * len(axes))))

    # Too many arguments pylint: disable=R0913
    def _wait_to_the_end_of_reference(self, axes, timeout, polldelay):
        maxtime = time() + timeout
        while not all(list(self._isreferenced(axes, throwonaxiserror=True).values())):
            if time() > maxtime:
                self.stopall()
                raise SystemError('waitonreferencing() timed out after %.1f seconds' % timeout)
            sleep(polldelay)

    def _enable_axes(self, axes):
        for axis in axes:
            self._pidevice.EAX(axis, True)
