import time
import numpy as np
import matplotlib.pyplot as plt

from class_OSM2 import OSM2

port = 'COM3'
myspectro = OSM2(port)

# reply = myspectro.setEchoOFF()
# for i in reply:
#     print(i.decode().rstrip())

# reply = myspectro.setHeaderOFF()
# for i in reply:
#     print(i.decode().rstrip())

# reply = myspectro.setWavelengthOFF()
# for i in reply:
#     print(i.decode().rstrip())

# reply = myspectro.setExposureTime(100)
# for i in reply:
#     print(i.decode().rstrip())

# reply = myspectro.startSingleExposure()
# for i in reply:
#     print(i.decode().rstrip())

# reply = myspectro.getWavelength()
# wavelength = np.asarray(reply[0:-1], dtype = np.float32)

# reply = myspectro.getCurrentSpectrum()
# intensity = np.asarray(reply[0:-1], dtype = np.float32)


low_wl,top_wl,wl_res,exp_time = 450,800,1,100
wavelength,intensity = myspectro.mAcquireSpectrum(low_wl,top_wl,wl_res,exp_time)
"""
fig, ax = plt.subplots()
ax.plot(wavelength, intensity)
ax.set(xlabel='Wavelength (nm)', ylabel='Intensity (arb)', title='Acquired Spectrum')
ax.grid()
plt.show()
"""



