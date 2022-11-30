"""
retrofit_impact_analysis.py - simple categorisation of lower/median/upper damage index values,
    based on multiple retrofit simulations for a single TC event (scenario)

Pass the event id number as a command line argument:

$ python retrofit_impact_analysis.py 004-08495

Generates three CSV files that contain aggregated counts of buildings in damage
states for each LGA. 

Author: Craig Arthur
Date: 2022-11-30
"""


import os
import sys
import pandas as pd
eventid = sys.argv[1]
inputPath = f"/g/data/w85/QFES_SWHA/impact/RETROFIT/{eventid}"
inputFile = os.path.join(inputPath, "quantiles.csv")
LGA_NAMES = ['Brisbane', 'Gold Coast', 'Moreton Bay',
             'Redland', 'Sunshine Coast', 'Noosa']
LGA_CODES = [31000, 33430, 35010, 36250, 36720, 35740]
LGAs = pd.DataFrame(data={"LGA_CODE": LGA_CODES,
                          "LGA_NAME": LGA_NAMES})

bins=[0.00, 0.02, 0.1, 0.2, 0.5, 1.0]
labels=['Negligible', 'Slight', 'Moderate', 'Extensive', 'Complete']

df = pd.read_csv(inputFile)
df = df[df.LGA_CODE.isin(LGA_CODES)]

df['Median damage state'] = pd.cut(df['0.5'], bins, right=True, labels=labels)
df['Lower damage state'] = pd.cut(df['0.05'], bins, right=True, labels=labels)
df['Upper damage state'] = pd.cut(df['0.95'], bins, right=True, labels=labels)

df.pivot_table(index='LGA_NAME', columns='Median damage state', aggfunc='size', fill_value=0).\
to_csv(os.path.join(inputPath, f"{eventid}_med_damage_state.csv"))

df.pivot_table(index='LGA_NAME', columns='Lower damage state', aggfunc='size', fill_value=0).\
to_csv(os.path.join(inputPath, f"{eventid}_lower_damage_state.csv"))

df.pivot_table(index='LGA_NAME', columns='Upper damage state', aggfunc='size', fill_value=0).\
to_csv(os.path.join(inputPath, f"{eventid}_upper_damage_state.csv"))