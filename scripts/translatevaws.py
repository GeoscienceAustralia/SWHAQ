"""
translatevaws.py - basic script to translate VAWS output to csv

TODO:
- output as NRML 0.5
- output as OasisLMF format
"""

import os
import sys
import numpy as np
import h5py

# Read the first command line argument as the input file:
filename = sys.argv[1]

try:
    fh = h5py.File(filename, 'r')
except:
    print(f"Cannot read {filename} as an hdf5 file")
    raise

ws = fh['wind_speeds'][:]
meandi = fh['vulnerability']['mean_di'][:]
di = fh['house']['di'][:]
sd = np.std(di, axis=1)
cov = np.sqrt(sd)/meandi
base, ext = os.path.splitext(filename)
outputfile = f"{base}.csv"
np.savetxt(outputfile, np.vstack([ws, di.T]).T, fmt="%.4f", delimiter=',')

meandifile = f"{base}.mean.csv"
np.savetxt(meandifile, np.vstack([ws, meandi, cov]).T, fmt="%.4f", delimiter=',',
           header='IML, mean_loss, cov')
