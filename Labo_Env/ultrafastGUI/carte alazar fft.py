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

def timedom(tabnu,spectrum):
    time,Et = fq.ezifft(tabnu,spectrum,amplitudeSpectrumRecentering=(False))
    return time,Et

def freqdom(tabtime,Et):
    tabnu,spectrum = fq.ezfft(tabtime,Et,neg=True)
    return tabnu,spectrum

#volt = loadtxt('D:/2023.06.05_14.21.37_1.1.1.1.A.txt',unpack=True)
volt1 = np.load("C:/Users/milio/OneDrive/Documents/GitHub/femtoQ-Intruments/Labo_Env/ultrafastGUI/dataf.npy")
time = np.linspace(0,len(volt1)/500e6,len(volt1))
#time = time[:int(1/(1046.8749672851561)/(time[1]-time[0]))]
#volt = volt[:int(1/(1046.8749672851561)/(time[1]-time[0]))]
volt = np.hanning(len(time))*volt1



plt.figure()
plt.plot(time,volt)
plt.show()

nurf,srf = freqdom(time,volt)

b = 0.000001
frep1 = 100e6
lowpass = 1/(1+np.exp(b*(nurf-frep1/2)))
lowpassneg = 1/(1+np.exp(b*(-nurf-frep1/2)))
Sfil = lowpass[np.where(nurf>=0)]*lowpassneg[np.where(nurf>=0)]*np.abs(srf[np.where(nurf>=0)])

peakind = find_peaks(Sfil,distance = 30, threshold = 2.5e-7)[0]

plt.figure()
#plt.plot(nurf,np.abs(srf))
plt.plot(nurf[np.where(nurf>=0)],Sfil/max(Sfil))
plt.plot(nurf[np.where(nurf>=0)][peakind],Sfil[peakind]/max(Sfil),'.')
plt.semilogy()
plt.show()

tint = 1/nurf[np.where(nurf>=0)][peakind][1]
nint = int(time[-1]//tint)
#time = time[:int(1/(1/tint)/(time[1]-time[0]))]
#volt1 = volt1[:int(1/(1/tint)/(time[1]-time[0]))]












with open('C:/Users/milio/OneDrive/Documents/Maitrise/Dual-frequency comb/SPM/RetrivedSpectrumSlaveNoSPM.npy', 'rb') as f:
    Ss = np.load(f)   
with open('C:/Users/milio/OneDrive/Documents/Maitrise/Dual-frequency comb/SPM/RetrivedWavelengthsSlaveNoSPM.npy', 'rb') as f:
    wls = np.load(f)
with open('C:/Users/milio/OneDrive/Documents/Maitrise/Dual-frequency comb/SPM/RetrivedSpectrumMasterNoSPM.npy', 'rb') as f:
    Sm = np.load(f)   
with open('C:/Users/milio/OneDrive/Documents/Maitrise/Dual-frequency comb/SPM/RetrivedWavelengthsMasterNoSPM.npy', 'rb') as f:
    wlm = np.load(f)
Sm = Sm/max(Sm)
Ss = Ss/max(Ss)
wlm = wlm*1e9 

plt.figure()
#plt.plot(wlhitran,Shitran,label="Acetylene Absorption",alpha = 0.5)
plt.plot(wlm,Sm*Ss,label="Master * Slave (FROG)")
plt.xlim(1490,1640)
plt.ylim(0,1)
plt.xlabel("Wavelength [nm]")
plt.ylabel("Intensity [arb.u.]")
plt.legend()
plt.show()


"""
timef,voltf = timedom(nurf,srf*lowpass*lowpassneg)
timef = timef*1e-5

plt.figure()
plt.plot(timef,np.real(voltf))
plt.show()

fopt,S = freqdom(timef,voltf)

plt.figure()
plt.plot(fopt,np.abs(S))
plt.show()

"""














