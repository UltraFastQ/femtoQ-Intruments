#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

from logging import debug
from ..gcsmessages import GCSMessages
from ..common.gcsbasedevice import GCSBaseDevice
from .gcs21commands import GCS21Commands

__signature__ = 0x2a007082069b2844e1067012802e8849


# Invalid method name pylint: disable=C0103
# Too many public methods pylint: disable=R0904
class GCS21Device(GCSBaseDevice, GCS21Commands):
    """Provide a device connected via the PI GCS DLL or antoher gateway, can be used as context manager."""

    def __init__(self, devname='', gcsdll='', gateway=None):
        """Provide a device, connected via the PI GCS DLL or another 'gateway'.
        @param devname : Name of device, chooses according DLL which defaults to PI_GCS2_DLL.
        @param gcsdll : Name or path to GCS DLL to use, overwrites 'devname'.
        @type gateway : pipython.pidevice.interfaces.pigateway.PIGateway
        """
        GCSBaseDevice.__init__(self, devname, gcsdll, gateway)
        messages = GCSMessages(self.dll)
        GCS21Commands.__init__(self, messages)

    def close(self):
        """Close connection to device and daisy chain."""
        debug('GCS21Device.close()')
        self.unload()

    def CloseConnection(self):
        """Reset axes property and close connection to the device."""
        del self.axes
        GCSBaseDevice.CloseConnection(self)

    def GetError(self):
        """Get current controller error.
        @return : Current error code as integer.
        """
        return self.qERR()
