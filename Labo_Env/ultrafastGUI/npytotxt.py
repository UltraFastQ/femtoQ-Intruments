# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 15:02:24 2022

@author: UltrafastQ
"""

import numpy as np

data = np.load('Spectre_01_12_2022__14_47_20.npy')

wavelength = data[0,:]
intensity = data[1,:]

print(wavelength)

with open('refDispWave.txt','w') as f :
    for i in range(0,len(wavelength)):
        f.write(str(round(wavelength[i],3))+'\t'+str(int(intensity[i]))+'\n')
    f.close()