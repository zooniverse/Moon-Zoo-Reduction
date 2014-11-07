import numpy as np
from matplotlib import pyplot as plt

c = np.arange(1000)
cm = np.arange(0.0, 1.0001, 0.001)
w1 = 1.0 + 0.25*np.arcsinh(c/100.)
w2 = np.sqrt(1.0 - cm)
w = np.dot(w1[:,None], w2[None,:])
plt.imshow(w[::-1], extent=(0, 1, 0, 1000), aspect=1.0/1000)
plt.xlabel('$count_m/count$', labelpad=20)
plt.ylabel('$count$', labelpad=5)
cb = plt.colorbar()
cb.set_label('$weight$', labelpad=10)
plt.subplots_adjust(bottom=0.2, left=0.05)
plt.contour(w, levels=[0.71, 0.9], colours='k', linestyles=['dashed', 'dotted'], extent=(0, 1, 0, 1000), aspect=1.0/1000)
plt.savefig('weight.png')
