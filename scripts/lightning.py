import sys
from os.path import join as pjoin

import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime


from cartopy import crs as ccrs
from cartopy import feature as cfeature
import matplotlib.pyplot as plt
import seaborn as sns

SOURCE = "Weatherzone Total Lightning Network (2016-2021)"
cbar_kwargs = {"shrink":0.9, 'ticks': np.arange(0, 101, 10), 'label':r"Mean lightning pulses [km$^{-2}$ year$^{-1}$]"}
states = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\raw\from_wz"
ds = xr.open_rasterio(pjoin(datapath, "lightning-density-wztln-au-201510_202103.tif"))

stationfile = r"X:\georisk\HaRIA_B_Wind\projects\multipliers\AWS_QLD\AWS_sites_location.csv"
stndf = pd.read_csv(stationfile)
ax = plt.axes(projection=ccrs.PlateCarree())
ax.figure.set_size_inches(15,12)
ds[0, :, :].plot.contourf(ax=ax, transform=ccrs.PlateCarree(), 
                 levels=np.arange(0, 101, 5), extend='max', cmap='hot_r',
                 cbar_kwargs=cbar_kwargs )
for idx, stn in stndf.iterrows():
    ax.plot(stn.Longitude, stn.Latitude, 
            transform=ccrs.PlateCarree(),
            marker='*', color='k')
    ax.annotate(stn.Station, xy=(stn.Longitude+0.01, stn.Latitude),
                textcoords='data', transform=ccrs.PlateCarree())

ax.coastlines(resolution='10m')
ax.add_feature(states, edgecolor='0.15', linestyle='--')
gl = ax.gridlines(draw_labels=True, linestyle=":")
gl.top_labels = False
gl.right_labels = False
ax.set_extent((151.0, 154.25, -29.0, -25.5))
ax.set_title("Mean annual lightning density")
fig = plt.gcf()
plt.text(0.0, -0.05, f"Source: {SOURCE}", transform=ax.transAxes, fontsize='xx-small', ha='left',)
plt.savefig(pjoin(datapath, "lightning-density-SEQ.png"), bbox_inches='tight')