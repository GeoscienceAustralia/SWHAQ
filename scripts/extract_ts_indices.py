import numpy as np
import os
import xarray as xr
import pandas as pd
from calendar import monthrange
import time
from datetime import datetime
from mpi4py import MPI

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
        u10 = xr.open_dataset(u10file, chunks='auto').u10.cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        v10 = xr.open_dataset(u10file, chunks='auto').v10.cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        totalx = xr.open_dataset(totalxfile, chunks='auto').u10.cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        z = xr.open_dataset(zfile, chunks='auto').z.sel(longitude=long_slice, latitude=lat_slice).compute()

        speed500 = np.sqrt(u.sel(level=500).compute() ** 2 + v.sel(pressure=500).compute() ** 2)
        speed10 = np.sqrt(u10 ** 2 + v10 ** 2)

        mason = (speed500 - speed10) * cape ** 1.67
        mason = mason.data.reshape((-1, 24)).max(axis=1)

        idxs = abs(6_000 * 9.80665 - z).argmin(axis=0).compute()
        utop = u.data.flatten()[idxs.flatten() * idxs.size + np.arange(idxs.size)].reshape(idxs.shape).compute()
        vtop = v.data.flatten()[idxs.flatten() * idxs.size + np.arange(idxs.size)].reshape(idxs.shape).compute()

        uu = utop - u10
        vv = vtop - v10
        shear = np.sqrt(uu ** 2 + vv ** 2)
        allen = shear * cape ** 1.67
        allen = allen.data.reshape((-1, 24)).max(axis=1)

        totalx = totalx.data.reshape((-1, 24)).max(axis=1)


