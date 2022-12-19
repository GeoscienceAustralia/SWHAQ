"""
Update track details for TC scenario 004-08495

"""

import os

import pandas as pd
import numpy as np
from vincenty import vincenty
from Utilities.track import ncSaveTracks, Track
from datetime import datetime

df0 = pd.read_csv("C:/WorkSpace/swhaq/data/tracks/track.004-08495b.csv")

df = df0.copy()
df['Datetime'] = pd.to_datetime(df['Datetime'])
df.index = df['Datetime']
del df['Datetime']
del df['Unnamed: 0']

rs = df.resample('20T', closed='right').interpolate()

ntimes = len(rs.index)
starttime = rs.index[0]

newdt = pd.date_range(starttime, periods=ntimes, freq='H')

df2 = pd.DataFrame(index=newdt, columns=rs.columns)
df2[df2.columns] = rs.values

df2['TimeElapsed'] = np.arange(ntimes)
dt = np.diff(df2.index) / (3600 * np.timedelta64(1, 's'))
coords = df2[["Latitude", "Longitude"]].values
dists = [vincenty(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
speed = np.zeros(len(df2))
speed[:-1] = np.array(dists) / dt

df2["Speed"] = speed
df2['Datetime'] = df2.index.values
df2.set_index(pd.Series(np.arange(ntimes)), inplace=True)
df2['Datetime'] = df2.Datetime.apply(
        lambda x: datetime.strftime(x, "%Y-%m-%d %H:%M")
        )

df2.to_csv("C:/WorkSpace/swhaq/data/tracks/track.004-08495c.csv", index=False)

newtrack = Track(df2.to_records(index=False))
newtrack.trackId = (4, 8495)
newtrack.trackfile = "track.004-08495c.nc"
newtrack.data['Datetime'] = [datetime.strptime(x, "%Y-%m-%d %H:%M") for x in newtrack.data['Datetime']]
scenarioTrackFile = "C:/WorkSpace/swhaq/data/tracks/track.004-08495c.nc"
atts = {"history": "Linear decline in intensity from base scenario",
        "title": "Synthetic tropical cyclone track scenario 004-08495c"}
ncSaveTracks(scenarioTrackFile, [newtrack], calendar='julian', attributes=atts)