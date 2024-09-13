import numpy as np
import matplotlib.pyplot as plt

Vin = 5

R20 = 25000
R100 = 1000

Rref = np.linspace( 100, 25000)
Vs20  = Vin * R20/(R20+Rref)
Vs100 = Vin * R100/(R100+Rref)

fig, ax = plt.subplots(1)
ax.plot( Rref, Vs20)
ax.plot( Rref, Vs100)
ax.plot( Rref, Vs20-Vs100)
plt.show()

# print( Vin*( R100/((R100+Rref)**2)- R20/((R20+Rref)**2)) )