import os
from matplotlib import pyplot as plt
import xarray as xr

ari = 100
datadir = "/g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep"

hfp = os.path.join(datadir, f"windspeed_{ari}_yr.nc")
lfp = os.path.join(datadir, f"windspeed_{ari}_yr_low_res.nc")

os.system(f"gdal_translate -outsize 10% 10% {hfp} {lfp}")
ds = xr.load_dataset(lfp)
extent = [ds.lon[0], ds.lon[-1], ds.lat[0], ds.lat[-1]]
params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
plt.rcParams.update(params)

plt.figure(figsize=(25, 25))
plt.imshow(ds.gust.data * (ds.gust.data >= 0), extent=extent)
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.colorbar()
plt.savefig(os.path.join(datadir, f"windspeed_{ari}_yr_low_res.png"))