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

frep = 100e6
dfrep = 100
N = frep/dfrep+1
fsync =  N*frep
#print(fsync)



try:
    voltraw = np.load("C:/Users/Liom-admin/Documents/GitHub/femtoQ-Intruments/Labo_Env/ultrafastGUI/data 100Hz 100MS.npy")
except:
    voltraw = loadtxt('C:/Users/Liom-admin/Documents/AlazarTech/2023.06.07_11.26.18_100Hz_100MS_1.1.1.1.B.txt',unpack=True)
sample_rate = 100e6 #S/s
timeraw = np.linspace(0,len(voltraw)/sample_rate,len(voltraw))

plt.figure()
plt.plot(timeraw,voltraw)
#plt.plot(timeraw,np.imag(hilbert(voltraw)))
plt.title("Raw data")
plt.show()


nurf,srf = freqdom(timeraw,voltraw)
b = 0.000001
a = 0.1
frep1 = 100e6
lowf = 800000
lowpass = 1/(1+np.exp(b*(nurf-frep1/2)))
lowpassneg = 1/(1+np.exp(b*(-nurf-frep1/2)))
highpass = -1/((1+np.exp(a*(nurf-lowf)))*(1+np.exp(-a*(nurf+lowf))))+1
Sfil = lowpass[np.where(nurf>=0)]*lowpassneg[np.where(nurf>=0)]*np.abs(srf[np.where(nurf>=0)])*highpass[np.where(nurf>=0)]

Speak = lowpass[np.where(nurf>=0)]*lowpassneg[np.where(nurf>=0)]*np.abs(srf[np.where(nurf>=0)])
peakind = find_peaks(Speak,threshold=0.5*np.max(Speak))[0]

plt.figure()
#plt.plot(nurf,np.abs(srf))
plt.plot(nurf[np.where(nurf>=0)],Sfil/max(Sfil))
#plt.plot(nurf[np.where(nurf>=0)][peakind],Speak[peakind]/max(Speak),".")
#plt.semilogy()
plt.title("Filtered-Frequency")
plt.show()

srff = srf*lowpass*lowpassneg*highpass

tf,Etf = timedom(nurf,srff)
tf = tf+tf[-1]

plt.figure()
plt.plot(tf,np.real(Etf))
plt.title("Filtered-Time")
plt.show()


tint = 1/nurf[np.where(nurf>=0)][peakind[0]]
#nint = int(tf[-1]//tint)
nint = 1
voltavg = 0
i = 0

while i != nint:
    voltavg += Etf[:int(1/(1/tint)/(tf[1]-tf[0]))]
    #voltavg += Etf[np.where((tf>0.00214)&(tf<0.00217))[0]]
    i += 1


timeavg = tf[:int(1/(1/tint)/(tf[1]-tf[0]))]
#timeavg = tf[np.where((tf>0.00214)&(tf<0.00217))[0]]
nurfavg,srfavg = freqdom(timeavg,voltavg)

plt.figure()
#plt.plot(nurf,np.abs(srf))
plt.plot(nurfavg[np.where(nurfavg>=0)],np.abs(srfavg[np.where(nurfavg>=0)])/max(np.abs(srfavg[np.where(nurfavg>=0)])))
#plt.semilogy()
plt.title(fr"Filtered-Averaged-$N_{int}$={nint}-Frequency")
plt.show()


#time = time[:int(1/(100)/(time[1]-time[0]))]
#volt = volt1[:int(1/(100)/(time[1]-time[0]))]
#volt = np.hanning(len(time))*volt

#timet = time[np.where((time>0.00214)&(time<0.00217))[0]]
#voltt = volt1[np.where((time>0.00214)&(time<0.00217))[0]]
#voltt = voltt-np.mean(voltt)










"""


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
plt.plot(wlm,2*np.sqrt(Sm*Ss)/max(2*np.sqrt(Sm*Ss)),label="Master * Slave (FROG)")
plt.xlim(1490,1640)
plt.ylim(0,1)
plt.xlabel("Wavelength [nm]")
plt.ylabel("Intensity [arb.u.]")
plt.legend()
plt.show()
"""

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














