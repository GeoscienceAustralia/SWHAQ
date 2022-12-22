import os
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib.ticker import ScalarFormatter, LogLocator, NullFormatter

import xarray as xr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from ari_interpolate import gdp_recurrence_intervals
import hazard
import seaborn as sns
sns.set_context("talk")
majloc = LogLocator()
minloc = LogLocator(base=10.0, subs=np.arange(0.1, 1, 0.1), numticks=12)
pe = patheffects.withStroke(foreground="white", linewidth=5)

units = "km/h"

datadir = "/g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep_pp"
IN_DIR = os.path.expanduser('/g/data/w85/QFES_SWHA/hazard/input')
pe = patheffects.withStroke(linewidth=5, foreground="white")

# plot AEP windspeeds for each station where available:
OBSDIR = "/g/data/w85/data/obs/obsep"
obsdict = {"BRISBANE AERO": "040223",
           "AMBERLEY AMO": "040004",
           "ARCHERFIELD AIRPORT": "040211",
           "BRISBANE REGIONAL OFFICE": "040214",
           "COOLANGATTA": "040717",
           "SUNSHINE COAST AIRPORT": "040861",
           "REDCLIFFE": "040958",
           "TOOWOOMBA AIRPORT": "041529",
           "TEWANTIN RSL PARK": "040908",
           "GOLD COAST SEAWAY": "040764",
           "GYMPIE": "040093",
           "DOUBLE ISLAND POINT LIGHTHOUSE": "040068",
           "CAPE MORETON LIGHTHOUSE": "040043"}

fp = os.path.join(IN_DIR, "AllStationsSuperStation_20220622.xlsx")
df = pd.read_excel(fp, skiprows=1).iloc[9:]

df["aep"] = 1 - np.exp(-1 / df["ARI [yrs]"])
windspeeds = np.linspace(20, 100, 81)
syn_aep = np.interp(windspeeds, df.Synoptic.values, df.aep.values)
syn_aep[windspeeds > df.Synoptic.max()] = 0.0
ts_aep = np.interp(windspeeds, df.Thunderstorm.values, df.aep.values)
ts_aep[windspeeds > df.Thunderstorm.max()] = 0.0

tc_df = pd.read_csv(os.path.join(IN_DIR, "tc_ari_params_", "parameters.csv"))
tc_df.columns = tc_df.columns.str.strip()

for idx, row in tc_df.iterrows():
    print(row.locName)

    tc_aep_df =  d.read_csv(os.path.join(IN_DIR, "tc_ari_params_", f"{row.locId}.csv"))
    shape, scale, rate, mu = row[['it_shape', 'it_scale', 'it_rate', 'it_thresh']].values
    tc_aep = 1.0 - np.exp(-1.0 / gdp_recurrence_intervals(windspeeds, mu, shape, scale, rate))

    tc_aep[windspeeds <= hazard.GPD.gpdReturnLevel(1, mu, shape, scale, rate)] = 0.0
    finterp = interp1d(tc_aep_df.wspd.values, tc_aep_df.AEP.values,
                    bounds_error=False, fill_value=tc_aep_df.AEP.min())
    tc_aep_pp = finterp(windspeeds)
    comb_aep_ = 1.0 - (1.0 - syn_aep) * (1.0 - ts_aep) * (1.0 - tc_aep)
    comb_aep_pp = 1.0 - (1.0 - syn_aep) * (1.0 - ts_aep) * (1.0 - tc_aep_pp)
    fig, ax = plt.subplots(1, 1, figsize=(12.8, 9.6))
    plt.title(f"{row.locName} AEP")

    if units == "km/h":
        x = windspeeds * 3.6
    else: # Assume m/s
        x = windspeeds
    plt.semilogy(x, syn_aep, label="Synoptic", path_effects=[pe])
    plt.semilogy(x, ts_aep, label="Thunderstorm", path_effects=[pe])
    #plt.semilogy(x, tc_aep, label="Tropical Cyclone", path_effects=[pe])
    plt.semilogy(x, tc_aep_pp, label="TC", path_effects=[pe], linestyle=":")

    #plt.semilogy(x, comb_aep_, label="Combined", path_effects=[pe], linestyle='-.')
    plt.semilogy(x, comb_aep_pp, label="Combined", path_effects=[pe], linestyle='-.')
    if row.locName.lstrip() in obsdict:
        obsppaep = pd.read_csv(
           os.path.join(OBSDIR, f"{obsdict[row.locName.lstrip()]}.ep.csv"),
           names = ['gust', 'ppaep'], index_col=False)
        plt.scatter(obsppaep['gust']*3.6, obsppaep['ppaep'], marker="^", s=30,
        c='k', zorder=100, label="Observations")
    plt.xlabel(f"0.2-sec gust wind speed [{units}]")
    plt.ylabel("Annual exceedance probability")
    plt.ylim((10e-5, 1))
    ax.yaxis.set_major_locator(majloc)
    ax.yaxis.set_minor_locator(minloc)
    ax.yaxis.set_minor_formatter(NullFormatter())
    plt.grid(which='major', linestyle='-')
    plt.grid(which='minor', linestyle='--', linewidth=1)
    plt.legend()
    fig.tight_layout()
    plt.savefig(os.path.join(datadir, f"windspeed_aep_{row.locName.strip()}.obs.png"))
    plt.close(fig)

    outdf = pd.DataFrame(np.array([windspeeds, syn_aep, ts_aep, tc_aep_pp, comb_aep_pp]).T,
                        columns=["windspeed", 'syn_aep', 'ts_aep', 'tc_aep', 'comb_aep'])
    outdf.to_csv(os.path.join(datadir, f"windspeed_aep_{row.locName.strip()}.csv"), index=False)

#
# plot 100 year ARI windspeed

ari = 100

# convert to low resolution
hfp = os.path.join(datadir, f"windspeed_{ari}_yr.nc")
lfp = os.path.join(datadir, f"windspeed_{ari}_yr_low_res.nc")

os.system(f"gdal_translate -outsize 10% 10% {hfp} {lfp}")

# load in an plot low resolution file
params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
          'axes.labelsize': 'x-large',
          'axes.titlesize': 'x-large',
          'xtick.labelsize': 'x-large',
          'ytick.labelsize': 'x-large'}
plt.rcParams.update(params)

ds = xr.load_dataset(lfp)
gust = ds.wind_speed_of_gust[
    np.where(ds.latitude <= -25)[0],
    np.where(ds.longitude >= 150)[0]
    ]
extent = [gust.longitude[0], gust.longitude[-1],
          gust.latitude.min(), gust.latitude.max()]
plt.figure(figsize=(25, 25))
plt.imshow(np.flipud(gust.data * (gust.data >= 0)),
           extent=extent)
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.colorbar()
plt.savefig(os.path.join(datadir, f"windspeed_{ari}_yr_low_res.png"))

