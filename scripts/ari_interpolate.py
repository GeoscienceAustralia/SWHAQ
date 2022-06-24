import os

TCRM_PATH = os.path.expanduser('~/geoscience/repos/tcrm')
DATA_DIR = os.path.expanduser('~/geoscience/data/SEQ')

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import sys
import geopandas as gpd
from pykrige import OrdinaryKriging

sys.path.append(TCRM_PATH)

import hazard
import xarray as xr


def gdpWindSPeed(return_levels, mu, shape, scale, rate, npyr=365.25):
    ri = np.power((return_levels - mu) * (shape / scale) + 1, 1 / shape) / (npyr * rate)
    if not np.isscalar(ri):
        ri[np.isnan(ri)] = np.inf
    elif np.isnan(ri):
        ri = np.inf
    return ri

# load in a process synoptic and ts ARI data
fp = os.path.join(DATA_DIR, "AllStationsSuperStation_20220622.xlsx")
df = pd.read_excel(fp, skiprows=1).iloc[9:]

df["aep"] = 1.0 / df["ARI [yrs]"]
windspeeds = np.linspace(20, 100, 100)
syn_aep = np.interp(windspeeds, df.Synoptic.values, df.aep.values)
syn_aep[windspeeds > df.Synoptic.max()] = 0.0
ts_aep = np.interp(windspeeds, df.Thunderstorm.values, df.aep.values)
ts_aep[windspeeds > df.Thunderstorm.max()] = 0.0

# load TC ARI curves for stations
stnlist = gpd.read_file(os.path.join(DATA_DIR, "SEQ_station_list.shp"))
tc_df = pd.read_csv(os.path.join(DATA_DIR, "ari_params/parameters.csv"))

tc_df.columns = [c.strip() for c in tc_df.columns]
tc_df['longitude'] = stnlist.loc[tc_df.locId.values - 1].Longitude.values
tc_df['latitude'] = stnlist.loc[tc_df.locId.values - 1].Latitude.values

tc_df.locName = tc_df.locName.str.strip()
tc_df.drop_duplicates(inplace=True)
tc_df.set_index('locName', drop=False, inplace=True)

shape, scale, rate, mu = tc_df.iloc[0][['gpd_shape', 'gpd_scale', 'gpd_rate', 'gpd_thresh']].values


# spatially interpolate TC ARI curves
params = []
for i in range(len(tc_df)):
    shape, scale, rate, mu = tc_df.iloc[i][['it_shape', 'it_scale', 'it_rate', 'it_thresh']].values
    params.append([shape, scale, rate, mu])
params = np.array(params)

# SEQ grid
lats = np.linspace(-10, -30, 1000)
longs = np.linspace(137, 154, 1000)

# station lat and longs
stn_lats = tc_df.latitude.values
stn_longs = tc_df.longitude.values

param_names = ['shape', 'scale', 'rate', 'mu']
grid_params = dict()

for j in range(4):
    OK = OrdinaryKriging(
        stn_longs,
        stn_lats,
        params[:, j],
        coordinates_type='geographic',
        pseudo_inv=True,
        verbose=False,
        enable_plotting=False,
    )
    z, _ = OK.execute("grid", longs, lats)
    grid_params[param_names[j]] = z


# combine the AEP for TC, synoptic and TS
shape, scale = grid_params["shape"][:, :, None], grid_params["scale"][:, :, None]
rate, mu = grid_params["rate"][:, :, None], grid_params["mu"][:, :, None]

print("max windspeed:", hazard.GPD.gpdReturnLevel(10_000, mu, shape, scale, rate).max())

tc_aep = 1.0 / gdpWindSPeed(windspeeds[None, None, :], mu, shape, scale, rate).data
comb_aep = 1.0 - (1.0 - syn_aep[None, None, :]) * (1.0 - ts_aep[None, None, :]) * (1.0 - tc_aep)

# convert windspeed coords + AEP values to AEP coords and windspeed values
# funky code to quickly linearly interpolate (a for loop + numpy interpolate was much much slower)
ris = np.array([
    2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100,
    150, 200, 250, 300, 350, 400, 450, 500, 1000, 2000, 2500,
    5000, 10000]
)

aeps = 1 / ris

comb_aep_flat = comb_aep.reshape((-1, len(windspeeds)))
grid_idxs = np.arange(comb_aep_flat.shape[0])
aep_windspeed_grid = []

for ri, aep in zip(ris, aeps):

    mask = comb_aep >= aep
    idxs = np.where(np.diff(mask))[2]
    # print(ri, aep, len(idxs))

    w1 = comb_aep_flat[grid_idxs, idxs] - aep
    w2 = aep - comb_aep_flat[grid_idxs, idxs + 1]
    w = w1 + w2
    w1 /= w
    w2 /= w

    aep_ws = w1 * windspeeds[idxs] + w2 * windspeeds[idxs + 1]

    da = xr.DataArray(
        aep_ws.reshape(comb_aep.shape[:-1]),
        coords=dict(lon=longs, lat=lats),
        dims=["lat", "lon"]
    )
    ds = xr.Dataset(data_vars={'windspeed': da})

    ds.to_netcdf(os.path.join(DATA_DIR, "RI", f"windspeed_{ri}_yr.netcdf"))

