# -*- coding: utf-8 -*-
"""
Created on Wed Jul 27 15:30:16 2022

@author: milio
"""
import time
import instrumental.drivers.spectrometers.thorlabs_ccs as ccscode
import matplotlib.pyplot as plt
import numpy as np
import femtoQ as fq


spectro = ccscode.CCS()
#print(spectro.get_device_info())
#print(spectro.get_integration_time())
#print(spectro.set_integration_time("0.02 s"))
#print(spectro.get_integration_time())
#spectro.start_single_scan()
#time.sleep(1)
#if spectro.is_data_ready():
#    data = spectro.get_scan_data()
wl = spectro._wavelength_array
spectro.start_continuous_scan()
time.sleep(5)
spectro.start_single_scan()
time.sleep(0.02)
S = spectro.get_scan_data()

plt.plot(wl,S)
plt.show()

wl = spectro._wavelength_array
spectro.start_single_scan()
time.sleep(0.02)
S = spectro.get_scan_data()

plt.plot(wl,S)
plt.show()

#plt.plot(wl,spectro._wavelength_array)
#plt.show()

