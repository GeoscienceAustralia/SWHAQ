import os
import xarray as xr

out_arr = None
path = "/g/data/w85/QFES_SWHA/hazard/input/tsindices/"

for fn in os.listdir(path)[:3]:
    if '2021' in fn:
        # skip 2021 because its incomplete
        continue

    if out_arr is None:
        out_arr = xr.load_dataset(os.path.join(path, fn))


print(out_arr)