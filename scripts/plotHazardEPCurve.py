#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import xarray as xr
import pandas as pd

import fiona

from matplotlib import pyplot as plt
from matplotlib.ticker import LogLocator, NullFormatter

import seaborn as sns
context = 'talk'
sns.set_context(context)
#sns.set_style('whitegrid')

majlocator = LogLocator()

minlocator = LogLocator(base=10.0, subs=np.arange(0.1, 1, 0.1), numticks=12)

# TODO: Make this an argument to the script
# Currently set to a subset on my laptop
datapath = '/scratch/w85/swhaq/hazard/output/QLD'

groups = ['GROUP1', 'GROUP2']
rcps = ['RCP45', 'RCP85']
periods = ['1981-2020', '2021-2040', '2041-2060', '2061-2080', '2081-2100'] #'1981-2020',
colors = ['#AED6F1', '#5DADE2', '#2E86C1', '#21618C', 'k']

def plotLocation(locName, locLon, locLat, g, r):
    # For full page width figures:
    figsize = (8,6)

    # For half-page width:
    #figsize = (4,3)

    fig, ax = plt.subplots(figsize=figsize)

    for p, c in zip(periods, colors):
        scenario = f'{g}_{r}_{p}'
        ds = xr.open_dataset(os.path.join(datapath, scenario, 'hazard', 'hazard_rel_hist.nc'))
        ari = ds.ari.values
        aep = 1 - np.exp(-1./ari)
        locDict = dict(lon=locLon, lat=locLat)
        wspd = ds.sel(locDict, method='nearest')['wspd'].values.flatten()
        ax.semilogy(wspd, aep, color=c, label=p)

    ax.yaxis.set_major_locator(majlocator)
    ax.yaxis.set_minor_locator(minlocator)
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(title="Time period", fontsize='x-small')
    ax.set_ylabel("Annual exceedance probability")
    ax.set_xlabel("Wind speed [m/s]")
    ax.set_xlim((0, 100))
    ax.set_title(locName)
    ax.grid()
    ax.grid(which='minor', linestyle='--', linewidth=0.5)
    fig.tight_layout()

    # TODO: save figures to file, rather than showing them
    # To ensure the margins are correctly captured, add
    # plt.savefig(filepath, bbox_inches='tight')
    filename = f'{datapath}/plots/{context}/{g}_{r}/' + locName.replace('/', '-') + '.AEP.bc.png'
    print(filename)
    plt.savefig(filename, bbox_inches='tight')
    plt.close(fig)


def main():
    with fiona.open('/g/data/w85/uz2922/code/tcrm/input/stationlist.shp') as shp:
        for x in shp:
            locName = x['properties']['Place']
            locLon = x['properties']['Longitude']
            locLat = x['properties']['Latitude']

            if locLon < 135:
                continue
            if locLon > 160:
                continue
            if locLat < -30:
                continue
            if locLat > -5:
                continue

            for g in groups:
                for r in rcps:
                    print(g, r)
                    plotLocation(locName, locLon, locLat, g, r)

main()
