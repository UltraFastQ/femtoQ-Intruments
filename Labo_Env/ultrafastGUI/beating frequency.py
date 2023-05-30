# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from scipy.optimize import curve_fit
import numba
from scipy.signal import hilbert, chirp, find_peaks
from scipy.integrate import simps
import femtoQ.tools as fq
from scipy.constants import c as C
import csv
plt.close("all")
pi = np.pi

# see number of csv file in ...... file
nfiles = 5 #exemple

i =0
fBNC = np.zeros(nfiles)
while i != nfiles:
    data = "C:/Users/milio/OneDrive/Documents/Maitrise/MokuPro et Frequency Counter/bnc_beat_stabilized_3.csv"
    if "stabilized" in data:
        
        fBNCi = data.lstrip('C:/Users/milio/OneDrive/Documents/Maitrise/MokuPro et Frequency Counter/bnc_beat_stabilized_')
        fBNCi = fBNCi.rstrip('.csv')
        fBNC[i] = float(fBNCi)
    i+=1




if "bnc" in data:
    delimiter = ","
    comments = "Time"
    datas = np.genfromtxt(data,delimiter=delimiter,comments=comments)
    times = 0.1*np.linspace(0,len(datas[:,0]),len(datas[:,0]))
    freps = datas[:,1]
    frepstds = np.std(freps)
    frepmeans = np.mean(freps)
    xlim1 = times[-1]
    xlim2 = 2
    yliml = "Number of Events in "+str(np.round(times[-1]/3600,2))+" Hours"



plt.figure()
plt.plot(times,freps,color="black",alpha=0.9)
plt.plot(np.array([times[0],times[-1]]),np.array([frepstds,frepstds])+frepmeans,"--",label=r"$+\sigma$",linewidth=2,color="red")
plt.plot(np.array([times[0],times[-1]]),np.array([-frepstds,-frepstds])+frepmeans,"--",label=r"$-\sigma$",linewidth=2,color="green")
plt.ylabel(r"Repetition Rate Variation $\delta f_{rep}$ [Hz]")
plt.xlabel("Time [s]")
plt.xlim(0,xlim1)
plt.legend()
plt.show()
















