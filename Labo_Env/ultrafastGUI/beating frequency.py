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

def droite(x,a,b):
    return (1e6*a*x/30-b*1e6)/1e3

#beat = np.arange(2.999970,2.999978,0.000001)
#beat = np.concatenate((beat,np.arange(2.999980,3.000046,0.000002)))
#beat = np.concatenate((beat,np.arange(3.000047,3.000052,0.000001)))
#beat = np.concatenate((beat,np.arange(3.000054,3.000067,0.000002)))

beat = np.arange(3,3.000046,0.000002)
beat = np.concatenate((beat,np.arange(3.000047,3.000052,0.000001)))
beat = np.concatenate((beat,np.arange(3.000054,3.000067,0.000002)))
freps = np.zeros(len(beat))
frepstds = np.zeros(len(beat))


for i in range(len(beat)):
    #data = "D:/bnc_"+str(round(beat[i],6))+"ghz.csv" # home
    data = "E:/bnc_"+str(round(beat[i],6))+"ghz.csv" # lab

    if "bnc" in data:
        delimiter = ","
        comments = "Time"
        datas = np.genfromtxt(data,delimiter=delimiter,comments=comments)
        times = 0.1*np.linspace(0,len(datas[:,0]),len(datas[:,0]))
        frepsd = datas[:,1]/1000
        frepstds[i] = np.std(frepsd)
        freps[i] = np.mean(frepsd)
        xlim1 = times[-1]
        xlim2 = 2
        yliml = "Number of Events in "+str(np.round(times[-1]/60,2))+" Minutes"

        
        
        
        """
        plt.figure()
        plt.plot(times,frepsd,color="black",alpha=0.9)
        #plt.plot(np.array([times[0],times[-1]]),np.array([frepstds,frepstds])+frepmeans,"--",label=r"$+\sigma$",linewidth=2,color="red")
        #plt.plot(np.array([times[0],times[-1]]),np.array([-frepstds,-frepstds])+frepmeans,"--",label=r"$-\sigma$",linewidth=2,color="green")
        plt.ylabel(r"Repetition Rate Variation $\delta f_{rep}$ [Hz]")
        plt.xlabel("Time [s]")
        plt.xlim(0,xlim1)
        plt.legend()
        plt.show()
        """


popt,pcov = curve_fit(droite,beat[:-2],freps[:-2])
xfit = np.arange(2.999992,3.000070,0.0000001)
perr = np.sqrt(np.diag(pcov))
print(popt)
print(perr)

plt.figure()
plt.plot(beat,freps,".")
plt.errorbar(beat, freps, yerr=frepstds,fmt="none")
plt.plot(xfit,droite(xfit,popt[0],popt[1]))
plt.grid(alpha=0.5)
plt.xlabel("Input Frequency at BNC [GHz]")
plt.ylabel("Beat Frequency at Frequency Counter [kHz]")
plt.show()









