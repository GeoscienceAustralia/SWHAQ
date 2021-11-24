import numpy as np
import os
import xarray as xr
from calendar import monthrange
from mpi4py import MPI
import metpy
import time


def calc_lr13(height_profile, temp_profile):
    idx = np.where(height_profile <= 1_000)[0][-1]
    temp_1 = temp_profile[idx] * (1_000 - height_profile[idx])
    temp_1 += temp_profile[idx + 1] * (height_profile[idx + 1] - 1_000)
    temp_1 /= height_profile[idx + 1] - height_profile[idx]

    idx = np.where(height_profile <= 3_000)[0][-1]
    temp_3 = temp_profile[idx] * (3_000 - height_profile[idx])
    temp_3 += temp_profile[idx + 1] * (height_profile[idx + 1] - 3_000)
    temp_3 /= height_profile[idx + 1] - height_profile[idx]

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
    top_idx = None

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
                top_idx = bottom_idx
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
    bottom_idx, top_idx = calc_effective_layer(pressure, temperature, dewpoint)

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

    qmelt = calc_melting_point_mixing_ratio(relative_humidity, pressure, temperature, dewpoint)

    dowdy = 6.1e-02 * shear + 1.5e-1 * windspeed_mean + 9.4e-1 * lr13 + 3.9e-2 * rhmin13
    dowdy += 1.7e-02 * srhe + 3.8e-1 * qmelt + 4.7e-4 * efflcl - 1.3e1
    dowdy = 1 / (1 + dowdy.exp())

    return dowdy


comm = MPI.COMM_WORLD

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

years = np.arange(1980, 2022)
rank = comm.Get_rank()
long_slice = slice(148, 154)
lat_slice = slice(-24, -33)
rank_years = years[(years % comm.size) == rank]

t0 = time.time()

for year in rank_years:
    for month in range(1, 13):
        print(f"Processing {month}/{year}")
        days = monthrange(year, month)[1]
        ufile = f"{pl_prefix}/u/{year}/u_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        vfile = f"{pl_prefix}/v/{year}/v_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        capefile = f"{sl_prefix}/cape/{year}/cape_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        u10file = f"{sl_prefix}/10u/{year}/10u_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        v10file = f"{sl_prefix}/10v/{year}/10v_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        totalxfile = f"{sl_prefix}/totalx/{year}/totalx_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        zfile = f"{pl_prefix}/z/{year}/z_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        tfile = f"{pl_prefix}/t/{year}/t_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        rhfile = f"{pl_prefix}/r/{year}/r_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"

        if not os.path.isfile(ufile):
            continue

        u = xr.open_dataset(ufile, chunks='auto').u.sel(longitude=long_slice, latitude=lat_slice).compute()
        v = xr.open_dataset(vfile, chunks='auto').v.sel(longitude=long_slice, latitude=lat_slice).compute()
        cape = xr.open_dataset(capefile, chunks='auto').cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        u10 = xr.open_dataset(u10file, chunks='auto').u10.sel(longitude=long_slice, latitude=lat_slice).compute()
        v10 = xr.open_dataset(v10file, chunks='auto').v10.sel(longitude=long_slice, latitude=lat_slice).compute()
        totalx = xr.open_dataset(totalxfile, chunks='auto').totalx.sel(longitude=long_slice, latitude=lat_slice).compute()
        z = xr.open_dataset(zfile, chunks='auto').z.sel(longitude=long_slice, latitude=lat_slice).compute()
        temp = xr.open_dataset(tfile, chunks='auto').t.sel(longitude=long_slice, latitude=lat_slice).compute()
        rh = xr.open_dataset(rhfile, chunks='auto').t.sel(longitude=long_slice, latitude=lat_slice).compute()

        t1 = time.time()
        print(f"Data loading: {t1 - t0} s")
        dowdy = cape.copy(data=np.empty_like(cape.data))

        for i, time in enumerate(u.coords['time']):
            for j, lat in enumerate(u.coords['latitude']):
                for k, lon in enumerate(u.coords['longitude']):
                    u_profile = u.data[i, :, j, k]
                    v_profile = v.data[i, :, j, k]
                    height_profile = z.data[i, :, j, k] / 9.80665
                    pressure_profile = z.coords['pressure'].data
                    temp_profile = temp.data[i, :, j, k]
                    rh_profile = rh.data[i, :, j, k]

                    dowdy.data[i, j, k] = calc_dowdy(
                        u.data[i, :, j, k], v.data[i, :, j, k], z.coords['pressure'].data,
                        temp.data[i, :, j, k], z.data[i, :, j, k] / 9.80665, rh.data[i, :, j, k]

                    )

        data_vars = {
            "dowdy": dowdy
        }

        coords = {
            'time': u.coords['time'].data.reshape((-1, 24))[:, 0],
            'latitude': u.coords['latitude'].data,
            'longitude': u.coords['longitude'].data,
        }

        ds = xr.Dataset(data_vars, coords)
        ds.to_netcdf(outpath + f"dowdy_{year}{month:02d}01-{year}{month:02d}{days}.nc")
        print(f"Calculations: {time.time() - t1} s")
        break
    break

print("Time taken:", time.time() - t0, "s")
