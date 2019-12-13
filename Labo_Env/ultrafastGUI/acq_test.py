from usb_1208LS import *
import time
import numpy as np
import sys
import numpy as np
import matplotlib.pyplot as plt

start = time.time()

miniLAB = usb_miniLAB()

print('Test analog acquisition')

# This number depends on the channel you plugged in.
chan = 1

# The different options should be in the imported code
gain = miniLAB.BP_1_00V

values = np.zeros(0)
x = np.zeros(0)

for k in range(100):
	values = np.append(values, miniLAB.AIn(chan, gain))
	x = np.append(x, time.time() - start)


print('ok')
print(values)
print(np.mean(values))
plt.plot(x, values)
plt.show()
