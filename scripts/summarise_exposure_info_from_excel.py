import os
import logging
import numpy as np
import pandas as pd
import re
from builtins import str
import pdb

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)

    
COLUMNS = {
    "Number of people": ['population_count'],
    "Number of residential builldings": ['building_count'],
    "Number of commercial buildings": ['commercial_building_count'],
    "Number of industrial buildings": ['industrial_building_count'],
    "Number of emergency facilities": ['police_station', 
                                       'ambulance_station',
                                       'fire_station',
                                       'ses_facility',
                                       'emergency_management_facilities'],
    "Number of health facilities": ['hospital_public',
                                    'hospital_private',
                                    'nursing_home',
                                    'retirement_home'],
    "Airports": ['airport_major_areas', 
                 'airport_landing_grounds'],
    "Number of school facilities": ['school_pre_primary',
                                    'school_secondary',
                                    'school_tertiary',
                                    'school_other'],
    "Length of major roads (km)": ['roads_major_kms',
                                   'roads_arterial_and_sub_arterial_kms'],
    "Length of railway lines (km)": ['railway_tracks_kms'],
    "Length of electricity transmission Lines (km)": ['transmission_electricity_lines_kms']
          }

dir = r"C:\WorkSpace\swhaq\data\exposure\reports"
outputdir = r"C:\WorkSpace\swhaq\data\exposure\summary"
regex = '(\w+)_Cat_(\d)_(\d{3}-\d{5})_local_wind\.xls'
nameCheck = re.compile(regex)
fileList = []
uniqueNameList = []
index = pd.RangeIndex(1,6)
for f in os.listdir(dir):
    if nameCheck.search(f):
        logging.info(f)
        fileList.append(os.path.join(dir, f))
        m = re.match(regex, f)
        logging.info(f"Processing a {m.group(2)} TC for {m.group(1)} (event id: {m.group(3)})")
        df = pd.read_excel(os.path.join(dir, f))
        df.set_index('category', inplace=True)
        pdb.set_trace()
        newdf = pd.DataFrame()
        for k in COLUMNS:
            newdf[k] = df[COLUMNS[k]].sum(axis=1)
        newdf.sort_index(inplace=True)
        odf = pd.DataFrame(index=index, columns=newdf.columns)
        for i in range(1, 6):
            if i in newdf.index:
                print(newdf.loc[i])
                odf.loc[i] = newdf.loc[i]
            #else:
            #    odf.append(pd.Series(), ignore_index=True)

        odf.T.to_excel(os.path.join(outputdir, f))
