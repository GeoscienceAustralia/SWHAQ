#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import median_filter

import pdb

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


datapath = '/scratch/w85/swhaq/hazard/output/QLD'
datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\hazard\projections"
groups = ['GROUP1', 'GROUP2']
rcps = ['RCP45', 'RCP85']
periods = ['2021-2040', '2041-2060', '2061-2080', '2081-2100']

g = 'GROUP1'
rlabel = {'RCP45': 'RCP 4.5', 'RCP85': 'RCP 8.5'}
p = '2081-2100'
aris = [50, 100, 500, 2000]
figsize=(12, 10)
prj = ccrs.PlateCarree()
borders = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

levels = np.arange(-100, 101, 10)

for g in groups:
    for r in rcps:
        for p in periods:
            scenario = f'{g}_{r}_{p}'
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_rel.nc')
            print(f"Processing {fname}")
            ds = xr.open_dataset(fname)
            for ari in aris:
                fig, ax = plt.subplots(1, 1, subplot_kw={'projection':prj})
                title = f"1:{ari} AEP relative difference - {p}"
                ds.wspd.sel({'ari':ari}).plot.contourf(
                    levels=levels, extend='both',
                    add_labels=True,
                    cbar_kwargs={'label':"Relative change in AEP wind speed [%]"},
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
                outputfile = os.path.join(datapath, scenario, 'plots', f'hazard_rel_change.{ari}.png')
                plt.savefig(outputfile, bbox_inches='tight')
                plt.close(fig)

from itertools import product

for p in periods:
    for ari in aris:
        fig, axes = plt.subplots(2, 2, figsize=(10,10),
                                 subplot_kw={'projection':prj},
                                 sharex=True, sharey=True)
        ax = axes.flatten()
        for i, (g, r) in enumerate(product(groups, rcps)):
            print(f"Plotting hazard change for {g} - {r} - {p} - {ari}")
            suptitle = f"Change in 1:{ari}-AEP wind speed - {p}"
            scenario = f"{g}_{r}_{p}"
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_rel.nc')
            ds = xr.open_dataset(fname)
            title = f"{g} {rlabel[r]}"
            im = ds.wspd.sel({'ari':ari}).plot.contourf(levels=levels, extend='both',
                                                   add_labels=True, add_colorbar=False,
                                                   ax=ax[i])
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
        cbarlabel = "Relative change in AEP wind speed [%]"
        fig.colorbar(im, cax=cbar_ax, label=cbarlabel)
        #plt.tight_layout()
        fig.suptitle(suptitle)
        outputfile = os.path.join(datapath, f'hazard_rel_change.{ari}.{p}.png')
        plt.savefig(outputfile, bbox_inches='tight')
        plt.close(fig)

