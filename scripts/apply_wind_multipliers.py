import xarray as xr
import os
from netCDF4 import Dataset
from osgeo import osr, gdal, gdalconst
import numpy as np
from os.path import join as pjoin, dirname, realpath, isdir, splitext
from osgeo.gdal_array import BandReadAsArray, CopyDatasetInfo, BandWriteArray
import logging
import time

def reprojectDataset(src_file, match_filename, dst_filename,
                     resampling_method=gdalconst.GRA_Bilinear,
                     match_projection=None, warp_memory_limit=0.0):
    """
    Reproject a source dataset to match the projection of another
    dataset and save the projected dataset to a new file.

    :param src_filename: Filename of the source raster dataset, or an
                         open :class:`gdal.Dataset`
    :param match_filename: Filename of the dataset to match to, or an
                           open :class:`gdal.Dataset`
    :param str dst_filename: Destination filename.
    :param resampling_method: Resampling method. Default is bilinear
                              interpolation.

    """

    if isinstance(src_file, str):
        src = gdal.Open(src_file, gdal.GA_ReadOnly)
    else:
        src = src_file
    srcBand = src.GetRasterBand(1)
    srcBand.SetNoDataValue(-9999)
    src_proj = src.GetProjection()

    # We want a section of source that matches this:
    if isinstance(match_filename, str):
        match_ds = gdal.Open(match_filename, gdal.GA_ReadOnly)
    else:
        match_ds = match_filename
    matchBand = match_ds.GetRasterBand(1)
    matchBand.SetNoDataValue(-9999)

    if match_projection:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(match_projection)
        match_proj = srs.ExportToWkt()
    else:
        match_proj = match_ds.GetProjection()
    match_geotrans = match_ds.GetGeoTransform()
    wide = match_ds.RasterXSize
    high = match_ds.RasterYSize

    # Output / destination
    drv = gdal.GetDriverByName('GTiff')
    dst = drv.Create(dst_filename, wide, high, 1, gdal.GDT_Float32)
    dst.SetGeoTransform(match_geotrans)
    dst.SetProjection(match_proj)
    dstBand = dst.GetRasterBand(1)
    dstBand.SetNoDataValue(-9999)

    # Do the work
    gdal.ReprojectImage(src, dst, src_proj, match_proj, resampling_method, WarpMemoryLimit=warp_memory_limit)

    del dst  # Flush
    if isinstance(match_filename, str):
        del match_ds
    if isinstance(src_file, str):
        del src

    return


def createRaster(array, x, y, dx, dy, epsg = 4326, filename=None, nodata=-9999):
    """
    Create an in-memory raster for processing. By default, we assume
    the input array is in geographic coordinates, using WGS84 spatial
    reference system.

    :param array: Data array to be stored.
    :type  array: :class:`numpy.ndarray`
    :param x: x-coordinate of the array values.
    :type  x: :class:`numpy.ndarray`
    :param y: y-coordinate of the array values - should be a negative
              value.
    :type  y: :class:`numpy.ndarray`
    :param float dx: Pixel size in x-direction.
    :param float dy: Pixel size in y-direction.
    :param int epsg: EPSG code of the spatial reference system
                     of the input array (default=4326, WGS84)
    :param filename: Optional path
     to store the data in.
    :type  filename: str or None

    """

    rows, cols = array.shape
    originX, originY = x[0], y[0]
    if filename:
        _, ext = splitext(filename)
    if filename and ext == '.tif':
        driver = gdal.GetDriverByName('GTiff')
        tempRaster = driver.Create(filename, cols, rows, 1, gdal.GDT_Float32)
    elif filename and ext == '.img':
        driver = gdal.GetDriverByName('HFA')
        tempRaster = driver.Create(filename, cols, rows, 1, gdal.GDT_Float32)
    else:
        driver = gdal.GetDriverByName('MEM')
        tempRaster = driver.Create('', cols, rows, 1, gdal.GDT_Float32)

    tempRaster.SetGeoTransform((originX, dx, 0,
                                originY, 0, dy))
    tempBand = tempRaster.GetRasterBand(1)
    tempBand.WriteArray(array[::int(np.sign(dy) * 1)])
    tempBand.SetNoDataValue(nodata)
    tempRasterSRS = osr.SpatialReference()
    tempRasterSRS.ImportFromEPSG(epsg)
    tempRaster.SetProjection(tempRasterSRS.ExportToWkt())

    tempBand.FlushCache()
    return tempRaster


in_dir = "/g/data/w85/QFES_SWHA/hazard/output/combined_aep"
out_dir = "/g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep_pp"

logging.basicConfig(filename=os.path.join(out_dir, "wm_pp.log"), level=logging.INFO,
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s', 
                    datefmt='%y-%m-%d %H:%M:%s')

logging.info("Loading wind multiplier file.")
t0 = time.time()
wm = xr.open_rasterio("/g/data/w85/QFES_SWHA/multipliers/output/QLD/wind-multipliers-maxima.vrt", chunks='auto')
wm = wm.sel(band=1).compute()
logging.info(f"Finished loading wm - took {time.time() - t0}s")

m4_max_file = "/g/data/w85/QFES_SWHA/multipliers/output/QLD/wind-multipliers-maxima.vrt"
m4_max_file_obj = gdal.Open(m4_max_file, gdal.GA_ReadOnly)

for fn in sorted(os.listdir(in_dir)):
    if fn in os.listdir(out_dir):
        logging.info(f"Skipping {fn}.")
        continue

    t0 = time.time()
    logging.info(f"Processing {fn}.")
    # fn = "windspeed_200_yr.nc"
    ingust = xr.load_dataset(os.path.join(in_dir, fn))
    arr = ingust.windspeed.data
    dx = np.diff(ingust.lon).mean()
    dy = np.diff(ingust.lat).mean()

    wind_raster = createRaster(arr, ingust.lon, ingust.lat, dx, dy)
    wind_prj_file = os.path.join(out_dir, "reproj_" + fn)

    gdal.SetConfigOption('GDAL_NUM_THREADS', '4')
    reprojectDataset(wind_raster, m4_max_file_obj, wind_prj_file)

    wind_prj = xr.open_rasterio(wind_prj_file, chunks='auto').sel(band=1)
    out = wm.data * wind_prj.data.compute()
    da = xr.DataArray(out, dims=wind_prj.dims, coords=wind_prj.coords)
    ds = xr.Dataset(dict(gust=da))
    ds.to_netcdf(os.path.join(out_dir, fn))
    del ds
    del da
    del wind_prj

    # break
    logging.info(f"Finished processing {fn} - took {time.time() - t0}s")
