#!/usr/bin/env python
# coding: utf-8

# # Landfall rates for simulated tropical cyclones
# 
# This notebook looks at the rate of landfalling tropical cyclones
# simulated in the TCHA. "Landfall" is a loose definition, where we have set out
# a series of gates around the coastline, which are set 50 km off the coast, and
# each gate is 200 km wide. 
# 
# We look at landfall as this is where the impacts of TCs are felt. We will
# compare to historical rates at a later point. 
# 
# The gates are defined in a vector shapefile as line segments. We'll look at
# the counts, and the mean intensity at landfall to see how well it corresponds
# to historical landfall rates and intensity. 
# 
# Note however, we'd expect the historical record to be somewhat different to
# the mean  values determined here. Arguably, the historical record should be
# (statistically) indistiguishable from the range of scenarios. It should appear
# to be like any other member of the distribution.
# 
# The simulations used here are 35-year simulations of TC activity in the
# Australian region. This corresponds to the length of historical record used
# as the input record to the TCHA (1981-2016). The TCs are simulated with a
# 3-hour timestep. 


import os
from os import walk
from os.path import join as pjoin
import matplotlib.pyplot as plt
import geopandas as gpd
from Utilities import track
from shapely.geometry import LineString, Point
import numpy as np
import pandas as pd
import seaborn as sns
sns.set_style('whitegrid')


# Start with reading in the gates into a `GeoDataFrame`,
# and adding some additional attributes. This `GeoDataFrame` will be duplicated
# for each simulation, then aggregated for the summary statistics. 

gates = gpd.read_file("C:/WorkSpace/data/tcha/gates.shp")
gates['sim'] = 0
gates['count'] = 0
gates['meanlfintensity'] = np.nan
gates['minlfintensity'] = np.nan
gates['cat1'] = 0
gates['cat2'] = 0
gates['cat3'] = 0
gates['cat4'] = 0
gates['cat5'] = 0


# Define a function to read in the track files. The track files are the TCRM format files, which are netCDF files, with a heirarchical structure. The `tracks.ncReadTrackData` function does this, but we still need to convert each track to a `GeoDataFrame` and add a `geometry` attribute that represents the line of each time step in the track history. We also assign a category attribute to each segment, which at this point in time is simply based on categorising the central pressure according to the Bureau of Meteorology's TC intensity scale.

def readTracks(trackFile):
    """
    Read a track file and create a `GeoPandas.GeoDataFrame` from the data, with
    separate polyline features for each unique track in the file. Also adds a
    nominal intensity category based on the central pressure value.
    
    :param str trackFile: Path to a TCRM-format track file
    
    :returns: `GeoPandas.GeoDataFrame` of tracks
    """
    tracks = track.ncReadTrackData(trackFile)
    trackgdf = []
    for t in tracks:
        segments = []
        for n in range(len(t.data) - 1):
            segment = LineString([[t.Longitude[n], t.Latitude[n]],[t.Longitude[n+1], t.Latitude[n+1]]])
            segments.append(segment)
        gdf = gpd.GeoDataFrame.from_records(t.data[:-1])
        gdf['geometry'] = segments
        gdf['category'] = pd.cut(gdf['CentralPressure'], 
                                bins=[0, 930, 955, 970, 985, 990, 1020], 
                                labels=[5,4,3,2,1,0])
        trackgdf.append(gdf)
    trackgdf = pd.concat(trackgdf)
    return trackgdf

def isLeft(line, point):
    """
    Test whether a point is to the left of a (directed) line segment. 
    
    :param line: :class:`Shapely.geometry.LineString` of the line feature being tested
    :param point: :class:`Shapely.geometry.Point` being tested
    
    :returns: `True` if the point is to the left of the line segment, `False` otherwise 
    """
    start = Point(line.coords[0])
    end = Point(line.coords[1])

    det = (end.x - start.x) * (point.y - start.y) - (end.y - start.y) * (point.x - start.x)
    if det > 0: return True
    if det <= 0: return False

def isLandfall(gate, tracks):
    """
    Determine the count of tracks crossing a gate segment. 
    
    :param gate: `shapely.Geometry.LineSegment` 
    :param tracks: `GeoPandas.GeoDataFrame` of tracks, where the `geometry` field is a
                   `LineSegment`
                   
    """
    crossings = tracks.crosses(gate.geometry)
    landfall = []
    for t in tracks[crossings].itertuples():
        if isLeft(gate.geometry, Point(t.geometry.coords[0])):
            landfall.append(True)
        else:
            landfall.append(False)

    return tracks[crossings][landfall]


# This function counts the number of track segments that cross the coastal gates. 

def countCrossings(gates, tracks, sim):
    """
    Count the crossing rate of all gates for all tracks in a given simulation.
    
    """
    gates['sim'] = sim
    for i, gate in enumerate(gates.itertuples(index=False)):
        ncrossings = 0
        l = isLandfall(gate, tracks)
        ncrossings = len(l)
        if ncrossings > 0:
            gates['count'].iloc[i] = ncrossings
            gates['meanlfintensity'].iloc[i] = l['CentralPressure'].mean()
            gates['minlfintensity'].iloc[i] = l['CentralPressure'].min()
            cathist, bins = np.histogram(l['category'].values, bins=[0,1,2,3,4,5, 6])
            gates['cat1'].iloc[i] = cathist[0]
            gates['cat2'].iloc[i] = cathist[1]
            gates['cat3'].iloc[i] = cathist[2]
            gates['cat4'].iloc[i] = cathist[3]
            gates['cat5'].iloc[i] = cathist[4]
        else:
            gates['count'].iloc[i] = 0
            gates['meanlfintensity'].iloc[i] = np.nan
            gates['minlfintensity'].iloc[i] = np.nan
            gates['cat1'].iloc[i] = 0
            gates['cat2'].iloc[i] = 0
            gates['cat3'].iloc[i] = 0
            gates['cat4'].iloc[i] = 0
            gates['cat5'].iloc[i] = 0
            
    return gates


# Get the list of track files from the input data path (this'll become a config
# option in a scripted version of theis notebook). Just find all files in the
# directory that end with "nc" - assume that you're pointing to a directory that
# only has track files. 


filelist = []
datapath = "C:/WorkSpace/swhaq/data/tracks/GROUP1-RCP45-1981-2010/"
for (dirpath, dirnames, filenames) in walk(datapath):
    filelist.extend([fn for fn in filenames if fn.endswith('nc')])
    break
nfiles = len(filelist)
print(f"There are {nfiles} track files")

# Now we loop through all the gates and determine the landfall rates for each simulation. 

gatedflist = []
for sim, f in enumerate(filelist):
    gatedf = gates.copy()
    tracks = readTracks(pjoin(datapath,f))
    gatedf = countCrossings(gatedf, tracks, sim)
    gatedflist.append(gatedf)

gatesummary = pd.concat(gatedflist)

def q10(x): return x.quantile(0.1)
def q90(x): return x.quantile(0.9)
def q25(x): return x.quantile(0.25)
def q75(x): return x.quantile(0.75)

gs = gatesummary.groupby('gate').agg({'count':['sum',np.nanmean, np.nanstd, 'min', 'max', q10, q90],
                                      'cat1': ['sum',np.nanmean, np.nanstd],
                                      'cat2': ['sum',np.nanmean, np.nanstd],
                                      'cat3': ['sum',np.nanmean, np.nanstd],
                                      'cat4': ['sum',np.nanmean, np.nanstd],
                                      'cat5': ['sum',np.nanmean, np.nanstd],
                                      'meanlfintensity':[np.nanmean, q10, q25, q75, q90],
                                      'minlfintensity':[np.nanmean,'min', np.nanstd]}, as_index=False)

gs.columns = ['_'.join(col).strip() for col in gs.columns.values]
gs.reset_index(col_level=1)
gs.columns = gs.columns.get_level_values(0)

gatedata = gates[['gate', 'longitude', 'latitude', 'label', 'geometry']].join(gs)
gatedata.columns


# In[10]:


#gatedata = pd.read_csv("C:/WorkSpace/data/tcha/sim_landfall.csv")
#gatedata.columns


# In[11]:


width=0.4
fig, ax = plt.subplots(3,1,figsize=(12,16),sharex=True)
cat12 = np.add(gatedata['cat1_nanmean'], gatedata['cat2_nanmean']/35.).tolist()
cat123 = np.add(cat12, gatedata['cat3_nanmean']).tolist()
cat1234 = np.add(cat123, gatedata['cat4_nanmean']).tolist()
ax[0].bar(gatedata['gate'], gatedata['cat1_nanmean'], color='b', label="Cat 1")
ax[0].bar(gatedata['gate'], gatedata['cat2_nanmean'], bottom=gatedata['cat1_nanmean'], color='g', label='Cat 2')
ax[0].bar(gatedata['gate'], gatedata['cat3_nanmean'], bottom=cat12, color='y', label='Cat 3')
ax[0].bar(gatedata['gate'], gatedata['cat4_nanmean'], bottom=cat123, color='orange', label='Cat 4')
ax[0].bar(gatedata['gate'], gatedata['cat5_nanmean'], bottom=cat1234, color='r', label='Cat 5')

ax[0].legend()
ax[0].set_ylabel("Mean number of TCs")
ax[1].plot(gatedata['gate'], gatedata['minlfintensity_nanmean'], label='Minimum landfall intensity')
ax[1].plot(gatedata['gate'], gatedata['meanlfintensity_nanmean'], color='r', label='Mean landfall intensity')
ax[1].fill_between(gatedata['gate'], gatedata['meanlfintensity_q10'],
                   gatedata['meanlfintensity_q90'],color='r', alpha=0.25)

ax[1].legend(loc=2)
ax[1].set_ylim((900, 1020))
ax[1].set_ylabel("Pressure (hPa)")
ax[2].plot(gatedata['gate'], gatedata['count_sum']/1000)
ax[2].fill_between(gatedata['gate'], gatedata['count_q90'],gatedata['count_q10'], alpha=0.25)
ax[2].set_xlim((0,48))
ax[2].set_xticks(np.arange(0,48,2))
ax[2].set_yticks(np.arange(0,0.25,.02))
ax[2].set_xticklabels(gatedata['label'][::2], rotation='vertical')
ax[2].set_ylabel("Mean proportion of landfall")


# In[12]:


width=0.4
fig, ax = plt.subplots(1,1, figsize=(12,6), sharex=True)
cat12 = np.add(gatedata['cat1_nanmean'], gatedata['cat2_nanmean']).tolist()
cat123 = np.add(cat12, gatedata['cat3_nanmean']).tolist()
cat1234 = np.add(cat123, gatedata['cat4_nanmean']).tolist()
ax.bar(gatedata['gate'], gatedata['cat1_nanmean'], color='b', label="Cat 1")
ax.bar(gatedata['gate'], gatedata['cat2_nanmean'], bottom=gatedata['cat1_nanmean'], color='g', label='Cat 2')
ax.bar(gatedata['gate'], gatedata['cat3_nanmean'], bottom=cat12, color='y', label='Cat 3')
ax.bar(gatedata['gate'], gatedata['cat4_nanmean'], bottom=cat123, color='orange', label='Cat 4')
ax.bar(gatedata['gate'], gatedata['cat5_nanmean'], bottom=cat1234, color='r', label='Cat 5')



ax.legend()
ax.set_ylabel("Number of TCs")
ax.set_xlim((0,48))
ax.set_xticks(np.arange(0,48,2))
ax.set_yticks(np.arange(0,1,.2))
ax.set_xticklabels(gatedata['label'][::2], rotation='vertical')
ax.set_ylabel("Mean rate of landfall")
plt.savefig(os.path.join(datapath, "mean_landfall_rate_intensity.png"), bbox_inches='tight')


# In[13]:


width=0.4
fig, ax = plt.subplots(1,1, figsize=(12,6), sharex=True)
cat12 = np.add(gatedata['cat1_nanmean'], gatedata['cat2_nanmean']).tolist()
cat123 = np.add(cat12, gatedata['cat3_nanmean']).tolist()
cat1234 = np.add(cat123, gatedata['cat4_nanmean']).tolist()
ax.bar(gatedata['gate'], gatedata['cat1_nanmean'], color='b', label="Cat 1")
ax.bar(gatedata['gate'], gatedata['cat2_nanmean'], bottom=gatedata['cat1_nanmean'], color='g', label='Cat 2')
ax.bar(gatedata['gate'], gatedata['cat3_nanmean'], bottom=cat12, color='y', label='Cat 3')
ax.bar(gatedata['gate'], gatedata['cat4_nanmean'], bottom=cat123, color='orange', label='Cat 4')
ax.bar(gatedata['gate'], gatedata['cat5_nanmean'], bottom=cat1234, color='r', label='Cat 5')

ax.legend()
ax.set_ylabel("Number of TCs")
ax.set_xlim((0,48))
ax.set_xticks(np.arange(0,48,2))
ax.set_yticks(np.arange(0,0.11,.02))
ax.set_xticklabels(gatedata['label'][::2], rotation='vertical')
ax.set_ylabel("Mean rate of landfall")
plt.savefig(os.path.join(datapath,"mean_landfall_rate_intensity.png"), bbox_inches='tight')


# In[14]:


#gatedata.to_file("C:/WorkSpace/data/tcha/sim_landfall.shp")


# In[14]:


gatedata


# In[15]:


gatedata_nogeom = pd.DataFrame(gatedata.drop(columns='geometry'))
gatedata_nogeom.to_csv(os.path.join(datapath,"sim_landfall.csv"), index=False)


# In[ ]:




