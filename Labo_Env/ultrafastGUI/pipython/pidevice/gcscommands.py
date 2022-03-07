#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide GCS functions to control a PI device."""

from . import GCS2Commands
from . import GCS21Commands
from . import GCS21Error
from . import isgcs21

__signature__ = 0x918923b97a85efe36b5561def777984d


# Function name "GCSCommands" doesn't conform to snake_case naming style pylint: disable=C0103
def GCSCommands(gcsmessage=None, _is_umf=False, gcscommands=None):
    """Get instance of GCS2Commands or GCS21Commands or UMBCommandsBase dependent on the connected
    controller and on the availability of the GCS2Commnads and GCS21Commands class.
    Forcing a specific GCSxxCommand version is possible by 'gcscommands=GCS2Commnads' or 'gcscommands=GCS21Commands'
    :param gcsmessage : pipython.pidevice.gcsmessages.GCSMessages
    :param is_umf: Obsolete, only implemented because of compatibility reasons.
    for the UMF framework ist returned
    :param gcscommands : None or pipython.pidevice.GCS2Commands or pipython.pidevice.GCS21Commands
    :type gcsmessages: GCSMessages
    :type is_umf: boolean
    :type gcscommands: GCVCommandsBase
    :return: Instance of GCS2Commnads or GCS21Commands or UMBCommandsBase
    """

    if not gcsmessage or not gcsmessage.connected:
        raise TypeError("gcsmessage must not be 'None' and must be connected to the controller")

    # if 'gcscommands != None' force the specific GCSxxCommands version
    if not gcscommands:
        # if both GCSxxCommand calsses ar available, use isgcs21 function to find out which if a GCS2 or GCS21
        # controller is connected and return an instance to the according class
        if isgcs21(gcsmessage):
            gcsmessage.gcs_error_class = GCS21Error
            gcscommands = GCS21Commands
        else:
            gcscommands = GCS2Commands

    if not gcscommands:
        # at this point gcscommands must not be None.
        raise TypeError("syntaxversion must be 'GCS2Commands' or 'GCS21Commands'")

    return gcscommands(gcsmessage)
