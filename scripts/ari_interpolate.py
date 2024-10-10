import os
import sys
import pandas as pd
import numpy as np
import sys
import geopandas as gpd
import rioxarray
import xarray as xr
import time
from datetime import datetime
from pyproj import CRS
from git import Repo

from scipy.interpolate import interp1d
from pykrige import OrdinaryKriging

import hazard

IN_DIR = os.path.expanduser('/g/data/w85/QFES_SWHA/hazard/input')
OUT_DIR = os.path.expanduser('/g/data/w85/QFES_SWHA/hazard/output')
repo = Repo(path='', search_parent_directories=True)

commit = repo.commit()
AUTHOR = commit.author.name
COMMITDATE = time.strftime("%Y-%m-%d %H:%M:%S",
                           time.gmtime(commit.committed_date))
URL = list(repo.remotes[0].urls)[0]
now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
history_msg = f"{now}: {(' ').join(sys.argv)}"
comment = ("This research was undertaken with the assistance of "
           "resources from the National Computational Infrastructure "
           "(NCI Australia), an NCRIS enabled capability supported by "
           "the Australian Government. Funding for the project was "
           "provided by the Commonwealth Government of Australia and "
           "Queensland Government through the Queensland Resilience and "
           "Risk Reduction Fund")

# Global attributes:
gatts = {"title": "Combined regional wind hazard data",
         "institution": "Geoscience Australia",
         "repository": URL,
         "author": AUTHOR,
         "commit_date": COMMITDATE,
         "commit": commit.hexsha,
         "history": history_msg,
         "comment": comment,
         "references": "http://pid.geoscience.gov.au/dataset/ga/147446",
         "created_on": now}


def gdp_recurrence_intervals(return_levels, mu, shape, scale,
                             rate, npyr=365.25):
    """
    Calculate recurrence intervals for specified return levels for a
    distribution with the given threshold, scale and shape parameters.

    :param intervals: :class:`numpy.ndarray` or float of return levels
              to evaluate recurrence intervals for.
    :param float mu: Threshold parameter (also called location).
    :param float shape: Shape parameter.
    :param float scale: Scale parameter.
    :param float rate: Rate of exceedances (i.e. number of observations greater
                       than `mu`, divided by total number of observations).
    :param float npyr: Number of observations per year.

    :returns: recurrence intervals for the specified return levels.

    """

    ri = np.power((return_levels - mu) * (shape / scale) + 1,
                  1 / shape) / (npyr * rate)
    if not np.isscalar(ri):
        ri[np.isnan(ri)] = np.inf
    elif np.isnan(ri):
        ri = np.inf
    return ri


def interpgrid(data, windspeeds, aeps):
    """
    Interpolate wind speeds to defined AEPs. We treat the exceedance
    probabilities as the

    :param data: :class:`np.ndarray` of the combined AEP at defined wind speeds
        across the domain.
    :param windspeeds: :class:`np.array` of the wind speeds. Must be the same
        length as data.shape[-1]
    :param aeps: :class:`np.array` containing the target exceedance
        probabilities

    :returns: :class:`np.ndarray` of the wind speeds at the defined AEPs over
        the grid

    """
    nx, ny = data.shape[:-1]
    out = np.zeros((nx, ny, len(aeps)))

    for x in range(nx):
        for y in range(ny):
            f = interp1d(data[x, y, :], windspeeds, bounds_error=False,
                         fill_value="extrapolate")
            out[x, y, :] = f(aeps)
    return out


if __name__ == "__main__":

    # load in a process synoptic and TS ARI data - provided by UQ (Matt Mason)
    fp = os.path.join(IN_DIR, "AllStationsSuperStation_20220622.xlsx")
    df = pd.read_excel(fp, skiprows=1).iloc[9:]

    df["aep"] = 1 - np.exp(-1 / df["ARI [yrs]"])
    windspeeds = np.linspace(20, 100, 101)
    syn_aep = np.interp(windspeeds, df.Synoptic.values, df.aep.values)
    syn_aep[windspeeds > df.Synoptic.max()] = 0.0
    ts_aep = np.interp(windspeeds, df.Thunderstorm.values, df.aep.values)
    ts_aep[windspeeds > df.Thunderstorm.max()] = 0.0

    # load TC ARI curves for stations:
    stnlist = gpd.read_file(os.path.join(
        IN_DIR, "stations", "SEQ_station_list.shp"))
    tc_df = pd.read_csv(os.path.join(
        IN_DIR, "tc_ari_params_", "parameters.csv"))

    tc_df.columns = [c.strip() for c in tc_df.columns]
    tc_df['longitude'] = stnlist.loc[tc_df.locId.values - 1].Longitude.values
    tc_df['latitude'] = stnlist.loc[tc_df.locId.values - 1].Latitude.values

    tc_df.locName = tc_df.locName.str.strip()
    tc_df.drop_duplicates(inplace=True)
    tc_df.set_index('locName', drop=False, inplace=True)

    shape, scale, rate, mu = tc_df.iloc[0][
        ['gpd_shape', 'gpd_scale', 'gpd_rate', 'gpd_thresh']].values

    # spatially interpolate TC ARI curves
    params = []
    for i in range(len(tc_df)):
        shape, scale, rate, mu = tc_df.iloc[i][
            ['it_shape', 'it_scale', 'it_rate', 'it_thresh']].values
        params.append([shape, scale, rate, mu])
    params = np.array(params)
    # SEQ grid
    lats = np.linspace(-24, -30, 300)
    longs = np.linspace(151, 155, 200)

    # station lat and longs
    stn_lats = tc_df.latitude.values
    stn_longs = tc_df.longitude.values

    tc_aep_pp = np.zeros((len(tc_df), len(windspeeds)))
    for i, (idx, row) in enumerate(tc_df.iterrows()):
        tc_aep_df =  pd.read_csv(os.path.join(IN_DIR, "tc_ari_params_", f"{row.locId}.csv"))
        finterp = interp1d(tc_aep_df.wspd.values, tc_aep_df.AEP.values,
                   bounds_error=False, fill_value=tc_aep_df.AEP.min())
        tc_aep_pp[i, :] = finterp(windspeeds)

    param_names = ['shape', 'scale', 'rate', 'mu']
    grid_params = dict()
    for j in range(4):
        OK = OrdinaryKriging(
            stn_longs,
            stn_lats,
            params[:, j],
            coordinates_type='geographic',
            pseudo_inv=True,
            verbose=False,
            enable_plotting=False,
        )
        z, _ = OK.execute("grid", longs, lats)
        grid_params[param_names[j]] = z

    tc_aep_grid = np.zeros((len(lats),
                            len(longs),
                            len(windspeeds)))
    for j in range(len(windspeeds)):
        OK = OrdinaryKriging(
            stn_longs,
            stn_lats,
            tc_aep_pp[:, j],
            coordinates_type='geographic',
            pseudo_inv=True,
            verbose=False,
            enable_plotting=False,
        )
        z, _ = OK.execute("grid", longs, lats)
        tc_aep_grid[:, :, j] = z

    # combine the AEP for TC, synoptic and TS
    shape, scale = grid_params["shape"][:, :, None], grid_params["scale"][:, :, None]
    rate, mu = grid_params["rate"][:, :, None], grid_params["mu"][:, :, None]

    print("max windspeed:", hazard.GPD.gpdReturnLevel(10_000, mu, shape, scale, rate).max())

    tc_aep = 1.0 - np.exp(-1 / gdp_recurrence_intervals(windspeeds[None, None, :], mu, shape, scale, rate).data)
    comb_aep = 1.0 - (1.0 - syn_aep[None, None, :]) * (1.0 - ts_aep[None, None, :]) * (1.0 - tc_aep_grid)

    # convert windspeed coords + AEP values to AEP coords and windspeed values
    # funky code to quickly linearly interpolate (a for loop + numpy
    # interpolate was much much slower)
    ris = np.array([
        1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100,
        150, 200, 250, 300, 350, 400, 450, 500, 1000, 2000, 2500,
        5000, 10000]
    )

    aeps = 1 - np.exp(-1 / ris)
    outda = interpgrid(comb_aep, windspeeds, aeps)
    for idx, (ri, aep) in enumerate(zip(ris, aeps)):
        da = xr.DataArray(
            outda[:, :, idx],
            coords=dict(longitude=longs, latitude=lats),
            dims=["latitude", "longitude"],
            attrs={'recurrence_interval': ri,
                   'exceedance_probability': aep,
                   'standard_name': 'wind_speed_of_gust',
                   'units': 'm s-1'}
        )
        da.rio.write_crs(7844, inplace=True)
        crs_name = CRS.from_epsg(7844).name
        ds = xr.Dataset(data_vars={'wind_speed_of_gust': da})
        # Update attributes of the dimension variables
        ds.spatial_ref.attrs.update(horizontal_datum_name=crs_name)
        ds.longitude.attrs.update(
            standard_name='longitude',
            long_name="Longitude",
            units='degrees_east',
            axis='X'
        )
        ds.latitude.attrs.update(
            standard_name='latitude',
            long_name="Latitude",
            units='degrees_north',
            axis='Y'
        )
        ds.attrs.update(**gatts)
        ds.to_netcdf(os.path.join(OUT_DIR, "combined_aep",
                                  f"windspeed_{ri}_yr.nc"))
