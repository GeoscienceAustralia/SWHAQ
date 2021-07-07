"""
As a demonstration of the scaling process in practice, here we display the
individual $\Delta p_c$ values for the reference and projection, as well as
the observed $\Delta p_c$ values. On each, we add a line at the 99th
percentile for each collection of data. The relative change in the $Q(0.99)$
between the reference period and the future period is 2.1. 

"""

import os
import sys
import logging
from os.path import join as pjoin
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches

import re
import numpy as np
import pandas as pd
import seaborn as sns
import datetime as dt

import cartopy.crs as ccrs
import cartopy.feature as feature
import statsmodels.api as sm
from datetime import timedelta, datetime

import shapely.geometry as sg
from shapely.geometry import box as sbox
from shapely.geometry import LineString

from scipy.optimize import curve_fit
import scipy.stats as stats

from qdm import qdm

# From TCRM codebase
from Utilities.loadData import maxWindSpeed

from builtins import str
sns.set_style('whitegrid')
sns.set_context("talk")

from git import Repo, InvalidGitRepositoryError

try:
    r = Repo('', search_parent_directories=True)
    commit = str(r.commit('HEAD'))
except InvalidGitRepositoryError:
    commit = 'unknown'

LOGGER = logging.getLogger()
logFormat = "%(asctime)s: %(funcName)s: %(message)s"
logging.basicConfig(level='INFO', 
                    format=logFormat,
                    filename='quantileMapping.log', 
                    filemode='w',
                    datefmt="%Y-%m-%d %H:%M:%S")
console = logging.StreamHandler(sys.stdout)
console.setLevel(getattr(logging, 'INFO'))
formatter = logging.Formatter(logFormat,
                              datefmt='%H:%M:%S', )
console.setFormatter(formatter)
LOGGER.addHandler(console)
LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
LOGGER.info(f"Code version: {commit}")

def load_track_file(filename):
    """
    Load a TCLV file into a :class:`pandas.DataFrame`, and add a field 
    representing the age of each TCLV in hours, and the pressure difference.
    
    :param str filename: Path to a TCLV data file
    
    :returns: :class:`pandas.DataFrame`
    """
    # This assumes the format of the TCLV files is identical
    LOGGER.info(f"Loading TCLV data from {filename}")
    columns = ['num', 'year', 'month', 'day', 'hour', 'lon', 'lat',
               'pmin', 'vorticity', 'vmax', 'tanomsum','tanomdiff',
               'pmslanom', 'poci', 'reff','ravg','asym']
    try:
        df = pd.read_csv(filename, delimiter=' ', skipinitialspace=True,
                         names=columns, parse_dates={'datetime':[1,2,3,4]},
                         keep_date_col=True, 
                         dtype={'year':int, 'month':int, 'day':int})
    except:
        LOGGER.exception(f"Failed to load {filename}")
        raise
    df['dt'] = df.groupby('num')['datetime'].apply(lambda x: x.diff())
    df['dt'] = df['dt'].transform(lambda x: x.total_seconds())

    df['age'] = df.groupby('num')['dt'].apply(np.cumsum).fillna(0)/3600.
    # Throw in the pressure deficit for good measure:
    df['pdiff'] = df['poci'] - df['pmin']

    # And normalised intensity. This is the intensity at any given time,
    # dividied by the lifetime maximum intensity for each unique event
    df['ni'] = df.pdiff / df.groupby('num').pdiff.transform(np.max)
    return df

def filter_tracks(df, start_year=1980, end_year=2010, zeta=0, age=36):
    """
    Takes a `DataFrame` and filters on the basis of a prescribed vorticity 
    threshold, lifetime and a given time period.
    
    :param df: :class:`pandas.DataFrame` that holds the TCLV data
    :param int start_year: Starting year of the time period to filter
    :param int end_year: End year of the period to filter
    :param float zeta: Vorticity threshold to filter the TCLV data. 
                       This can be a positive value, as we filter on the
                       absolute value of the field.
    :param int age: Minimum age of the TCLVs in hours
    
    """
    tracks = df.groupby('num')
    filterdf = tracks.filter(lambda x: (x['datetime'].dt.year.min() >= start_year) &
                             (x['datetime'].dt.year.max() <= end_year) &
                             (x['age'].max() >= age) &
                             (np.abs(x['vorticity'].min()) > zeta))
    return filterdf

def filter_tracks_domain(df, minlon=90, maxlon=180, minlat=-40, maxlat=0):
    """
    Takes a `DataFrame` and filters on the basis of whether the track interscts
    the given domain, which is specified by the minimum and maximum longitude and 
    latitude.
    
    NOTE: This assumes the tracks and bounding box are in the same geographic 
    coordinate system (i.e. generally a latitude-longitude coordinate system). 
    It will NOT support different projections (e.g. UTM data for the bounds and
    geographic for the tracks).
    
    NOTE: This doesn't work if there is only one point for the track. 
    
    :param df: :class:`pandas.DataFrame` that holds the TCLV data
    :param float minlon: minimum longitude of the bounding box
    :param float minlat: minimum latitude of the bounding box
    :param float maxlon: maximum longitude of the bounding box
    :param float maxlat: maximum latitude of the bounding box
    """

    domain = sbox(minlon, minlat, maxlon, maxlat, ccw=False)
    tracks = df.groupby('num')
    tempfilter = tracks.filter(lambda x: len(x) > 1)
    filterdf = tempfilter.groupby('num').filter(lambda x: LineString(zip(x['lon'], x['lat'])).intersects(domain))
    return filterdf

def calculateMaxWind(df, dtname='ISO_TIME'):
    """
    Calculate a maximum gust wind speed based on the central pressure deficit and the 
    wind-pressure relation defined in Holland (2008). This uses the function defined in 
    the TCRM code base, and simply passes the correct variables from the data frame
    to the function
    
    This returns a `DataFrame` with an additional column (`vmax`), which represents an estimated
    0.2 second maximum gust wind speed.
    """
    LOGGER.debug("Calculating maximum wind speed")
    idx = df.num.values
    varidx = np.ones(len(idx))
    varidx[1:][idx[1:]==idx[:-1]] = 0
    
    dt = (df[dtname] - df[dtname].shift()).fillna(pd.Timedelta(seconds=0)).apply(lambda x: x / np.timedelta64(1,'h')).astype('int64') % (24*60)
    df['vmax'] = maxWindSpeed(varidx, dt.values, df.lon.values, df.lat.values,
                              df.pmin.values, df.poci.values, gustfactor=1.223)
    return df

def loadTCLVdata(dataPath, model, start_year, end_year, domain):
    """ 
    Load TCLV data from a directory, for a given year range 
    and a geographic domain

    :param str dataPath: Path to the directory that contains the TCLV track
    files
    :param int start_year: beginning of the time period (year)
    :param int end_year: end of the time period (year)

    NOTE:: This function is modified from the similarly named function in
    `quantileMapping.py`. This version returns a dataframe containing all track
    data for a single model.
    """
    m, rcp = model.split(' ')
    filename = pjoin(dataPath, f"all_tracks_{m}_{rcp.lower()}.dat")
    LOGGER.info(f"Loading data from {filename}")
    df = load_track_file(filename)
    df = filter_tracks(df, start_year, end_year)
    df = filter_tracks_domain(df, *domain)
    return df

def loadObsData(obsfile, domain):
    """
    Load observational data. 

    Assumes that the data is an IBTrACS v04 file

    :param str obsfile: Path to the data file
    :param tuple domain: Tuple containing min/max lon/lat values
    """
    LOGGER.info(f"Loading obsered TC data from {obsfile}")
    best = pd.read_csv(obsfile, skiprows=[1],
                       usecols=[0,6,8,9,11,95,113],
                       na_values=[' '],
                       parse_dates=[1])
    best.rename(columns={'SID':'num', 'LAT': 'lat', 'LON':'lon',
                        'WMO_PRES':'pmin', 'BOM_WIND':'vmax',
                        'BOM_POCI':'poci'}, inplace=True)
    best = best[best.poci.notnull() & best.pmin.notnull()]
    best['pdiff'] = best.poci - best.pmin
    best = best[best.pdiff > 1]
    obstc = filter_tracks_domain(best, *domain)
    return obstc

path = "../data/tclv/"
plotpath = "../figures/20210210"
regex = r'all_tracks_(.+)_(rcp\d+)\.dat'

model = 'CNRM-CM5Q RCP85'

dist = stats.lognorm
binvals = np.arange(0, 100, 5)
params = pd.DataFrame(columns=['Model', 'RCP', 'period',
    'bc', 'mu', 'sigma', 'zeta'].append(binvals.tolist()))

LOGGER.info("Processing observations...")
domain = (135, 160, -25, -10)
bins = np.arange(0, 100, 5)
obstc = loadObsData("../data/ibtracs.since1980.list.v04r00.csv", domain)
obslmi = obstc.loc[obstc.groupby(["num"])["pdiff"].idxmax()]
h, b = np.histogram(obslmi.pdiff, bins=bins, density=True)
histdict = {b:h for b, h in zip(b, h)}
obsparams = stats.lognorm.fit(obslmi.pdiff, loc=0, scale=1)
params = params.append({"Model": "Obs", "RCP": "Obs", 
                        'period': '1981-2019', 'bc': False,
                        "mu": obsparams[0], "sigma": obsparams[1],
                        "zeta": obsparams[2], **histdict},
                        ignore_index=True)

LOGGER.info("Processing the reference period 1981 - 2010")
refdf = loadTCLVdata(path, model, 1981, 2019, domain)
futdf = loadTCLVdata(path, model, 2081, 2100, domain)

# Pull out the LMI
srefdata = refdf.loc[refdf.groupby('num')["pdiff"].idxmax()].set_index(['num'])
sfutdata = futdf.loc[futdf.groupby('num')["pdiff"].idxmax()].set_index(['num'])

refq099 = np.quantile(srefdata.pdiff, 0.99)
futq099 = np.quantile(sfutdata.pdiff, 0.99)
obsq099 = np.quantile(obslmi.pdiff, 0.99)
delta = futq099/refq099

obsdata = obslmi.pdiff.values[obslmi.pdiff.values > 0]

# Apply the QDM to derive corrected LMI values
brefpdiff = qdm(obsdata, srefdata.pdiff.values, srefdata.pdiff.values)[1]
bfutpdiff = qdm(obsdata, refdf.pdiff.values, sfutdata.pdiff.values)[1]

fig, ax = plt.subplots(1, 2, figsize=(16, 8), sharey=True)
ax[0].scatter(srefdata.datetime, srefdata.pdiff, s=1, c='r')
ax[0].scatter(sfutdata.datetime, sfutdata.pdiff, s=1, c='r')
ax[0].set_xlim(datetime(1981, 1, 1), datetime(2100, 1, 1))
ax[0].axhline(refq099, xmin=0, xmax=0.833333, linestyle='--', color='0.5')
ax[0].axhline(refq099, xmin=0, xmax=0.25, linestyle='--', color='k')
ax[0].axhline(futq099, xmin=0.83333, xmax=1, linestyle='--', color='k')
ax[1].scatter(obslmi.ISO_TIME, obslmi.pdiff, s=1, c='b', label='Observations')
ax[1].scatter(srefdata.datetime, brefpdiff, s=1, c='r', label='Simulated')
ax[1].scatter(sfutdata.datetime, bfutpdiff, s=1, c='r')
ax[1].axhline(obsq099, xmin=0, xmax=0.83333, linestyle='--', color='0.5')
ax[1].axhline(obsq099, xmin=0, xmax=0.3333, linestyle='--', color='k')
ax[1].axhline(obsq099*delta, xmin = 0.83333, xmax=1, linestyle='--', color='k')
ax[1].set_xlim(datetime(1981, 1, 1), datetime(2100, 1, 1))
ax[1].legend(loc=2)
ax[0].set_ylabel(r"$\Delta p_c$ [hPa]")
ax[0].set_xlabel("Year")
ax[1].set_xlabel("Year")
ax[0].set_title('Raw')
ax[1].set_title('Corrected')

styles = mpatches.ArrowStyle.get_styles()
def to_texstring(s):
    s = s.replace("<", r"$<$")
    s = s.replace(">", r"$>$")
    s = s.replace("|", r"$|$")
    return s

x = datetime(2080, 1, 1)
y = 0.4 * (refq099 + futq099)
tx = datetime(2060, 1, 1)
ty = 0.4 * (refq099 + futq099)
stylename = '-['
ax[0].annotate(r'$\delta_{fut}$' + ' = {0:.2f}'.format(delta), (x, y),
                (tx, ty), xycoords='data',
                ha="right", va="center",
                size=1.4,
                arrowprops=dict(arrowstyle=stylename,
                                fc="b", ec="b",
                                connectionstyle="arc3,rad=-0.05",
                                ),
                fontsize='x-small', color='b',
                bbox=dict(boxstyle="square", fc="w", alpha=0.5))

ax[0].annotate(r"$Q_{ref}(0.99)$" + " = {0:.1f}".format(refq099), 
            (datetime(1995, 1, 1), refq099),
            (datetime(2000, 1, 1), 3*refq099),
            ha="center", va="center", size=1.4,
            arrowprops=dict(arrowstyle='->',
                                fc="b", ec="b", shrinkB=1.5,
                                connectionstyle="arc3,rad=-0.0",
                                ),
            fontsize='x-small', color='b',
            bbox=dict(boxstyle="square", fc="w", alpha=0.5))

ax[0].annotate(r"$Q_{fut}(0.99)$" + " = {0:.1f}".format(futq099), 
            (datetime(2090, 1, 1), futq099),
            (datetime(2080, 1, 1), 2*futq099),
            ha="center", va="center", size=1.4,
            arrowprops=dict(arrowstyle='->',
                                fc="b", ec="b", shrinkB=1.5,
                                connectionstyle="arc3,rad=-0.0",
                                ),
            fontsize='x-small', color='b',
            bbox=dict(boxstyle="square", fc="w", alpha=0.5))

ax[1].annotate(r"$Q_{obs}(0.99)$" + " = {0:.1f}".format(obsq099),
            (datetime(1995, 1, 1), obsq099),
            (datetime(1995, 1, 1), 1.5*obsq099), 
            ha="center", va='center', size=1.4,
            arrowprops=dict(arrowstyle="->",
                            fc='b', ec='b', shrinkB=1.5,
                            connectionstyle='arc3,rad=-0.05'),
            fontsize='x-small', color='b',
            bbox=dict(boxstyle="square", fc="w", alpha=0.5))

ax[1].annotate(r"$Q_{futb}(0.99)$" + " = {0:.1f}".format(obsq099 * delta),
            (datetime(2090, 1, 1), obsq099 * delta),
            (datetime(2060, 1, 1), 1.5*obsq099), 
            ha="center", va='center', size=1.4,
            arrowprops=dict(arrowstyle="->",
                            fc='b', ec='b', shrinkB=1.5,
                            connectionstyle='arc3,rad=0.5'),
            fontsize='x-small', color='b',
            bbox=dict(boxstyle="square", fc="w", alpha=0.5))

plt.savefig(pjoin(plotpath, f'illustration_qdm.{model.replace(" ", "_")}.png'), bbox_inches='tight')
None

# Just print the values for a visual check
print(f"Reference quantile: {refq099:.2f}" )
print(f"Projected quantile: {futq099:.2f}" )
print(f"Observed quantile: {obsq099:.2f}")
print(f"Bias corrected projection quantile: {obsq099*delta:.2f}")
print(f"Ratio of observed to reference quantiles: {obsq099 / refq099:.2f}")