import os
import xarray as xr

out_ds = None
path = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

for fn in os.listdir(path)[:4]:
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






print(out_ds)