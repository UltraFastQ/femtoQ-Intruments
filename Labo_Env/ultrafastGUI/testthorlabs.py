# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from scipy.optimize import curve_fit
import numba
from scipy.signal import hilbert, chirp, find_peaks
from scipy.integrate import simps
import femtoQ.tools as fq
import scipy.fftpack as ft
import instrumental.drivers.spectrometers.thorlabs_ccs as ccscode

#allDevices = _deviceMgr.ListAll[OSA]();

Spectro = ccscode.CCS()

Spectro.start_single_scan()
plt.plot(Spectro._wavelength_array,Spectro.get_scan_data())
plt.show()

Spectro.start_single_scan()
plt.plot(Spectro._wavelength_array,Spectro.get_scan_data())
plt.show()

#data = Spectro.take_data()
#plt.plot(data[1],data[0])

"""
from newportxps import NewportXPS
xps = NewportXPS('164.54.160.000', username='Administrator', password='Please.Let.Me.In')
print(xps.status_report())
 # XPS host:         164.54.160.000 (164.54.160.000)
 # Firmware:         XPS-D-N13006
 # Current Time:     Sun Sep 16 13:40:24 2018
 # Last Reboot:      Wed Sep 12 14:46:44 2018
 # Trajectory Group: None
 # Groups and Stages


for gname, info in xps.groups.items():
    print(gname, info)

for sname, info in xps.stages.items():
    print(sname, xps.get_stage_position(sname), info)


xps.move_stage('SampleZ.Pos', 1.0)

xps.home_group('DetectorX')
"""