import xarray as xr
import rasterio
from rasterio import features
import shapely
from shapely.geometry import Point, Polygon, mapping
import numpy as np
from matplotlib import pyplot as plt
import fiona


fp = "/g/data/w85/QFES_SWHA/wind/regional/004-08495/windfield/evolution.004-08495.nc"
ds = xr.open_dataset(fp)

# create transform
lat = ds.lat.data
lon = ds.lon.data

nx = len(lon)
ny = len(lat)
xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
xres = (xmax - xmin) / float(nx)
yres = (ymax - ymin) / float(ny)
geotransform = rasterio.Affine(xres, 0, xmin, 0, yres, ymin)

schema = {
    'geometry': 'Polygon',
    'properties': {'timestamp': 'str'},
}

outfp = "/g/data/w85/kr4383/004-08495-93kmh-winds.shp"
with fiona.open('004-08495-93kmh-winds.shp', 'w', 'ESRI Shapefile', schema, crs="EPSG:4326") as c:

    for i in range(0, len(ds.time.data), 3):
        t = ds.time.data[i]
        xx = ds.gust_speed.sel(time=t).compute()

        # mask and xtract polygons
        mask = xx.data >= 25.8
        if mask.any():
            all_polygons = []
            for shape, value in features.shapes(mask.astype(np.int16), mask=(mask >0), transform=geotransform):
                poly = shapely.geometry.shape(shape)
                c.write({
                    'geometry': mapping(poly),
                    'properties': {'timestamp': str(t)},
                })
            
            print(str(t))
            print(poly.bounds)