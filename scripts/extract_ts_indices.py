import numpy as np
import os
import xarray as xr
from calendar import monthrange
from mpi4py import MPI


def dask_index(arr, indexes):
    # assumes doing the second axis
    sz1 = arr.data.shape[1] * arr.data.shape[2] * arr.data.shape[3]
    sz2 = indexes.shape[1] * indexes.shape[2]
    idxs = indexes.data.flatten() * sz2 + sz1 * (np.arange(indexes.size) // sz2) + np.arange(indexes.size) % sz2
    # sort indices for speed
    y = idxs.argsort()
    i = np.empty_like(y)
    i[y] = np.arange(y.size)
    return arr.data.flatten()[idxs[y]].compute()[i].reshape(indexes.shape)


def dask_interpolate(u, v, z, height):
    top = height * 9.80665
    idxs = (abs(top - z) + 1_000_000_000 * (z > top)).argmin(axis=1).compute()
    z1 = dask_index(z, idxs)
    u1 = dask_index(u, idxs)
    v1 = dask_index(v, idxs)
    z2 = dask_index(z, idxs - 1)
    u2 = dask_index(u, idxs - 1)
    v2 = dask_index(v, idxs - 1)
    u_interp = (u2 * (top - z1) + u1 * (z2 - top)) / (z2 - z1)
    v_interp = (v2 * (top - z1) + v1 * (z2 - top)) / (z2 - z1)
    return u_interp, v_interp


comm = MPI.COMM_WORLD

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"


years = np.arange(1979, 2022)
rank = comm.Get_rank()
long_slice = slice(148, 154)
lat_slice = slice(-24, -33)
rank_years = years[(years % comm.size) == rank]

for year in rank_years:
    for month in range(1, 13):
        days = monthrange(year, month)[1]
        ufile = f"{pl_prefix}/u/{year}/u_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        vfile = f"{pl_prefix}/v/{year}/v_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        capefile = f"{sl_prefix}/cape/{year}/cape_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        u10file = f"{sl_prefix}/10u/{year}/10u_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        v10file = f"{sl_prefix}/10v/{year}/10v_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        totalxfile = f"{sl_prefix}/totalx/{year}/totalx_era5_oper_sfc_{year}{month:02d}01-{year}{month:02d}{days}.nc"
        zfile = f"{pl_prefix}/z/{year}/z_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}{days}.nc"

        if not os.path.isfile(ufile):
            continue

        u = xr.open_dataset(ufile, chunks='auto').u.sel(longitude=long_slice, latitude=lat_slice)
        v = xr.open_dataset(vfile, chunks='auto').v.sel(longitude=long_slice, latitude=lat_slice)
        cape = xr.open_dataset(capefile, chunks='auto').cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        u10 = xr.open_dataset(u10file, chunks='auto').u10.sel(longitude=long_slice, latitude=lat_slice).compute()
        v10 = xr.open_dataset(v10file, chunks='auto').v10.sel(longitude=long_slice, latitude=lat_slice).compute()
        totalx = xr.open_dataset(totalxfile, chunks='auto').totalx.sel(longitude=long_slice, latitude=lat_slice).compute()
        z = xr.open_dataset(zfile, chunks='auto').z.sel(longitude=long_slice, latitude=lat_slice)

        speed500 = np.sqrt(u.sel(level=500).compute() ** 2 + v.sel(level=500).compute() ** 2)
        speed10 = np.sqrt(u10 ** 2 + v10 ** 2)

        mason = (speed500 - speed10) * cape ** 1.67
        mason = mason.data.reshape((-1, 24) + mason.data.shape[1:]).max(axis=1)

        totalx = totalx.data.reshape((-1, 24) + totalx.data.shape[1:]).max(axis=1)

        utop, vtop = dask_interpolate(u, v, z, height=6_000)
        uu = utop - u10
        vv = vtop - v10
        shear = np.sqrt(uu ** 2 + vv ** 2)
        allen = shear * cape ** 1.67
        allen = allen.data.reshape((-1, 24) + allen.data.shape[1:]).max(axis=1)




