#!/bin/python3

import csv
from dateutil.parser import parse
from datetime import datetime
from pathlib import Path

TIMES = ["1981-2010","2021-2040","2041-2060","2061-2080","2081-2100"]

EMISSION_SCENARIOS = ["RCP45","RCP85"]

GROUPS = {
        'GROUP1': ["ACCESS1-3Q","CSIRO-Mk3-6-0Q","GFDL-ESM2MQ","HadGEM2Q","MIROC5Q"],
        'GROUP2': ["ACCESS1-0Q","CCSM4Q","CNRM-CM5Q","GFDL-CM3Q","MPI-ESM-LRQ","NorESM1-MQ"]
}

INPUT_FOLDER = Path('/g/data/w85/QFES_SWHA/hazard/input/tclv/20200622')
OUTPUT_FOLDER = Path('/g/data/w85/QFES_SWHA/hazard/input/tclv/20200622')


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
                    if belongs(groups[group], emission_scenario, time, f):
                        found = True
        
        if not found:
            print(f)


def merge_tracks(group, emission_scenario, time):
    output_file = '{}_{}_{}.dat'.format(group, emission_scenario, time)
    HEADER = None

    start_time, end_time = time.split('-')
    start_time = datetime(int(start_time), 1, 1)
    end_time = datetime(int(end_time) + 1, 1, 1)

    with open(OUTPUT_FOLDER / output_file, 'w') as out:
        writer = csv.writer(out)

        for f in INPUT_FOLDER.iterdir():
            if belongs(group, emission_scenario, time, f):
                with open(f) as fl:
                    reader = csv.reader(fl)
                    header = next(reader)

                    if HEADER is None:
                        HEADER = header
                        writer.writerow(HEADER)

                    elif HEADER != header:
                        raise ValueError('{} is not {}'.format(header, HEADER))

                    for row in reader:
                        t = parse(row[0])
                        if t >= start_time and t < end_time:
                            writer.writerow(row)

if __name__ == '__main__':
    for group in GROUPS:
        for emission_scenario in EMISSION_SCENARIOS:
            for time in TIMES:
                merge_tracks(group, emission_scenario, time)
