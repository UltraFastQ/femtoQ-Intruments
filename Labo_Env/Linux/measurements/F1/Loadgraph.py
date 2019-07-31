import numpy as np
import matplotlib.pyplot as plt
import os
import ezfft

files = []
dir_path = os.getcwd()

for r, d, f in os.walk(dir_path):
    for file in f:
        if '.npy' in file:
            files.append(os.path.join(r, file))

for i, f in enumerate(files):
    values = np.load(f)
    x = values[0]
    x = x
    y = values[1]
    f, s = ezfft.ezfft(x, y)
    s = np.abs(s)
    s = s/np.max(s)
    plt.figure(i)
    plt.plot(x, y)
    plt.figure(i+1)
    plt.plot(f, s)
    break

plt.show()
