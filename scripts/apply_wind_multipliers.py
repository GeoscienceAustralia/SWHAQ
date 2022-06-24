import xarray as xr
import os

wm = xr.open_rasterio("/g/data/w85/QFES_SWHA/multipliers/output/QLD/wind-multipliers-maxima.vrt")

in_dir = "/g/data/w85/QFES_SWHA/hazard/output/combined_aep"
out_dir = "/g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep"

fn = "windspeed_200_yr.nc"
ingust = xr.open_dataset(os.path.join(in_dir, fn)).interp(lon=wm.x.data, lat=wm.y.data)

out = ingust.windspeed.data * wm.sel(band=1).data
da = xr.DataArray(out, dims=ingust.dims, coords=ingust.coords)
ds = xr.Dataset(dict(gust=da))
c = ds.to_netcdf(os.path.join(out_dir, fn), compute=True)
# c.compute(num_workers=4)
