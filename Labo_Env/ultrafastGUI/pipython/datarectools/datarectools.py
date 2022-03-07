#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for setting up and using the data recorder of a PI device."""

from __future__ import print_function

__signature__ = 0x9ef82b7849165c2349e7804a66a1a8c4

from ..pidevice.common.gcscommands_helpers import isdeviceavailable
from ..pidevice.gcs2.gcs2commands import GCS2Commands
from ..pidevice.gcs2.gcs2datarectools import GCS2Datarecorder
from ..pidevice.gcs21.gcs21commands import GCS21Commands
from ..pidevice.gcs21.gcs21datarectools import GCS21Datarecorder

# Function name "Datarecorder" doesn't conform to snake_case naming style pylint: disable=C0103
def Datarecorder(gcs, recorder_id=''):
    """
    Returns an instance to GCS2Datarecorder or GCS21Datarecorder depending on the controller type
    :param gcs: pipython.gcscommands.GCSCommands
    :param recorder_id: the data recorder Id for GCS21 contrllers
    :return:GCS2Datarecorder or GCS21Datarecorder
    """
    if isdeviceavailable([GCS21Commands, ], gcs):
        return GCS21Datarecorder(gcs, recorder_id)

    if isdeviceavailable([GCS2Commands], gcs):
        return GCS2Datarecorder(gcs)

    raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)
