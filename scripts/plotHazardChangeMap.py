#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


datapath = 'C:/WorkSpace/swhaq/data/hazard'

g = 'GROUP1'
r = 'RCP45'
p = '2081-2100'
aris = [50, 100, 500, 2000]
figsize=(10, 10)
prj = ccrs.PlateCarree()
borders = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

levels = np.arange(-15, 16, 2.5)

scenario = f'{g}_{r}_{p}'
fname = os.path.join(datapath, scenario, 'hazard', 'hazard_change.nc')
ds = xr.open_dataset(fname)

for ari in aris:
    ax = plt.subplot(projection=prj)

    title = f"{ari}-year ARI difference - {p}"
    ds.wspd.sel({'ari':ari}).plot.contourf(levels=levels, extend='both',
                subplot_kws=dict(projection=prj), add_labels=True,
                ax=ax)

    ax.coastlines(resolution='10m')
    ax.add_feature(borders, edgecolor='k', linewidth=0.5)
    gl = ax.gridlines(draw_labels=True, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 'x-small'}
    gl.ylabel_style = {'size': 'x-small'}
    ax.set_title(title)
    plt.tight_layout()

    outputfile = os.path.join(datapath, scenario, 'plots', f'hazard_change.{ari}.png')

    plt.savefig(outputfile, bbox_inches='tight')
    plt.clf()
