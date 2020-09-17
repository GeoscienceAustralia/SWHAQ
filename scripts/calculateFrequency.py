import os
import sys
import logging
import re
from os.path import join as pjoin
from datetime import datetime
from builtins import str

from matplotlib import pyplot as plt

import numpy as np
import pandas as pd

from shapely.geometry import box as sbox
from shapely.geometry import LineString

import scipy.stats as stats
from git import Repo, InvalidGitRepositoryError
import seaborn as sns

# From TCRM codebase
from Utilities.loadData import maxWindSpeed

try:
    r = Repo('')
    commit = str(r.commit('HEAD'))
except InvalidGitRepositoryError:
    commit = 'unknown'

# Set up logging:
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

LABELS = ['TD', 'TC1', 'TC2', 'TC3', 'TC4', 'TC5']

PALETTE = sns.blend_palette([(0.000, 0.627, 0.235), (0.412, 0.627, 0.235), 
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
               'pmin', 'vorticity', 'vmax', 'tanomsum', 'tanomdiff',
               'pmslanom', 'poci', 'reff', 'ravg', 'asym']

    LOGGER.info(f"Loading TCLV data from {filename}")
    try:
        df = pd.read_csv(filename, delimiter=' ', skipinitialspace=True,
                         names=columns, parse_dates={'datetime': [1, 2, 3, 4]},
                         keep_date_col=True,
                         dtype={'year': int, 'month': int, 'day': int})
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
    filterdf = tempfilter.groupby('num').filter(
        lambda x: LineString(zip(x['lon'], x['lat'])).intersects(domain))
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
    varidx[1:][idx[1:] == idx[:-1]] = 0

    dt = (df[dtname] - df[dtname].shift()).fillna(pd.Timedelta(seconds=0)
                                                  ).apply(lambda x: x / np.timedelta64(1, 'h')).astype('int64') % (24*60)
    df['vmax'] = maxWindSpeed(varidx, dt.values, df.lon.values, df.lat.values,
                              df.pmin.values, df.poci.values, gustfactor=1.223)
    return df

def loadTCLVdata(dataPath, start_year=None, end_year=None, domain=None):
    """ 
    Load TCLV data from a directory, for a given year range 
    and a geographic domain

    :param str dataPath: Path to the directory that contains the TCLV track
    files
    :param int start_year: beginning of the time period (year)
    :param int end_year: end of the time period (year)
    :param tuple domain: Tuple of (min(lon), max(lon), min(lat), max(lat)) that
    describes the bounding domain.

    """

    if not os.path.isdir(dataPath):
        LOGGER.error(f"{dataPath} is not a valid directory")
        raise OSError(f"{dataPath} is not a valid directory")

    if start_year is not None or end_year is not None:
        if start_year is None or end_year is None:
            raise ValueError(
                "must supply both start year and end year or none")
        if start_year > end_year:
            raise ValueError(
                f"Start year {start_year} is greater than end year {end_year}")

    datadict = {}
    regex = r'all_tracks_(.+)_(rcp\d+)\.dat'
    for fname in os.listdir(dataPath):
        # Skip the ERA-Interim sourced TCLV set
        if fname == "all_tracks_ERAIntQ_rcp85.dat":
            continue

        if re.search(regex, fname):
            m = re.match(regex, fname)
            model, rcp = m.group(1, 2)
            filename = pjoin(dataPath, fname)
            df = load_track_file(filename)

            if start_year is not None:
                df = filter_tracks(df, start_year, end_year)
            if domain is not None:
                df = filter_tracks_domain(df, *domain)
            label = f"{model} {rcp.upper()}"
            datadict[label] = df
        else:
            LOGGER.debug(
                f"{fname} does not match the expected pattern. Skipping...")
            continue

    return datadict

def load_obs_data(obsfile, domain):
    """
    Load observational data. 

    Assumes that the data is an IBTrACS v04 file

    :param str obsfile: Path to the data file
    :param tuple domain: Tuple containing min/max lon/lat values
    """

    if not os.path.isfile(obsfile):
        LOGGER.error(f"{obsfile} does not exist")
        sys.exit()

    LOGGER.info(f"Loading observed TC tracks from {obsfile}")
    best = pd.read_csv(obsfile, skiprows=[1],
                       usecols=[0, 6, 8, 9, 11, 95, 113],
                       na_values=[' '],
                       parse_dates=[1])
    best.rename(columns={'SID': 'num', 'LAT': 'lat', 'LON': 'lon',
                         'WMO_PRES': 'pmin', 'BOM_WIND': 'vmax',
                         'BOM_POCI': 'poci'}, inplace=True)
    best = best[best.poci.notnull() & best.pmin.notnull()]
    best['pdiff'] = best.poci - best.pmin
    best = best[best.pdiff > 1]
    obstc = filter_tracks_domain(best, *domain)
    return obstc


if __name__ == '__main__':

    path = "data/tclv/"
    regex = r'all_tracks_(.+)_(rcp\d+)\.dat'
    domain = (135, 160, -25, -10)
    obstc = load_obs_data("data/ibtracs.since1980.list.v04r00.csv", domain)
    obstc = calculateMaxWind(obstc, 'ISO_TIME')
    tclvdata = loadTCLVdata(path, domain=domain)
    #futdata = loadTCLVdata(path, 1981, 2100, domain)
    #refparams = calculateFitParams(refdata)
    obsdata = obstc.pdiff.values[obstc.pdiff.values > 0]
    obsfreq = obsdata.groupby('num').ngroups / 40
    STARTS = [2021, 2041, 2061, 2081]
    ENDS = [2040, 2060, 2080, 2100]

    freqdf = pd.DataFrame(columns=['Model', 'RCP', 'start_year', 'plot_year', 'end_year', 'frequency'])
    #freqdf = freqdf.append({'Model':"IBTrACS", 'RCP':'', 'start_year':1980, 'end_year':2019, 'frequency':obsfreq}, ignore_index=True)
    for i, (m, df) in enumerate(tclvdata.items()):
        LOGGER.info(f"Processing {m}")
        model, rcp = m.split()
        refdf = filter_tracks(df, 1981, 2010)
        reffreq = refdf.groupby('num').ngroups / 30
        freqdf = freqdf.append({'Model':model, 'RCP':rcp, 'start_year':1981, 'plot_year':1995, 'end_year':2010, 'frequency':reffreq}, ignore_index=True)
        for s, e in zip(STARTS, ENDS):
            LOGGER.info(f"Processing time period {s} - {e}")
            futdf = filter_tracks(df, s, e)
            futfreq = futdf.groupby('num').ngroups / 20
            freqdf = freqdf.append({'Model':model, 'RCP':rcp, 'start_year':s, 'plot_year':s+9, 'end_year':e, 'frequency':futfreq}, ignore_index=True)
    
    g = sns.FacetGrid(freqdf, col='RCP', hue='Model',
                      height=5, aspect=1.25, legelnd_out=True)
    g.map(sns.lineplot, "plot_year", "frequency")
    for  cv, ax in g.axes_dict.items():
        ax.axhline(obsfreq, color='0.5', linestyle='--')
        ax.set_title(cv)
        ax.set_xlabel("Year")
        ax.set_xticks([1995, 2030, 2050, 2070, 2090])