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
    time,Et = fq.ezifft(tabnu,spectrum)
    return time,Et

def freqdom(tabtime,Et):
    tabnu,spectrum = fq.ezfft(tabtime,Et)
    return tabnu,spectrum

try:
    voltraw = np.load("C:/Users/milio/OneDrive/Documents/Maitrise/Dual-frequency comb/Data/data 500Hz_500MS_filter.npy")
    #voltraw = np.load("test.npy")
except:
    voltraw = loadtxt('C:/Users/Liom-admin/Documents/AlazarTech/test_1.1.1.1.B.txt',unpack=True)
    np.save("test.npy",voltraw)
    
sample_rate = 500e6 #S/s
timeraw = np.linspace(0,len(voltraw)/sample_rate,len(voltraw))
hilbertraw = hilbert(voltraw)

voltraw = voltraw-np.mean(voltraw)
Tpeakind = find_peaks(np.abs(hilbertraw),height=0.75*np.max(abs(hilbertraw)),distance = 2000)[0]
Tpeak = timeraw[Tpeakind]
Hpeak = abs(hilbertraw)[Tpeakind]

#plt.figure()
#plt.plot(timeraw,voltraw)
#plt.plot(timeraw,np.abs(hilbertraw))
#plt.plot(Tpeak,Hpeak,".")
#plt.title("Raw data")
#plt.show()

dtpeak = np.zeros(len(Tpeakind)-1)
for i in range(1,len(Tpeakind)):
    dtpeak[i-1] = Tpeak[i]-Tpeak[i-1]

plt.figure()
plt.plot(Tpeak[1:],dtpeak-np.mean(dtpeak))
plt.show()

nuigm,Sigm = fq.ezfft(Tpeak[1:],dtpeak-np.mean(dtpeak))

plt.figure()
plt.plot(nuigm[np.where(nuigm>0)],np.abs(Sigm)[np.where(nuigm>0)])
plt.show()


nurf,srf = freqdom(timeraw,voltraw)

b = 0.000001
a = 10
frep1 = 100e6
lowf = 1e7
lowpass = 1/(1+np.exp(b*(nurf-20e6)))
lowpassneg = 1/(1+np.exp(b*(-nurf+5e6)))
highpass = -1/((1+np.exp(a*(nurf-lowf)))*(1+np.exp(-a*(nurf+lowf))))+1
#Sfil = lowpass[np.where(nurf>=0)]*lowpassneg[np.where(nurf>=0)]*np.abs(srf[np.where(nurf>=0)])*highpass[np.where(nurf>=0)]
Sfil = np.abs(srf[np.where(nurf>=0)])

#Speak = lowpass[np.where(nurf>=0)]*lowpassneg[np.where(nurf>=0)]*np.abs(srf[np.where(nurf>=0)])
#peakind = find_peaks(Speak,threshold=0.5*np.max(Speak))[0]

plt.figure()
#plt.plot(nurf,np.abs(srf))
plt.plot(nurf[np.where(nurf>=0)],Sfil/max(Sfil))
plt.plot(nurf,lowpass*lowpassneg)
#plt.plot(nurf[np.where(nurf>=0)][peakind],Speak[peakind]/max(Speak),".")
#plt.semilogy()
plt.title("Filtered-Frequency")
plt.show()

#plt.figure()
#plt.plot(nurf,np.abs(srf))
#plt.plot(nurf,np.real(srf))
#plt.plot(nurf,np.imag(srf))
#plt.plot(nurf[np.where(nurf>=0)][peakind],Speak[peakind]/max(Speak),".")
#plt.semilogy()
#plt.title("Filtered-Frequency")
#plt.show()



srff = srf*lowpass*lowpassneg#*highpass

tf,Etf = timedom(nurf,srff)
tf = tf+tf[-1]

plt.figure()
plt.plot(tf,np.abs(Etf))
plt.title("Filtered-Time")
plt.show()


#tint = 1/nurf[np.where(nurf>=0)][peakind[0]]
#tint = 0.002
#nint = int(tf[-1]//tint)
nint = len(Tpeakind)-1
nint = 1
voltavg = 0

i = 0
#t1 = 0.001295
#t2 = 0.001299
t1 = 0.01003
t2 = 0.01006
while i != nint:
    #voltavg = Etf[np.where((tf>=timeraw[Tpeakind][i]) & (tf<=timeraw[Tpeakind][i+1]))]
    #lenv = len(voltavg)
    #print(len(voltavg))
    voltavg += Etf[np.where((tf>t1)&(tf<t2))[0]] # ajuster pour jiter entre interferogrammes? ###############################
    i += 1

    


timeavg = tf[np.where((tf>t1)&(tf<t2))[0]]
#timeavg = tf[np.where((tf>=timeraw[Tpeakind][0]) & (tf<=timeraw[Tpeakind][1]))]
voltavg = np.hanning(len(timeavg))*voltavg
nurfavg,srfavg = freqdom(timeavg,voltavg)

plt.figure()
#plt.plot(nurf,np.abs(srf))
plt.plot(nurfavg[np.where(nurfavg>=0)],(np.abs(srfavg[np.where(nurfavg>=0)])/max(np.abs(srfavg[np.where(nurfavg>=0)])))**2)
plt.semilogy()
plt.title(f"Filtered-Averaged-N_int={nint}-Frequency")
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














