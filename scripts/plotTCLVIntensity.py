import os
import sys
import logging
from os.path import join as pjoin
from matplotlib import pyplot as plt

import re
import numpy as np
import pandas as pd
import datetime as dt

from datetime import timedelta, datetime

from shapely.geometry import box as sbox
from shapely.geometry import LineString

import scipy.stats as stats

from builtins import str

from git import Repo

import seaborn as sns


r = Repo('')
commit = str(r.commit('HEAD'))

LOGGER = logging.getLogger()
logFormat = "%(asctime)s: %(funcName)s: %(message)s"
logging.basicConfig(level='DEBUG', 
                    format=logFormat,
                    filename='quantileMapping.log', 
                    filemode='w',
                    datefmt="%Y-%m-%d %H:%M:%S")
console = logging.StreamHandler(sys.stdout)
console.setLevel(getattr(logging, 'DEBUG'))
formatter = logging.Formatter(logFormat,
                              datefmt='%H:%M:%S', )
console.setFormatter(formatter)
LOGGER.addHandler(console)
LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
LOGGER.info(f"Code version: f{commit}")

labels = ['TD', 'TC1', 'TC2', 'TC3', 'TC4', 'TC5']

catpal = sns.blend_palette([(0.000, 0.627, 0.235), (0.412, 0.627, 0.235), 
                            (0.663, 0.780, 0.282), (0.957, 0.812, 0.000), 
                            (0.925, 0.643, 0.016), (0.835, 0.314, 0.118),
                            (0.780, 0.086, 0.118)], 6)

def load_track_file(filename):
    """
    Load a TCLV file into a :class:`pandas.DataFrame`, and add a field 
    representing the age of each TCLV in hours, and the pressure difference.
    
    :param str filename: Path to a TCLV data file
    
    :returns: :class:`pandas.DataFrame`
    """
    # This assumes the format of the TCLV files is identical
    columns = ['num', 'year', 'month', 'day', 'hour', 'lon', 'lat',
               'pmin', 'vorticity', 'vmax', 'tanomsum','tanomdiff',
               'pmslanom', 'poci', 'reff','ravg','asym']

    LOGGER.info(f"Loading TCLV data from {filename}")
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

    idx = df.num.values
    varidx = np.ones(len(idx))
    varidx[1:][idx[1:]==idx[:-1]] = 0
    
    dt = (df[dtname] - df[dtname].shift()).fillna(pd.Timedelta(seconds=0)).apply(lambda x: x / np.timedelta64(1,'h')).astype('int64') % (24*60)
    df['vmax'] = maxWindSpeed(varidx, dt.values, df.lon.values, df.lat.values,
                              df.pmin.values, df.poci.values, gustfactor=1.223)
    return df
    
def calculateFitParams(datadict, dist=stats.lognorm):
    """
    Calculate the fit parameters to a given distribution for a dataset. 

    :param datadict: :class:`dict` of `pandas.DataFrame`, with keys of model
    name/scenario
    :param func dist: Distribution function to use.
    This must have `fit`, `pdf`, `cdf` and `ppf` methods defined, as used in
    `scipy.stats.rv_continuous` distributions. Default is `scipy.stats.lognorm`.

    :returns: a `pandas.DataFrame` of the parameters for the fitted
    distribution.

    """

    params = pd.DataFrame(columns=['Model', 'RCP', 'mu', 'sigma', 'zeta'])
    for m, df in datadict.items():
        model, rcp = m.split(' ')
        popt = dist.fit(df.pdiff, loc=0, scale=1)
        params = params.append({'Model':model, 'RCP':rcp,
                                'mu':popt[0], 'sigma':popt[1],
                                'zeta':popt[2]},
                               ignore_index=True)
    return params
