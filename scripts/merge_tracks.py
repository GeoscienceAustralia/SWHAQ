#!/bin/python3

from os.path import join as pjoin
import csv
from dateutil.parser import parse
from datetime import datetime
from pathlib import Path
import pandas as pd

TIMES = ["1981-2010","2021-2040","2041-2060","2061-2080","2081-2100"]

EMISSION_SCENARIOS = ["RCP45","RCP85"]

GROUPS = {
        'GROUP1': ["ACCESS1-3Q","CSIRO-Mk3-6-0Q","GFDL-ESM2MQ","HadGEM2Q","MIROC5Q"],
        'GROUP2': ["ACCESS1-0Q","CCSM4Q","CNRM-CM5Q","GFDL-CM3Q","MPI-ESM-LRQ","NorESM1-MQ"]
}

INPUT_FOLDER = Path('C:/WorkSpace/data/tclv/tracks/corrected/20200622')
OUTPUT_FOLDER = Path('C:/WorkSpace/data/tclv/tracks/corrected/20200828')


def belongs(group, emission_scenario, time, f):
    g, es, t, *_ = f.stem.split('_')

    if g not in GROUPS[group]:
        return False
    if es != emission_scenario:
        return False
    if t == 'bc':
        return time == TIMES[0]
    return t == time


def find_missing():
    for f in INPUT_FOLDER.iterdir():
        found = False

        for group in GROUPS:
            for emission_scenario in EMISSION_SCENARIOS:
                for time in TIMES:
                    if belongs(GROUPS[group], emission_scenario, time, f):
                        found = True
        
        if not found:
            print(f)


def merge_tracks(group, emission_scenario, time):
    output_file = '{}_{}_{}.dat'.format(group, emission_scenario, time)
    HEADER = None

    start_time, end_time = time.split('-')
    inc = int(end_time) - int(start_time) + 1
    timeinc = 0
    start_time = datetime(int(start_time), 1, 1)
    end_time = datetime(int(end_time) + 1, 1, 1)

    # Empty list to store the dataframes as they are loaded
    alltracks = []

    for f in INPUT_FOLDER.iterdir():
        if belongs(group, emission_scenario, time, f):
            df = pd.read_csv(f)
            df['datetime'] = pd.to_datetime(df.datetime) + pd.offsets.DateOffset(years=timeinc)
            df['year'] += timeinc
            alltracks.append(df)
            timeinc += inc
        else:
            pass

    outdf = pd.concat(alltracks)
    outdf.to_csv(pjoin(OUTPUT_FOLDER, output_file),index=False)

if __name__ == '__main__':
    for group in GROUPS:
        for emission_scenario in EMISSION_SCENARIOS:
            for time in TIMES:
                merge_tracks(group, emission_scenario, time)
