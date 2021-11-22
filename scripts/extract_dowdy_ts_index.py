import numpy as np
import os
import xarray as xr
from calendar import monthrange
from mpi4py import MPI
import metpy

comm = MPI.COMM_WORLD

pl_prefix = "/g/data/rt52/era5/pressure-levels/reanalysis"
sl_prefix = "/g/data/rt52/era5/single-levels/reanalysis"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

years = np.arange(1980, 2022)
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

        u = xr.open_dataset(ufile, chunks='auto').u.sel(longitude=long_slice, latitude=lat_slice).compute()
        v = xr.open_dataset(vfile, chunks='auto').v.sel(longitude=long_slice, latitude=lat_slice).compute()
        cape = xr.open_dataset(capefile, chunks='auto').cape.sel(longitude=long_slice, latitude=lat_slice).compute()
        u10 = xr.open_dataset(u10file, chunks='auto').u10.sel(longitude=long_slice, latitude=lat_slice).compute()
        v10 = xr.open_dataset(v10file, chunks='auto').v10.sel(longitude=long_slice, latitude=lat_slice).compute()
        totalx = xr.open_dataset(totalxfile, chunks='auto').totalx.sel(longitude=long_slice, latitude=lat_slice).compute()
        z = xr.open_dataset(zfile, chunks='auto').z.sel(longitude=long_slice, latitude=lat_slice).compute()

        umean = np.empty_like(cape.data)
        lr13 = np.empty_like(cape.data)  # temperature lapse rate from 1-3km
        rhmin13 = np.empty_like(cape.data)  # rel hum min 1-3km
        srhe = np.empty_like(cape.data)  # effective-layer storm relative helicity
        qmelt = np.empty_like(cape.data)  # water vapor mixing ratio at the height of the melting level
        efflcl = np.empty_like(cape.data)

        for time in u.coords['time']:
            for lat in u.coords['latitude']:
                for lon in u.coords['longitude']:
                    umean = metpy.calc.mean_pressure_weighted(u.coords['level'], u, height=None, bottom=None, depth=None)

        lr13 = None # temperature lapse rate from 1-3km
        rhmin13 = None # rel hum min 1-3km
        srhe = None # effective-layer storm relative helicity
        qmelt = None # water vapor mixing ratio at the height of the melting level
        efflcl = None # effective-layer parcel lifting condensation level

        # dowdy = 6.1e-02 * shear + 1.5e-1 * umean + 9.4e-1 * lr13 + 3.9e-2 * rhmin13
        # dowdy += 1.7e-02 * srhe + 3.8e-1 * qmelt + 4.7e-4 * efflcl -1.3e1

        days = u.coords['time'].data.reshape((-1, 24))[:, 0]

        data_vars = {
        }

        coords = {
            'time': days,
            'latitude': u.coords['latitude'].data,
            'longitude': u.coords['longitude'].data,
        }

        ds = xr.Dataset(data_vars, coords)
        ds.to_netcdf(outpath + "ts_indices_{year}{month:02d}01-{year}{month:02d}{days}.nc")
