#!/usr/bin/env python
# coding: utf-8

import os
from itertools import product
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import median_filter
import pdb
import seaborn as sns
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


datapath = '/scratch/w85/swhaq/hazard/output/QLD'
groups = ['GROUP1', 'GROUP2']
rcps = ['RCP45', 'RCP85']
periods = ['1981-2020', '2021-2040', '2041-2060', '2061-2080', '2081-2100']

g = 'GROUP1'
r = 'RCP45'
p = '2081-2100'
aris = [50, 100, 500, 2000]
figsize=(12, 10)
prj = ccrs.PlateCarree()
borders = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

palette = [(1, 1, 1),
           (0.000, 0.627, 0.235),
           (0.412, 0.627, 0.235), 
           (0.663, 0.780, 0.282),
           (0.957, 0.812, 0.000),
           (0.925, 0.643, 0.016),
           (0.835, 0.314, 0.118),
           (0.780, 0.086, 0.118)]
cmap = sns.blend_palette(palette, as_cmap=True)
levels = np.arange(30, 101., 5.)

for g in groups:
    for r in rcps:
        for p in periods:
            scenario = f'{g}_{r}_{p}'
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_rel_hist.nc')
            print(f"Processing {fname}")
            ds = xr.open_dataset(fname)
            for ari in aris:
                fig, ax = plt.subplots(1, 1, subplot_kw={'projection':prj})
                title = f"{ari}-year ARI wind speed - {p}"
                ds.wspd.sel({'ari':ari}).plot.contourf(levels=levels, extend='both',
                subplot_kws=dict(projection=prj), add_labels=True, cmap=cmap,
                ax=ax)
                ax.coastlines(resolution='10m')
                ax.add_feature(borders, edgecolor='k', linewidth=0.5)
                gl = ax.gridlines(draw_labels=True, linestyle='--')
                gl.top_labels = False
                gl.right_labels = False
                gl.xformatter = LONGITUDE_FORMATTER
                gl.yformatter = LATITUDE_FORMATTER
                gl.xlabel_style = {'size': 'x-small'}
                gl.ylabel_style = {'size': 'x-small'}
                ax.set_title(title)
                plt.tight_layout()
                outputfile = os.path.join(datapath, scenario, 'plots', f'hazard.{ari}.mps.png')
                plt.savefig(outputfile, bbox_inches='tight')
                plt.close(fig)

for p in periods:
    for ari in aris:
        fig, axes = plt.subplots(2, 2, figsize=(10, 10),
                                 subplot_kw={'projection':prj},
                                 sharex=True, sharey=True)
        ax = axes.flatten()
        for i, (g, r) in enumerate(product(groups, rcps)):
            print(f"Plotting hazard for {g} - {r} - {p} - {ari}")
            suptitle = f"{ari}-ARI wind speed - {p}"
            scenario = f"{g}_{r}_{p}"
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_rel_hist.nc')
            ds = xr.open_dataset(fname)
            title = f"{g} {r}"
            im = ds.wspd.sel({'ari':ari}).plot.contourf(levels=levels, extend='both',
                                                   subplot_kws=dict(projection=prj),
                                                   add_labels=True, add_colorbar=False,
                                                   cmap=cmap, ax=ax[i])
            ax[i].coastlines(resolution='10m')
            ax[i].add_feature(borders, edgecolor='k', linewidth=0.5)
            gl = ax[i].gridlines(draw_labels=True, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            gl.xlabel_style = {'size': 'x-small'}
            gl.ylabel_style = {'size': 'x-small'}
            ax[i].set_title(title, fontsize='small')
        fig.subplots_adjust(right=0.85, wspace=0.1, hspace=0.05, top=0.95)
        cbar_ax = fig.add_axes([0.9, 0.15, 0.025, 0.7])
        cbarlabel = "ARI wind speed [m/s]"
        fig.colorbar(im, cax=cbar_ax, label=cbarlabel)
        #plt.tight_layout()
        fig.suptitle(suptitle)
        outputfile = os.path.join(datapath, f'hazard.{ari}.{p}.mps.png')
        plt.savefig(outputfile, bbox_inches='tight')
        plt.close(fig)
            
