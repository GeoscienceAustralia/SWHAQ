import os
import sys
import logging
import time
from calendar import monthrange
import xarray as xr
import metpy
from metpy.units import units
import numpy as np
import time

from parallel import attemptParallel, disableOnWorkers

MPI = attemptParallel()
comm = MPI.COMM_WORLD

logging.basicConfig(filename='extract_dowdy_ts_index.log', level=logging.DEBUG)

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

def main():
    """
    Handle command line arguments and call processing functions

    """

    if comm.rank == 0:
        master_process()
    else:
        slave_process()


def master_process():
    for year in range(1980, 2021):
        for month in range(1, 13):
            logging.info(f"Processing {month}/{year}")


def slave_process():
    data = comm.recv(source=0)
    tidx, coords, u_profiles, v_profiles, height_profiles, temp_profiles, rh_profiles = data
    outarray = np.zeros((u_profiles.shape[1], u_profiles.shape[2]))
    prssure_profile = coords['pressure'].data
    for j in range(u_profiles.shape[1]):
        for k in range(u_profiles.shape[2]):
            u_profile = u_profiles[:, j, k]
            v_profile = v_profiles[:, j, k]
            height_profile = height_profiles[:, j, k]
            temp_profile = temp_profiles[:, j, k]
            rh_profile = rh_profiles[:, j, k]

            outarray[j, k] = calc_dowdy(
                u_profile, v_profile, prssure_profile,
                temp_profile, height_profile, rh_profile

            )

    return outarray, tidx


def process(year: int, month: int):
    t0 = time.time()

    print(f"Started processing {month}/{year}")
    logging.info(f"Started processing {month}/{year}")

    long_slice = slice(148, 154)
    lat_slice = slice(-24, -33)

    days = monthrange(year, month)[1]
    ufile = f"{pl_prefix}/u/{year}/u_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    vfile = f"{pl_prefix}/v/{year}/v_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    zfile = f"{pl_prefix}/z/{year}/z_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    tfile = f"{pl_prefix}/t/{year}/t_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
    rhfile = f"{pl_prefix}/r/{year}/r_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"

    u = xr.open_dataset(ufile).u.sel(longitude=long_slice, latitude=lat_slice)
    v = xr.open_dataset(vfile).v.sel(longitude=long_slice, latitude=lat_slice)
    z = xr.open_dataset(zfile).z.sel(longitude=long_slice, latitude=lat_slice)
    temp = xr.open_dataset(tfile).t.sel(longitude=long_slice, latitude=lat_slice)
    rh = xr.open_dataset(rhfile).r.sel(longitude=long_slice, latitude=lat_slice)

    nt = len(u.coords['time'])
    tidx = 0
    status = MPI.Status()

    outarray = np.zeros((u.data.shape[0], u.data.shape[2], u.data.shape[3]))

    for rank in range(1, comm.size):
        u_profiles = u.data[tidx, ...]
        v_profiles = v.data[tidx, ...]
        height_profiles = z.data[tidx, ...] / 9.80665
        temp_profiles = temp.data[tidx, ...]
        rh_profiles = rh.data[tidx, ...]

        data = (tidx, u.coords, u_profiles, v_profiles, height_profiles, temp_profiles, rh_profiles)
        comm.send(data, dest=rank)

        tidx += 1

    terminated = 0
    while terminated < comm.size -1:
        result, outidx = comm.recv(source=MPI.ANY_SOURCE, status=status)
        outarray[outidx, ...] = result
        rank = status.source
        if tidx < nt:
            comm.send(tidx, dest=rank)
            tidx += 1
        else:
            terminated += 1

    print(f"Finished processing {month}/{year}. Took {np.round(time.time() - t0)}s")
    logging.info(f"Finished processing {month}/{year}. Took {np.round(time.time() - t0)}s")
    time_days = u.coords['time'].data.reshape((-1, 24))[:, 0]

    outarray = outarray.reshape((-1, 24, outarray.shape[1], outarray.shape[2])).max(axis=1)
    data_vars = {
        'dowdy': (('time', 'latitude', 'longitude'), outarray),
    }

    coords = {
        'time': time_days,
        'latitude': u.coords['latitude'].data,
        'longitude': u.coords['longitude'].data,
    }

    ds = xr.Dataset(data_vars, coords)
    # attribute_ds(ds)

    ds.to_netcdf(outpath + f"dowdy_ts_index_{year}{month:02d}01-{year}{month:02d}{days}.nc")


def calc_lr13(height_profile, temp_profile):
    idx = np.where(height_profile <= 1_000)[0][0]
    temp_1 = temp_profile[idx] * (1_000 - height_profile[idx])
    temp_1 += temp_profile[idx - 1] * (height_profile[idx - 1] - 1_000)
    temp_1 /= height_profile[idx - 1] - height_profile[idx]

    idx = np.where(height_profile <= 3_000)[0][0]
    temp_3 = temp_profile[idx] * (3_000 - height_profile[idx])
    temp_3 += temp_profile[idx - 1] * (height_profile[idx - 1] - 3_000)
    temp_3 /= height_profile[idx - 1] - height_profile[idx]

    return (temp_3 - temp_1) / 3


def calc_rhmin13(height_profile, rh_profile):
    mask = (1_000 <= height_profile) & (height_profile <= 3_000)
    return rh_profile[mask].min()


def calc_melting_point_mixing_ratio(relative_humidity, pressure, temperature, dewpoint):
    wetbulb = metpy.calc.wet_bulb_temperature(pressure, temperature, dewpoint)
    idx = np.where(wetbulb <= 0)[0][-1]
    mixing_ratio_1 = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure[idx], temperature[idx], relative_humidity[idx]
    )

    mixing_ratio_2 = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure[idx + 1], temperature[idx + 1], relative_humidity[idx + 1]
    )

    mixing_ratio = mixing_ratio_1 * (wetbulb[idx + 1] - 0) + mixing_ratio_2 * (0 - wetbulb[idx])
    mixing_ratio /= wetbulb[idx + 1] - wetbulb[idx]
    return mixing_ratio


def calc_dewpoint(pressure, temperature, relative_humidity):
    mixing_ratio = metpy.calc.mixing_ratio_from_relative_humidity(
        pressure, temperature, relative_humidity
    )
    vapor_pressure = metpy.calc.vapor_pressure(pressure, mixing_ratio)
    dewpoint = metpy.calc.dewpoint(vapor_pressure)
    return dewpoint


def calc_effective_layer(pressure, temperature, dewpoint):

    bottom_idx = None
    top_idx = 0

    # start at ground level and increment pressure levels
    for parcel_idx in range(len(pressure) - 1, -1, -1):
        p, t, td, mu_profile = metpy.calc.parcel_profile_with_lcl(
            pressure[parcel_idx:], temperature[parcel_idx:], dewpoint[parcel_idx:]
        )

        cape, cin = metpy.calc.cape_cin(p, t, td, mu_profile)

        if (cape > 100) and (cin > -250):
            # if this is the first pressure level (from ground) to satisfy the constraints
            # this is the bottom of the inflow layer
            if bottom_idx is None:
                bottom_idx = parcel_idx
        else:
            # if this is the first pressure level (from base of inflow level) that violates
            # the constraints this is the end of the inflow layer
            if bottom_idx is not None:
                top_idx = parcel_idx
                break

    return bottom_idx, top_idx


def calc_windpeed_mean(u, v, pressure):
    mask = (600 <= pressure) & (pressure <= 800)
    umean = metpy.calc.mean_pressure_weighted(
        pressure[mask], u[mask]
    )
    vmean = metpy.calc.mean_pressure_weighted(
        pressure[mask], v[mask]
    )
    windspeed_mean = metpy.calc.wind_speed(umean, vmean)
    return windspeed_mean


def calc_dowdy(u, v, pressure, temperature, height, relative_humidity):
    windspeed_mean = calc_windpeed_mean(u, v, pressure)
    lr13 = calc_lr13(height, temperature)
    rhmin13 = calc_rhmin13(height, relative_humidity)

    # find effective layer
    dewpoint = calc_dewpoint(pressure, temperature, relative_humidity)
    qmelt = calc_melting_point_mixing_ratio(relative_humidity, pressure, temperature, dewpoint)

    bottom_idx, top_idx = calc_effective_layer(pressure, temperature, dewpoint)

    if bottom_idx is None:
        srhe, shear, mixed_parcel, efflcl = 0, 0, 0, 0
    else:
        srhe = metpy.calc.storm_relative_helicity(
            height[top_idx:bottom_idx], u[top_idx:bottom_idx], v[top_idx:bottom_idx]
        )

        shear = metpy.calc.wind_speed(
            *metpy.calc.bulk_shear(
                pressure[top_idx:bottom_idx], u[top_idx:bottom_idx], v[top_idx:bottom_idx]
            )
        )

        mixed_parcel = metpy.cacl.mixed_parcel(
            pressure[top_idx:bottom_idx], temperature[top_idx:bottom_idx], dewpoint[top_idx:bottom_idx]
        )
        efflcl = metpy.calc.lcl(*mixed_parcel)

    dowdy = 6.1e-02 * shear + 1.5e-1 * windspeed_mean + 9.4e-1 * lr13 + 3.9e-2 * rhmin13
    dowdy += 1.7e-02 * srhe + 3.8e-1 * qmelt + 4.7e-4 * efflcl - 1.3e1
    dowdy = 1 / (1 + dowdy.exp())

    return dowdy