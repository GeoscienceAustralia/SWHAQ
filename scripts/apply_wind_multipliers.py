
import os
import sys
import rioxarray
import xarray as xr
from osgeo import osr, gdal, gdalconst
import numpy as np
from os.path import splitext
import logging
import time
from datetime import datetime
from git import Repo

repo = Repo(path='', search_parent_directories=True)

commit = repo.commit()
AUTHOR = commit.author.name
COMMITDATE = time.strftime("%Y-%m-%d %H:%M:%S",
                           time.gmtime(commit.committed_date))
URL = list(repo.remotes[0].urls)[0]
now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
history_msg = f"{now}: {(' ').join(sys.argv)}"

# Global attributes:
gatts = {"title": "Local wind hazard data",
         "repository": URL,
         "author": AUTHOR,
         "commit_date": COMMITDATE,
         "commit": commit.hexsha,
         "history": history_msg,
         "creation_date": now}


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
    gdal.ReprojectImage(src, dst, src_proj, match_proj, resampling_method,
                        WarpMemoryLimit=warp_memory_limit)

    del dst  # Flush
    if isinstance(match_filename, str):
        del match_ds
    if isinstance(src_file, str):
        del src

    return


def createRaster(array, x, y, dx, dy, epsg=4326,
                 filename=None, nodata=-9999):
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

logging.basicConfig(filename=os.path.join(out_dir, "wm_pp.log"),
                    level=logging.INFO,
                    format='%(asctime)s: %(name)s: %(levelname)s: %(message)s',
                    datefmt='%y-%m-%d %H:%M:%S')

logging.info("Loading wind multiplier file.")
t0 = time.time()
wm = rioxarray.open_rasterio("/g/data/w85/QFES_SWHA/multipliers/output/QLD/wind-multipliers-maxima.vrt", chunks='auto')
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
    ingust = xr.load_dataset(os.path.join(in_dir, fn), decode_coords="all")
    arr = ingust.wind_speed_of_gust.data
    ari = ingust.wind_speed_of_gust.attrs['recurrence_interval']
    aep = ingust.wind_speed_of_gust.attrs['exceedance_probability']
    dx = np.diff(ingust.longitude).mean()
    dy = np.diff(ingust.latitude).mean()
    epsg = ingust.wind_speed_of_gust.rio.crs.to_epsg()
    logging.debug(f"Hazard layer has CRS with EPSG {epsg}")
    wind_raster = createRaster(arr, ingust.longitude, ingust.latitude,
                               dx, dy, epsg)
    wind_prj_file = os.path.join(out_dir, "reproj_" + fn)

    gdal.SetConfigOption('GDAL_NUM_THREADS', '4')
    reprojectDataset(wind_raster, m4_max_file_obj, wind_prj_file)

    wind_prj = rioxarray.open_rasterio(wind_prj_file, chunks='auto').sel(band=1)
    out = wm.data * wind_prj.data.compute()
    wind_prj = wind_prj.rename({'x': 'longitude', 'y': 'latitude'})
    da = xr.DataArray(out, dims=wind_prj.dims, coords=wind_prj.coords,
                      attrs={'standard_name': 'wind_speed_of_gust',
                             'long_name': 'Maximum local gust wind speed',
                             'units': 'm s-1',
                             'missing_value': -9999.,
                             'recurrence_interval': ari,
                             'exceedance_probability': aep})
    da.rio.write_crs(epsg, inplace=True)
    ds = xr.Dataset(dict(wind_speed_of_gust=da))

    # Update attributes of the dimension variables
    ds.longitude.attrs.update(
        standard_name='longitude',
        long_name="Longitude",
        units='degrees_east',
        axis='X'
    )
    ds.latitude.attrs.update(
        standard_name='latitude',
        long_name="Latitude",
        units='degrees_north',
        axis='Y'
    )

    # Update global attributes
    ds.attrs.update(**gatts)

    ds.to_netcdf(os.path.join(out_dir, fn))
    del ds
    del da
    del wind_prj
    os.unlink(wind_prj_file)

    # break
    logging.info(f"Finished processing {fn} - took {time.time() - t0}s")
