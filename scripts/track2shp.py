import os
import Utilities.shapefile as shapefile
from Utilities.metutils import convert, bearing2theta
import numpy as np
from netCDF4 import Dataset, num2date
from datetime import datetime
from shapely.geometry import Point, LineString

TCRMFIELD_NAMES = ('CycloneNumber', 'TimeElapsed', 
                   'Longitude', 'Latitude', 'Speed', 'Bearing',
                   'pCentre', 'pEnv', 'rMax',
                   'Year', 'Month', 'Day', 'Hour', 'Minute', 'Category')
TCRMFIELD_TYPES = ("N",)*15
TCRMFIELD_WIDTH = (2, 6, 7, 7, 6, 6, 7, 7, 6, 4, 2, 2, 2, 2, 1)
TCRMFIELD_PRECS = (0, 2, 2, 2, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0)

TCRMFIELDS = [[n, t, w, p] for n, t, w, p in zip(TCRMFIELD_NAMES,
                                                 TCRMFIELD_TYPES,
                                                 TCRMFIELD_WIDTH,
                                                 TCRMFIELD_PRECS)]

ISO_FORMAT = "%Y-%m-%d %H:%M:%S"

TCRM_COLS = ('CycloneNumber', 'Datetime', 'TimeElapsed', 'Longitude',
             'Latitude', 'Speed', 'Bearing', 'CentralPressure',
             'EnvPressure', 'rMax')

TCRM_UNIT = ('', '', 'hr', 'degree', 'degree', 'kph', 'degrees',
                  'hPa', 'hPa', 'km')

TCRM_FMTS = ('i', 'object', 'f', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8')

TCRM_CNVT = {
    0: lambda s: int(float(s.strip() or 0)),
    1: lambda s: datetime.strptime(s.strip(), ISO_FORMAT),
    5: lambda s: convert(float(s.strip() or 0), TCRM_UNIT[5], 'mps'),
    6: lambda s: bearing2theta(float(s.strip() or 0) * np.pi / 180.),
    7: lambda s: convert(float(s.strip() or 0), TCRM_UNIT[7], 'Pa'),
    8: lambda s: convert(float(s.strip() or 0), TCRM_UNIT[8], 'Pa'),
}

TRACK_DT_ERR = "Track data does not have required \
attributes to convert to datetime object"

TRACK_EMPTY_GROUP = """No track groups in this netcdf file: {0}"""

class Track(object):
    """
    A single tropical cyclone track.

    The object exposes the track data through the object attributes.
    For example, If `data` contains the tropical cyclone track data
    (`numpy.array`) loaded with the :meth:`readTrackData` function,
    then the central pressure column can be printed out with the
    code::

        t = Track(data)
        print(t.CentralPressure)

    :type  data: numpy.ndarray
    :param data: the tropical cyclone track data.
    """

    def __init__(self, data):
        """
        :type  data: numpy.ndarray
        :param data: the tropical cyclone track data.
        """
        self.data = data
        self.trackId = None
        self.trackfile = None
        if (len(data) > 0) and ('CentralPressure' in data.dtype.names):
            self.trackMinPressure = np.min(data['CentralPressure'])
        else:
            self.trackMinPressure = None
        if (len(data) > 0) and ('WindSpeed' in data.dtype.names):
            self.trackMaxWind = np.max(data['WindSpeed'])
        else:
            self.trackMaxWind = None

    def __getattr__(self, key):
        """
        Get the `key` from the `data` object.

        :type  key: str
        :param key: the key to lookup in the `data` object.
        """
        if (key.startswith('__') and key.endswith('__')) or (key == 'data'):
            return super(Track, self).__getattr__(key)

        return self.data[key]

    def inRegion(self, gridLimit):
        """
        Check if the tropical cyclone track starts within a region.

        :type  gridLimit: :class:`dict`
        :param gridLimit: the region to check.
                          The :class:`dict` should contain the keys
                          :attr:`xMin`, :attr:`xMax`, :attr:`yMin` and
                          :attr:`yMax`. The *x* variable bounds the
                          latitude and the *y* variable bounds the
                          longitude.

        """
        xMin = gridLimit['xMin']
        xMax = gridLimit['xMax']
        yMin = gridLimit['yMin']
        yMax = gridLimit['yMax']

        return ((xMin <= self.Longitude[0]) and
                (self.Longitude[0] <= xMax) and
                (yMin <= self.Latitude[0]) and
                (self.Latitude[0] <= yMax))

    def minimumDistance(self, points):
        """
        Calculate the minimum distance between a track and a
        collection of :class:`shapely.geometry.Point` points. Assumes
        the points and the :attr:`Longitude` and :attr:`Latitude`
        attributes share the same coordinate system (presumed to be
        geographic coordinates).

        :param points: sequence of :class:`shapely.geometry.Point` objects.

        :returns: :class:`numpy.ndarray` of minimum distances between
                  the set of points and the line features (in km).
        """
        coords = [(x, y) for x, y in zip(self.Longitude, self.Latitude)]

        if len(coords) == 1:
            point_feature = Point(self.Longitude, self.Latitude)
            distances = [point_feature.distance(point) for point in points]
        else:
            line_feature = LineString(coords)
            distances = [line_feature.distance(point) for point in points]

        return convert(distances, 'deg', 'km')

def ncReadTrackData(trackfile):
    """
    Read a netcdf-format track file into a collection of
    :class:`Track` objects. The returned :class:`Track` objects *must*
    have all attributes accessed by the `__getattr__` method.

    :param str trackfile: track data filename (netCDF4 format).

    :return: track data
    :rtype: list of :class:`Track` objects

    """

    track_dtype = np.dtype({'names':TCRM_COLS,
                            'formats':TCRM_FMTS})
    try:
        ncobj = Dataset(trackfile, mode='r')
    except (IOError, RuntimeError):
        log.exception("Cannot open {0}".format(trackfile))
        raise IOError("Cannot open {0}".format(trackfile))

    g = ncobj.groups
    if not bool(g):
        # We have a track file that stores data in separate variables
        print(f"Reading data from a single track file")
        dt = ncobj.variables['Datetime']
        units = ncobj.getncattr('time_units')
        calendar = ncobj.getncattr('calendar')
        dtt = num2date(dt[:], units, calendar)
        newtd = np.zeros(len(dtt), dtype=track_dtype)
        for f in ncobj.variables.keys():
            if f != 'Datetime' and f in track_dtype.names:
                newtd[f] = ncobj.variables[f][:]
        newtd['Datetime'] = dtt
        track = Track(newtd)
        track.trackfile = trackfile
        track.trackId = eval(ncobj.trackId)

        return [track]

    tracks = []
    if "tracks" in g.keys():
        tgroup = g['tracks'].groups
        ntracks = len(tgroup)
        for i, (t, data) in enumerate(tgroup.items()):
            # log.debug("Loading data for {0}".format(t))
            track_data = data.variables['track'][:]

            try: 
                dt = num2date(track_data['Datetime'],
                              data.variables['time'].units,
                              data.variables['time'].calendar)
            except AttributeError:
                # log.exception(TRACK_DT_ERR)
                raise AttributeError

            newtd = np.zeros(len(track_data), dtype=track_dtype)
            for f in track_data.dtype.names:
                if f != 'Datetime' and f in track_dtype.names:
                    newtd[f] = track_data[f]
            newtd['Datetime'] = dt

            track = Track(newtd)
            track.trackfile = trackfile
            if hasattr(data.variables['track'], "trackId"):
                track.trackId = eval(data.variables['track'].trackId)
            else:
                track.trackId = (i+1, ntracks)
            tracks.append(track)

    else:
        print(TRACK_EMPTY_GROUP.format(trackfile))

    ncobj.close()
    return tracks

def recdropfields(rec, names):
    names = set(names)
    newdtype = np.dtype([(name, rec.dtype[name]) for name in rec.dtype.names
                       if name not in names])

    newrec = np.recarray(rec.shape, dtype=newdtype)
    for field in newdtype.names:
        newrec[field] = rec[field]

    return newrec

def mytracks2line(tracks, outputFile, dissolve=False):
    """
    Writes tracks to a shapefile as a collection of line features

    If dissolve==True, then each track feature is written as a
    single polyline feature, otherwise each track segment is
    stored as a separate feature.

    :type  tracks: list of :class:`Track` objects
    :param tracks: :class:`Track` features to store in a shape file

    :type  outputFile: str
    :param outputFile: Path to output file destination

    :type  dissolve: boolean
    :param dissolve: Store track features or track segments.

    :raises: :mod:`shapefile.ShapefileException` if there is an error
             when attempting to save the file.
    """
    sf = shapefile.Writer(shapefile.POLYLINE)
    sf.fields = TCRMFIELDS

    for track in tracks:
        track.data = recdropfields(track.data, ['Datetime'])
        if dissolve:
            if len(track.data) > 1:
                dlon = np.diff(track.Longitude)
                if dlon.min() < -180:
                    # Track crosses 0E longitude - split track
                    # into multiple parts:
                    idx = np.argmin(dlon)
                    parts = []
                    lines = zip(track.Longitude[:idx],
                                 track.Latitude[:idx])

                    parts.append(lines)
                    lines = zip(track.Longitude[idx+1:],
                                 track.Latitude[idx+1:])

                    parts.append(lines)
                    sf.line(parts)
                else:
                    lines = zip(track.Longitude, track.Latitude)
                    sf.line([lines])
            else:
                lines = zip(track.Longitude, track.Latitude)
                sf.line([lines])


            minPressure = track.trackMinPressure
            maxWind = track.trackMaxWind

            age = track.TimeElapsed.max()

            startYear = track.Year[0]
            startMonth = track.Month[0]
            startDay = track.Day[0]
            startHour = track.Hour[0]
            startMin = track.Minute[0]
            record = [track.CycloneNumber[0], startYear, startMonth, startDay,
                      startHour, startMin, age, minPressure, maxWind]
            sf.record(*record)

        else:
            if len(track.data) == 1:
                line = [[[track.Longitude, track.Latitude],
                        [track.Longitude, track.Latitude]]]
                sf.line(line)
                sf.record(*track.data[0])
            else:
                for n in range(len(track.data) - 1):
                    dlon = track.Longitude[n + 1] - track.Longitude[n]
                    if dlon < -180.:
                        # case where the track crosses 0E:
                        segment = [[[track.Longitude[n], track.Latitude[n]],
                                    [track.Longitude[n], track.Latitude[n]]]]
                    else:
                        segment = [[[track.Longitude[n],
                                     track.Latitude[n]],
                                    [track.Longitude[n + 1],
                                     track.Latitude[n + 1]]]]
                    sf.line(segment)
                    sf.record(*track.data[n])

                # Last point in the track:
                sf.line([[[track.Longitude[n + 1],
                           track.Latitude[n + 1]],
                              [track.Longitude[n + 1],
                               track.Latitude[n + 1]]]])
                sf.record(*track.data[n+1])

    try:
        sf.save(outputFile)
    except shapefile.ShapefileException:
        print("Cannot save shape file: {0}".format(outputFile))
        raise

def tracks2point(tracks, outputFile):
    """
    Writes tracks to a shapefile as a collection of point features.

    :type  tracks: list of :class:`Track` objects
    :param tracks: :class:`Track` features to store in a shape file

    :param str outputFile: Path to output file destination

    :raises: :mod:`shapefile.ShapefileException` if there is an error
             when attempting to save the file.

    """
    # LOG.info("Writing point shape file: {0}".format(outputFile))
    sf = shapefile.Writer(shapefile.POINT)
    sf.fields = TCRMFIELDS

    # LOG.debug("Processing {0} tracks".format(len(tracks)))

    for track in tracks:
        # track.data = recdropfields(track.data, ['Datetime'])
        for lon, lat, rec in zip(track.Longitude, track.Latitude, track.data):
            sf.point(lon, lat)
            sf.record(*rec)

    try:
        sf.save(outputFile)
    except shapefile.ShapefileException:
        # LOG.exception("Cannot save shape file: {0}".format(outputFile))
        raise

    return

def add_field(a, descr):
    if a.dtype.fields is None:
        raise ValueError ("`A' must be a structured numpy array")
    b = np.empty(a.shape, dtype=a.dtype.descr + descr)
    for name in a.dtype.names:
        b[name] = a[name]
    return b

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-id', '--track_id')
args = parser.parse_args()
trackId = args.track_id

# trackId= "005-06282"

trackNum, trackYear = int(trackId.split('-')[0]), int(trackId.split('-')[1])  

trackfileloc = "/g/data/w85/QFES_SWHA/tracks"

shpfileout = os.path.join('/g/data/w85/QFES_SWHA/wind/regional', trackId, 'tracks')
#shpfileout = os.path.join("/home/547/cxa547/tmp/", trackId, "tracks")
if not os.path.isdir(shpfileout):
    os.makedirs(shpfileout)

#For tracks pulled of THREDDS (e.g. http://dapds00.nci.org.au/thredds/fileServer/fj6/TCRM/TCHA18/tracks/tracks.04697.nc)
# track_file = os.path.join(trackfileloc, 'tracks.{0}.nc'.format(trackId.rpartition("-")[2]))

#For individual track .nc files
track_file = os.path.join(trackfileloc, 'track.{0}.nc'.format(trackId))

tracks = ncReadTrackData(track_file)
     
for track in tracks:
    if track.CycloneNumber[0] == trackNum:

        track.data = add_field(track.data, [('Year', int), ('Month', int),
                                                    ('Day', int), ('Hour', int),
                                                    ('Minute', int), ('Category', int)])

        i = 0
        for rec in track.data:
            rec['Year'] = int(track.Datetime[i].strftime('%Y'))
            rec['Month'] = int(track.Datetime[i].strftime('%m'))
            rec['Day'] = int(track.Datetime[i].strftime('%d'))
            rec['Hour'] = int(track.Datetime[i].strftime('%H'))
            rec['Minute'] = int(track.Datetime[i].strftime('%M'))
            if rec["CentralPressure"] < 930:
                Cat = 5  
            elif rec["CentralPressure"] < 955:
                Cat = 4
            elif rec["CentralPressure"] < 970:
                Cat = 3
            elif rec["CentralPressure"] < 985:
                Cat = 2
            elif rec["CentralPressure"] < 999:
                Cat = 1
            else:
                Cat = 0

            rec['Category'] = Cat
            # Comment out this line if the track doesn't cross the dateline.
            #rec['Longitude'] = rec['Longitude']- 360.
            i+=1

        track.data = recdropfields(track.data, ['Datetime'])


        line_shpfile = os.path.join(shpfileout, 'track.{0}.line.shp'.format(str(trackId)))
        line_prjfile = os.path.join(shpfileout, 'track.{0}.line.prj'.format(str(trackId)))
        mytracks2line([track], line_shpfile)
        # mytracks2line([track], line_shpfile, dissolve=True)

        pt_shpfile = os.path.join(shpfileout, 'track.{0}.point.shp'.format(str(trackId)))
        pt_prjfile = os.path.join(shpfileout, 'track.{0}.point.prj'.format(str(trackId)))
        tracks2point([track], pt_shpfile)

        prjwkt = "GEOGCS['GCS_GDA_1994',DATUM['D_GDA_1994',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        
        prjfh_l = open(line_prjfile, 'w')
        prjfh_l.write(prjwkt)
        prjfh_l.close()

        prjfh_p = open(pt_prjfile, 'w')
        prjfh_p.write(prjwkt)
        prjfh_p.close()
