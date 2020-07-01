#!/usr/bin/env python
# coding: utf-8

"""
:mod: `TCLVscaling` -- Quantile delta mapping of TCLV intensity
===================================================================

.. module:: TCLVscaling
    :synopsis: Use quantile delta mapping to scale intensity of TCLVs to
    observed distribution of intensity. 

.. moduleauthor:: Craig Arthur, <craig.arthur@ga.gov.au

We work with the central pressure deficit $\Delta p_c = p_{oci} - p_{c}$, where
$p_{oci}$ is the pressure of the outermost closed isobar (sometimes also
referred to as environmental pressure $p_{env}$) and $p_c$ is the minimum
central pressure. We use $\Delta p_c$, as this is the variable used in TCRM to
model intensity. $p_c$ is also more widely recorded in the Australian region,
for reasons that I'll not go into here. 

Irrespective of the variable chosen, regionally downscaled climate models, even
at 10 km grid spacing, do not sufficiently resolve the dynamics that drive TC
intensity. To accurately simulate maximum intensity (represented by surface wind
speed) arguably requires a convection-allowing model, which usually entails grid
spacings less than 2 km (e.g. Gentry and Lackmann, 2010; Walsh _et al_., 2013).
Such modelling efforts are beyond the scope of this project, so we rely on
scaling the intensity to address the issue.

We use a quantile mapping approach to adjust the $\Delta p_c$ of the TCLVs
extracted for future climate projections which does not _a priori_ assume a
stationary relationship in the scaling function (as we have previously done, for
example, in Arthur and Woolf, 2015). Cannon _et al._ (2015) describe a method
for bias correction of climate variables that conserves relative changes in
quantiles between current and future climate regimes. Called Quantile Delta
Mapping (QDM), the method ensures that climate sensitivity of the underlying
climate model remains unaffected by the correction process. The concepts
described in Cannon _et al._ have been applied to a range of other climate
variables - e.g. Bhatia _et al._ (2019) have applied QDM to intensity changes of
simulated TCs in high-resolution simulations.

Changes in frequency and track behavoiur - both key factors in understanding
likelihood of extreme winds - are drawn directly from the TCLV data and are
examined in a separate notebook.
"""
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

from qdm import qdm

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

# This section defines a number of functions that are used to load and filter
# the track data generated by the regional downscaling simulations.
#
# Filters are applied to eliminate spurious tracks that have a short lifetime.
# These spurious tracks are picked up by the detection and tracking method, but
# are not persisted for a sufficient time period (36 hours), which leads to an
# anomolous occurence of TCLVs around the Solomon Islands in some of the model
# output.
#
# A spatial filter is used to select only those tracks that pass through the
# study region - in this case Queensland and the Coral Sea. The regional
# downscaling was focused over the Queensland region (using a cubic-conformal
# grid configuration), so the marginal regions are unlikely to resolve the
# dynamics of the inner core of TCLVs. As the grid spacing of the computational
# grid increases, the fine scale features that control intensity of TCLVs will
# not be as well resolved, which will affect the distribution of intensity in
# simulated events.


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


def pyqdm(vobs, vref, vfut, dist=stats.lognorm):
    """
    Calculate the quantile delta mapping for a collection of simulated data. 

    This function is based on the formulation described in Cannon _et al._
    (2015) and Heo _et al._ (2019), where the relative change in quantiles 
    between a reference period and the future period are preserved.

    $\delta_{fut} = \dfrac{Q_{fut}}{F_{ref}^{-1}\left[ F_{fut} ( Q_{fut} ) \right]} $ 

    $Q_{futb} = F_{obs}^{-1} \left[ F_{fut} (Q_{fut}) \right] \times \delta_{fut} $

    $\delta_{fut}$ is the relative change in the quantiles between the simulated
    reference data ('sreftclv') and the simulated future data ('sfuttclv').
    $Q_{fut}$ is the quantile of the simulated future data. $F_{fut}$ and
    $F_{ref}^{-1}$ are a CDF of the simulated future data and an inverse CDF of
    the simulated reference data respectively. Finally, $F_{obs}^{-1}$ is the
    inverse CDF of the observed data, and $Q_{futb}$ are the corrected quantiles
    of the future data.

    In this framework, the algorithm is independent of the selection of
    distribution, which would be data-dependent, and more generally specific to
    the variable that is being corrected. We begin by fitting a lognormal
    distribution to the $\Delta p_c$ values in each of the observed, reference and
    future collections. 

    :param vobs: `numpy.array` of observed values 
    :param vref: `numpy.array` of reference period values (simulated) 
    :param vfut: `numpy.array` of future period values (simulated) 
    :param func dist: Distribution function to use.
    This must have `fit`, `pdf`, `cdf` and `ppf` methods defined, as used in
    `scipy.stats.rv_continuous` distributions. Default is `scipy.stats.lognorm`.

    :returns: `vfutb` a `numpy.array` of bias corrected future values. 
    """

    if not isinstance(vobs, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for observed values")
    if not isinstance(vref, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for reference period values")
    if not isinstance(vfut, (list, np.ndarray,)):
        raise TypeError("Incorrect input type for future period values")

    if any(np.isnan(vobs)):
        raise ValueError("Input observation array contains NaN values")
    if any(np.isnan(vref)):
        raise ValueError("Input reference array contains NaN values")
    if any(np.isnan(vfut)):
        raise ValueError("Input future array contains NaN values")

    pobs = dist.fit(vobs, loc=0, scale=1)
    pref = dist.fit(vref, loc=0, scale=1)
    pfut = dist.fit(vfut, loc=0, scale=1)

    # CDF of future, at the value of the future data points
    Fsf = dist.cdf(vfut, *pfut)

    # Inverse cdf of reference period distribution, evaluated at future CDF
    # values
    invFsr = dist.ppf(Fsf, *pref)

    # Relative change in values
    delta = vfut / invFsr
    vfutb = dist.ppf(Fsf, *pobs) * delta

    return vfutb


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


def append_ensembles(datadict):
    """
    Collect models together to create ensembles based on the RCP

    :param dict datadict: collection of `pandas.DataFrames` that hold
        the individual model data. Keys are "<model> <rcp>".

    :returns: An updated `datadict` with additional collections for the
        two RCPs (RCP 4.5 and RCP 8.5)  
    """
    # make a copy
    datadict = dict(datadict)
    ens45 = []
    ens85 = []

    for key, df in datadict.items():
        model, rcp = key.split()
        if rcp.upper() == 'RCP45':
            ens45.append(df)
        else:
            ens85.append(df)

    datadict['ENS RCP45'] = pd.concat(ens45, ignore_index=True)
    datadict['ENS RCP85'] = pd.concat(ens85, ignore_index=True)

    return datadict


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
        params = params.append({'Model': model, 'RCP': rcp,
                                'mu': popt[0], 'sigma': popt[1],
                                'zeta': popt[2]},
                               ignore_index=True)
    return params


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


def plot_categories(datadict, start, end, plotpath):
    fig, axes = plt.subplots(6, 4, figsize=(20, 20), sharex=True, sharey=True)
    ax = axes.flatten()

    for i, (m, df) in enumerate(datadict.items()):
        df['category'] = pd.cut(df['vmax'],
                                [0, 25, 35, 46, 62, 77, 200],
                                labels=LABELS)
        x = df['category'].value_counts()/len(df)
        ax[i].bar(LABELS, x, color=PALETTE)
        ax[i].set_title("{0}".format(m))
        ax[i].set_xlabel('')

    fig.suptitle('{0}-{1}'.format(start, end), size=20)
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
    plt.savefig(
        pjoin(plotpath, f"categories_{start}-{end}.png"), bbox_inches='tight')


if __name__ == '__main__':

    path = "data/tclv/"
    regex = r'all_tracks_(.+)_(rcp\d+)\.dat'

    # The variables are referenced in the following way::
    #
    # * `s` = simulated
    # * `ref` = reference time period (1981-2010)
    # * `fut` = future time period (2021-2040, 2041-2060, 2061-2080 or 2081-2100)
    # * `obstc` = observed TC events (using IBTrACS, 1981-2010)
    # * `b` = bias-corrected
    #
    # Firstly load the IBTrACS data and extract the relevant tracks for the region
    # of interest. We retain only those tracks that have a vaild $\Delta p$ value
    # and enter the simulation domain.

    domain = (135, 160, -25, -10)
    obstc = load_obs_data("data/ibtracs.since1980.list.v04r00.csv", domain)
    obstc = calculateMaxWind(obstc, 'ISO_TIME')
    obstc['category'] = pd.cut(obstc['vmax'], 
                               [0, 25, 35, 46, 62, 77, 200], 
                               labels=LABELS)
    obsparams = stats.lognorm.fit(obstc.pdiff, loc=0, scale=1)

    # First we explore the distribution of $\Delta p_c$ for the reference period
    # (1981-2010) in each of the models, and the best track archive. The figure
    # below shows the histogram of $\Delta p_c$, with a fitted lognormal
    # distribution to each.

    tclvdata = loadTCLVdata(path, domain=domain)
    #futdata = loadTCLVdata(path, 1981, 2100, domain)
    #refparams = calculateFitParams(refdata)
    obsdata = obstc.pdiff.values[obstc.pdiff.values > 0]

    obslmi = obstc.loc[obstc.groupby(["num"])["pdiff"].idxmax()]

    OUTPUTPATH = "C:/WorkSpace/data/tclv/tracks/corrected/20200622"
    FILETEMPLATE = "{0}_1981-2010_bc.csv"
    FUTFILETEMPLATE = "{0}_{1}-{2}_bc.csv"

    STARTS = [2021, 2041, 2061, 2081]
    ENDS = [2040, 2060, 2080, 2100]

    for s, e in zip(STARTS, ENDS):
        LOGGER.info(f"Processing time period {s} - {e}")
        #futdata = loadTCLVdata(path, s, e, domain)
        bfutdata = {}
        brefdata = {}
        for i, (m, df) in enumerate(tclvdata.items()):
            LOGGER.info(f"Processing {m}")
            refdf = filter_tracks(df, 1981, 2010)
            futdf = filter_tracks(df, s, e)

            # Determine LMI for each event in the reference and projected data
            try:
                srefdata = refdf.loc[refdf.groupby(
                    'num')["pdiff"].idxmax()].set_index(['num'])
                sfutdata = futdf.loc[futdf.groupby(
                    'num')["pdiff"].idxmax()].set_index(['num'])
            except:
                LOGGER.error(
                    f"Reference data: {refdf.groupby('num')['pdiff'].idxmax():.2f}")
                LOGGER.error(
                    f"Projected data: {futdf.groupby('num')['pdiff'].idxmax():.2f}")
            # Calculate the bias-corrected LMI
            try:
                srefdata['blmi'], sfutdata['blmi'] = qdm(
                    obsdata, srefdata.pdiff.values, sfutdata.pdiff.values)
            except:
                LOGGER.error(f"QDM failed for {m}")
                raise
            LOGGER.debug(
                f"Mean bias-corrected projected LMI: {sfutdata['blmi'].mean():.2f}")
            LOGGER.debug(
                f"Mean bias-corrected reference LMI: {srefdata['blmi'].mean():.2f}")

            # Now to join the bias-corrected LMI to the existing normalised
            # intensity to give bias-corrected pressure deficit values
            futdf.set_index('num')
            newdf = pd.merge(futdf, sfutdata['blmi'], on='num')
            futdf['pdiff'] = futdf.ni.values * newdf.blmi.values
            futdf['pmin'] = futdf['poci'] - futdf['pdiff']
            LOGGER.debug(
                f"Mean bias-corrected future pressure deficit: {futdf['pdiff'].mean():.2f}")
            # Calculate maximum wind speed (this will replace existing values)
            futdf = calculateMaxWind(futdf, 'datetime')
            # Save to file
            fname = pjoin(OUTPUTPATH, FUTFILETEMPLATE.format(
                m.replace(' ', '_'), s, e))
            futdf.to_csv(fname, sep=',',  float_format="%.3f", index=False)

            # Finished processing all the
            refdf.set_index('num')
            newdf = pd.merge(refdf, srefdata[['blmi']], on='num')
            refdf['pdiff'] = refdf.ni.values * newdf.blmi.values
            refdf['pmin'] = refdf['poci'] - refdf['pdiff']
            refdf = calculateMaxWind(refdf, 'datetime')
            fname = pjoin(OUTPUTPATH, FILETEMPLATE.format(m.replace(' ', '_')))
            refdf.to_csv(fname, sep=',',  float_format="%.3f", index=False)

    #plotCategories(refdata, 1980, 2010, path)
    #plotCategories(futdata, start, end, path)
