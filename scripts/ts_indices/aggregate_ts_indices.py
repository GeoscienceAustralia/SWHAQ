import os
import xarray as xr

out_ds = None
path = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"
outpath = "/g/data/w85/QFES_SWHA/hazard/input/ts_index_climatology.nc"

for fn in os.listdir(path)[:]:
    print("processing", fn)
    if '2021' in fn:
        # skip 2021 because its incomplete
        continue

    ds = xr.load_dataset(os.path.join(path, fn))
    mason = (ds.mason > 33867).sum(dim='time')
    allen = (ds.allen > 33867).sum(dim='time')
    totalx = (ds.totalx > 48.1).sum(dim='time')

    if out_ds is None:
        out_ds = xr.Dataset(coords=ds.sum(dim='time').coords, attrs=ds.attrs)
        out_ds['mason'] = mason
        out_ds['allen'] = allen
        out_ds['totalx'] = totalx
    else:
        out_ds['mason'] += mason
        out_ds['allen'] += allen
        out_ds['totalx'] += totalx

out_ds /= 41  # 41 years from 1980-2020 inclusive
out_ds.to_netcdf(outpath)
