"""
extract_multipliers_at_stations.py

Extract site exposure multipliers at the site of a collection of
Automatic Weather Stations used in the analysis of thunderstorm wind
gust data for the Severe Wind Hazard Assessment for South East Queensland.

Station locations are specified in a station details csv file

Site exposure multipliers (in this instance) are the set developed
specifically for the SWHA SEQ project

Contact: Craig Arthur
Date: 2022-12-12
"""

import os
import re
import pandas as pd
import geopandas as gpd
import xarray as xr

M3PATH = "/g/data/w85/QFES_SWHA/multipliers/output"
STNPATH = "/g/data/w85/data/stations/"
PATTERN = "(e\d+\.\d+s\d+.\d{4})"
DIRECTIONS = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
LONNAME = 'Longitude to 4 decimal places in decimal degrees'
LATNAME = 'Latitude to 4 decimal places in decimal degrees'
STNNUM = 'Bureau of Meteorology Station Number'

tdf = gpd.read_file(os.path.join(
    M3PATH, "QLD_tindex.shp")).set_crs(epsg=7844, inplace=True)

# Add a field to the tile index file that only contains the extent
# (e.g. e153.0001s28.0015)
tdf['tname'] = tdf['location'].apply(lambda x: re.search(PATTERN, x).group(0))

# Load station file and convert to a GeoDataFrame:
stndf = pd.read_csv(os.path.join(
    STNPATH, "DC02D_StnDet_999999999632559_updated.txt"))
geom = gpd.points_from_xy(stndf[LONNAME], stndf[LATNAME], crs="EPSG:7844")
stndf = gpd.GeoDataFrame(stndf, geometry=geom)

# Spatial join of the stations to the tiles:
stndf_tiles = stndf.sjoin(tdf, how="inner", predicate="intersects")
stndf_tiles.set_index(STNNUM, inplace=True, drop=False)

# Set default values:
for dirn in DIRECTIONS:
    MTNAME = f'Mt_{dirn}'
    MZNAME = f'Mz_{dirn}'
    M3NAME = f'M3_{dirn}'
    stndf_tiles[MTNAME] = 1
    stndf_tiles[MZNAME] = 1
    stndf_tiles[M3NAME] = 1

# Group by the tile name, this means we open each multiplier file only once
for tname, stns in stndf_tiles.groupby('tname'):
    print(f"Processing tile {tname}")
    lons = xr.DataArray(stns[LONNAME].values,
                        coords=[stns.index.values],
                        dims=[STNNUM])
    lats = xr.DataArray(stns[LATNAME].values,
                        coords=[stns.index.values],
                        dims=[STNNUM])
    for dirn in DIRECTIONS:
        MTNAME = f'Mt_{dirn}'
        MZNAME = f'Mz_{dirn}'
        mtfname = os.path.join(M3PATH, "QLD",
                               "topographic",
                               f"{tname}_mt_{dirn}.nc")
        mzfname = os.path.join(M3PATH, "QLD",
                               "terrain",
                               f"{tname}_mz_{dirn}.nc")
        mtds = xr.open_dataset(mtfname)
        mtval = (mtds.interp(lon=lons, lat=lats, method='nearest')
                 .to_dataframe()
                 .rename(columns={'Mt': MTNAME})
                 )
        stndf_tiles.loc[stns.index, MTNAME] = mtval[MTNAME]
        mzds = xr.open_dataset(mzfname)
        mzval = (mzds.interp(lon=lons, lat=lats, method='nearest')
                 .to_dataframe()
                 .rename(columns={'Mz': MZNAME})
                 )
        stndf_tiles.loc[stns.index, MZNAME] = mzval[MZNAME]

# Merge to give M3 value (really only M2, since we ignore shielding effects)
for dirn in DIRECTIONS:
    MTNAME = f'Mt_{dirn}'
    MZNAME = f'Mz_{dirn}'
    stndf_tiles[f'M3_{dirn}'] = stndf_tiles[MTNAME] * stndf_tiles[MZNAME]

# Save the data to file:
(stndf_tiles.drop(STNNUM, axis=1)
 .to_file(os.path.join(
    STNPATH, "DC02D_StnDet_999999999632559_M3.shp"))
 )
(stndf_tiles.drop('geometry', axis=1)
 .to_csv(os.path.join(
    STNPATH, "DC02D_StnDet_999999999632559_M3.csv"), index=False)
 )
