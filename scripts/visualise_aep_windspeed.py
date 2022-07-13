import os
from matplotlib import pyplot as plt
from matplotlib import patheffects
import xarray as xr
import pandas as pd
import numpy as np
from ari_interpolate import gdp_recurrence_intervals
import hazard


datadir = "/g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep"
IN_DIR = os.path.expanduser('/g/data/w85/QFES_SWHA/hazard/input')
pe = patheffects.withStroke(linewidth=5, foreground="white")
# plot AEP windspeeds for one station

fp = os.path.join(IN_DIR, "AllStationsSuperStation_20220622.xlsx")
df = pd.read_excel(fp, skiprows=1).iloc[9:]

df["aep"] = 1 - np.exp(-1 / df["ARI [yrs]"])
windspeeds = np.linspace(20, 100, 100)
syn_aep = np.interp(windspeeds, df.Synoptic.values, df.aep.values)
syn_aep[windspeeds > df.Synoptic.max()] = 0.0
ts_aep = np.interp(windspeeds, df.Thunderstorm.values, df.aep.values)
ts_aep[windspeeds > df.Thunderstorm.max()] = 0.0

i = 0
tc_df = pd.read_csv(os.path.join(IN_DIR, "tc_ari_params", "parameters.csv"))
tc_df.columns = [c.strip() for c in tc_df.columns]
shape, scale, rate, mu = tc_df.iloc[i][['it_shape', 'it_scale', 'it_rate', 'it_thresh']].values
tc_aep = 1.0 - np.exp(-1.0 / gdp_recurrence_intervals(windspeeds, mu, shape, scale, rate))
tc_aep[windspeeds <= hazard.GPD.gpdReturnLevel(1, mu, shape, scale, rate)] = 0.0

comb_aep_ = 1.0 - (1.0 - syn_aep) * (1.0 - ts_aep) * (1.0 - tc_aep)

plt.figure(figsize=(10, 10))
plt.title(f"{tc_df.iloc[i].locName} AEP")
plt.semilogy(windspeeds, syn_aep, label="Synoptic", path_effects=[pe])
plt.semilogy(windspeeds, ts_aep, label="Thunderstorm", path_effects=[pe])
plt.semilogy(windspeeds, tc_aep, label="Tropical Cyclone", path_effects=[pe])
plt.semilogy(windspeeds, comb_aep_, label="Combined", path_effects=[pe])
plt.xlabel("Windspeed (m/s)")
plt.ylabel("AEP")
plt.grid()
plt.legend()
plt.savefig(os.path.join(datadir, f"windspeed_aep_{tc_df.iloc[i].locName}.png"))

outdf = pd.DataFrame(np.array([windspeeds, syn_aep, ts_aep, tc_aep, comb_aep_]), columns=["windspeed", 'syn_aep', 'ts_aep', 'tc_aep', 'comb_aep'])
breakpoint()
#
# plot 100 year ARI windspeed

ari = 100

# convert to low resolution
hfp = os.path.join(datadir, f"windspeed_{ari}_yr.nc")
lfp = os.path.join(datadir, f"windspeed_{ari}_yr_low_res.nc")

os.system(f"gdal_translate -outsize 10% 10% {hfp} {lfp}")

# load in an plot low resolution file
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
# negative values indicate outside of wind multiplier/study domain
plt.imshow(ds.gust.data * (ds.gust.data >= 0), extent=extent)
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.colorbar()
plt.savefig(os.path.join(datadir, f"windspeed_{ari}_yr_low_res.png"))

