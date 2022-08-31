# module use /g/data/hh5/public/modules
# module load conda/analysis3
# conda activate analysis3
# python

import os
import glob
from datetime import datetime
import xarray as xr
import numpy as np
import pandas as pd

import geopandas as gpd
from osgeo import gdal, ogr, osr


inputfile = "/g/data/w85/QFES_SWHA/wind/regional/004-08495/windfield/evolution.004-08495.nc"
outputpath = "/scratch/w85/swhaq/shapefile/"
ds = xr.open_dataset(inputfile)
epsg = 4326
nodata = 0
dx = 0.02
dy = 0.02
ncols = ds.lon.size
nrows = ds.lat.size
originX = ds.lon.min().values
originY = ds.lat.min().values
geotransform = (originX, dx, 0.0, originY, dy, 0.0)

nds = ds.resample(time="15 min").nearest()
dest_folder = "/scratch/w85/swhaq/shapefile"
dst_layername = "region"
outdrv = ogr.GetDriverByName("ESRI Shapefile")

newgdf = gpd.GeoDataFrame(columns=['datetime', 'geometry'], geometry=None, crs="EPSG:4326")
nda = []
ndf = []
driver = gdal.GetDriverByName('MEM')
k = 0 
dts = nds.time.values.astype('datetime64[s]').tolist()
for t, dt in enumerate(dts):
    dtlabel = datetime.strftime(dt, "%Y%m%d%H%M")
    print(f"Processing time: {dtlabel}")
    tempRaster = driver.Create('', ncols, nrows, 1, gdal.GDT_Int16)
    tempRaster.SetGeoTransform((originX, dx, 0,
                                originY, 0, dy))
    tempBand = tempRaster.GetRasterBand(1)
    array = np.where(nds['gust_speed'].isel(time=t).data>=25.8, 1, 0)
    tempBand.WriteArray(array[::int(np.sign(dy) * 1)])
    tempBand.SetNoDataValue(0)

    tempRasterSRS = osr.SpatialReference()
    tempRasterSRS.ImportFromEPSG(epsg)
    tempRaster.SetProjection(tempRasterSRS.ExportToWkt())

    dst_ds = outdrv.CreateDataSource( os.path.join(outputpath, f"{dtlabel}.shp" ))
    dst_layer = dst_ds.CreateLayer(dst_layername, geom_type=ogr.wkbPolygon, srs = tempRasterSRS )
    fd = ogr.FieldDefn('zone', ogr.OFTInteger)
    dst_field = dst_layer.GetLayerDefn().GetFieldIndex('zone')
    gdal.Polygonize(tempBand, None, dst_layer, dst_field, [], callback=None)
    dst_ds = None
    gdf = gpd.read_file(os.path.join(outputpath, f"{dtlabel}.shp" ))
    gdf['datetime'] = dtlabel
    if len(gdf) > 1:
        newgdf = newgdf.append(gdf.iloc[-2])

newgdf.to_file("/scratch/w85/swhaq/shapefile/onset_time.shp")

