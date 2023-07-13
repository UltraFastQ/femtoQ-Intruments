# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from scipy.optimize import curve_fit
from scipy.signal import hilbert, chirp, find_peaks
from scipy.integrate import simps
import femtoQ.tools as fq
from scipy.constants import c as C
import easy_scpi as scpi

plt.close("all")
pi = np.pi

inst = scpi.Instrument('USB0') # initiates an object at specified port
inst.connect() # connects the device to specfied port

print(inst.source1.frequency()) # CW output Frequency in Hz. Returns current setting if there is no input in function

inst.display.enable("ON") # "ON" or "OFF"

modes = ["slave","external","internal"]
imode = 0
mode = modes[imode]

if mode == "slave":
    
    inst.source1.roscillator.output.state("ON")
    inst.source1.roscillator.output.frequency(100000000)
    inst.source1.roscillator.source("slave")
"""    
elif mode == "external":
    inst.source1.roscillator.output("ON")
    inst.source1.roscillator.external.frequency(99999400)
    inst.source1.roscillator.source("external")
    
elif mode == 'internal':
    inst.source1.roscillator.output("ON")
    inst.source1.roscillator.source("internal")
#inst.roscillator.source.
#inst.roscillator.external.frequency(99999400)
"""