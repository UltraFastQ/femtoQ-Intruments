#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

from . import gcserror
from .gcserror import GCSError
from .gcs2.gcs2commands import GCS2Commands
from .gcs2.gcs2device import GCS2Device
from .gcs21.gcs21commands import GCS21Commands
from .gcs21.gcs21device import GCS21Device
from .gcs21.gcs21commands_helpers import isgcs21
from .gcs21.gcs21error import GCS21Error
from .gcsdevice import GCSDevice

__all__ = ['GCSDevice', 'GCS2Device', 'GCS21Device', 'GCS2Commands', 'GCS21Commands', 'isgcs21']

__signature__ = 0x5901a038d04f880fc2c06678422dba6d
