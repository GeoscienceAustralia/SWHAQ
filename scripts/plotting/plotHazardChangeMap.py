#!/usr/bin/env python
# coding: utf-8

import os

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

from scipy import signal

def gaussKern(size):
    """
    Calculate a normalised Gaussian kernel to apply as a smoothing
    function.

    :param int size: the size of the kernel to use (how many points will be
                used in the smoothing operation).
    :returns: :class:`numpy.ndarray` normalised 2D kernel array for use in
               convolutions
    """
    size = int(size)
    x, y = np.mgrid[-size:size + 1, -size:size + 1]
    g = np.exp(-(x**2/float(size) + y**2/float(size)))
    return g / g.sum()

def smooth(im, n=15):
    """
    Smooth a 2D array `im` by convolving with a Gaussian kernel of size `n`.

    :param im: Array of values to be smoothed
    :type  im: :class:`numpy.ndarray`
    :param int n: Number of points to include in the smoothing.

    :returns: smoothed array (same dimensions as the input array)

    """
    g = gaussKern(n)
    improc = signal.convolve2d(im, g, mode='same', boundary='symm')
    return improc

def subset(ds, extent):

    data = ds.sel(
        lat=slice(extent[3], extent[2]),
        lon=slice(extent[0], extent[1])
    )
    return data


datapath = '/scratch/w85/swhaq/hazard/output/QLD'
datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\hazard\projections"
datapath = '/g/data/w85/QFES_SWHA/hazard/output/'
groups = ['GROUP1', 'GROUP2']
rcps = ['RCP45', 'RCP85']
periods = ['2021-2040', '2041-2060', '2061-2080', '2081-2100']

extent = (150, 155, -30, -24)
bbox = dict(boxstyle="round", fc="white", alpha=0.5)
g = 'GROUP1'
rlabels = {'RCP45': "RCP 4.5", "RCP85": "RCP 8.5"}
p = '2081-2100'
aris = [50, 100, 500, 2000]
figsize=(12, 10)
prj = ccrs.PlateCarree()
borders = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='10m',
        facecolor='none')

levels = np.arange(-15, 16, 2.5)

for g in groups:
    for r in rcps:
        for p in periods:
            scenario = f'{g}_{r}_{p}'
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_change.nc')
            print(f"Processing {fname}")
            ds = xr.open_dataset(fname)
            lats = ds.lat.sel(lat=slice(extent[3], extent[2])).values
            lons = ds.lon.sel(lon=slice(extent[0], extent[1])).values
            lat, lon = np.meshgrid(lats, lons)
            dx = np.mean(np.diff(ds.lon.values))
            for ari in aris:
                fig, ax = plt.subplots(1, 1, subplot_kw={'projection':prj})
                title = f"1:{ari} AEP difference - {p}"
                data = subset(ds.wspd.sel({'ari': ari}), extent)
                sdata = smooth(data, int(1/dx))
                cs = ax.contourf(lon, lat, sdata.T, levels=levels, extend='both', cmap='RdBu_r')
                plt.colorbar(cs, extend='both', label="Change in AEP wind speed [m/s]", ax=ax)
                ax.set_extent(extent)
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
                outputfile = os.path.join(datapath, scenario, 'plots', f'hazard_change.{ari}.png')
                plt.savefig(outputfile, bbox_inches='tight')
                plt.close(fig)

from itertools import product

for p in periods:
    for ari in aris:
        fig, axes = plt.subplots(2, 2, figsize=(10, 10),
                                 subplot_kw={'projection':prj},
                                 sharex=True, sharey=True)
        ax = axes.flatten()
        for i, (g, r) in enumerate(product(groups, rcps)):
            print(f"Plotting hazard change for {g} - {r} - {p} - {ari}")
            suptitle = f"Change in 1:{ari} AEP wind speed - {p}"
            scenario = f"{g}_{r}_{p}"
            fname = os.path.join(datapath, scenario, 'hazard', 'hazard_change.nc')
            ds = xr.open_dataset(fname)
            title = f"{g} {rlabels[r]}"
            data = subset(ds.wspd.sel({'ari': ari}), extent)
            lats = ds.lat.sel(lat=slice(extent[3], extent[2])).values
            lons = ds.lon.sel(lon=slice(extent[0], extent[1])).values
            lat, lon = np.meshgrid(lats, lons)
            sdata = smooth(data, int(1/dx))
            cs = ax[i].contourf(lon, lat, sdata.T, levels=levels, extend='both', cmap='RdBu_r')
            ax[i].set_extent(extent)
            ax[i].coastlines(resolution='10m')
            ax[i].add_feature(borders, edgecolor='k', linewidth=0.5)
            gl = ax[i].gridlines(draw_labels=True, linestyle='--')
            gl.top_labels = False
            gl.right_labels = False
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER
            gl.xlabel_style = {'size': 'x-small'}
            gl.ylabel_style = {'size': 'x-small'}
            ax[i].text(0.5, 0.95, title, ha='center', va='center', fontsize='small', transform=ax[i].transAxes, bbox=bbox)
        fig.subplots_adjust(right=0.875, wspace=0.1, hspace=0.05, top=0.95)
        cbar_ax = fig.add_axes([0.9, 0.15, 0.025, 0.7])
        cbarlabel = "Change in AEP wind speed [m/s]"
        fig.colorbar(cs, cax=cbar_ax, label=cbarlabel)
        #plt.tight_layout()
        fig.suptitle(suptitle)
        outputfile = os.path.join(datapath, f'hazard_change.{ari}.{p}.png')
        plt.savefig(outputfile, bbox_inches='tight')
        plt.close(fig)
            
