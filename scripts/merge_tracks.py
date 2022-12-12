#!/bin/python3
"""
merge_tracks.py - merge (bias-corrected) TCLV track datasets into two groups

The individual TCLV datasets are merged into two ensembles. The groups are
hard-coded here, but could readily be updated as needed. 

Author: Craig Arthur
Date: 2022-11-30
"""
from os.path import join as pjoin
from datetime import datetime
from pathlib import Path
import pandas as pd

TIMES = ["1981-2010","2021-2040","2041-2060","2061-2080","2081-2100"]

EMISSION_SCENARIOS = ["RCP45","RCP85"]

GROUPS = {
        'GROUP1': ["ACCESS1-3Q","CSIRO-Mk3-6-0Q","GFDL-ESM2MQ","HadGEM2Q","MIROC5Q"],
        'GROUP2': ["ACCESS1-0Q","CCSM4Q","CNRM-CM5Q","GFDL-CM3Q","MPI-ESM-LRQ","NorESM1-MQ"]
}

INPUT_FOLDER = Path(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\TCLV\tracks\corrected\20211124")
OUTPUT_FOLDER = Path(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\TCLV\tracks\ensemble\20211124")


def belongs(group, emission_scenario, time, f):
    """
    Determine if a given file name matches the required group, emission scenario
    and time period combination.

    :param list group: List of ensemble member names
    :param str emission_scenario: Either "RCP45" or "RCP85"
    :param str time: A string like "2021-2040"
    :param f: `str` or `Path` object representing the file

    :returns: :class:`bool` - True if it matches, False otherwise
    """
    try:
        g, es, t, *_ = f.stem.split('_')
    except ValueError as verr:
        # Handle case of a path listing that's not a file of the correct
        # name structure
        print(verr)
        return False

    if g not in GROUPS[group]:
        return False
    if es != emission_scenario:
        return False
    if t == 'bc':
        return time == TIMES[0]
    return t == time


def find_missing():
    """
    Redundant function
    """
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
    """
    Given a list of ensemble members, the emission scenario and the time period,
    merge all the relevant files into a single file. The function loops over all
    files in the `INPUT_FOLDER`, evaluates if it belongs to the group based on
    the list of members, emission scenario and time period (this info is
    contained in the file name). If it belongs in the ensemble, then it reads
    the data, does some manipulation of the dates and finally writes the full
    ensemble to a csv file. 

    :param list group: List of ensemble member names
    :param str emission_scenario: Either "RCP45" or "RCP85"
    :param str time: A string like "2021-2040"
    """

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
