#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import numpy as np
import seaborn as sns

import pdb
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-p', '--path', help="Input datafile path")
parser.add_argument('-r', '--region', help="Region: NQ=North Queensland, GC=Gold Coast")
args = parser.parse_args()
inputfile = args.path
region = args.region

NQ = False
GC = False
if region == 'NQ': NQ = True
if region == 'GC': GC = True





#inputfile = "C:/WorkSpace/data/qfes/exposure/Townsville_ResidentialExposure_NEXISV10_M4.csv"

# Set this to true to do some additional detailed mapping of building types to 
# curves, specific for the community 
localise = True
df = pd.read_csv(inputfile, sep=",",header=0, index_col=0, skipinitialspace=True)

# Filter out records that do not have an M4 value. 
df = df[df['M4'].notnull()]
df.info()


def buildingClass(df, classes, thresholds, AS1170='C'):

    for thres, cls in zip(thresholds, classes):
        idx = np.where((df['M4'] >= thres) & (df['WIND_REGION_CLASSIFCATION'] == AS1170))[0]
        df['AS4055_CLASS'][idx] = cls
        
    return df


# Apply a basic AS4055 class, based on the M4 value
thresholds = [-99999., 0.0, 0.8413, 1.0018, 1.2668, 1.5997]
classes = ['N2', 'N1', 'N2', 'N3', 'N4', 'N5']
df = buildingClass(df, classes, thresholds, 'A')


thresholds = [0.0, 0.8109, 1.0063, 1.2209, 1.4334]
classes = ['N2', 'N3', 'N4', 'N5', 'N6']
df = buildingClass(df, classes, thresholds, 'B')

# Region C
thresholds = [0.0, 0.833, 1.0141, 1.2428, 1.4692]
classes = ['C1', 'C2', 'C3', 'C4', 'Special']
df = buildingClass(df, classes, thresholds, 'C')

# Region D
thresholds = [0.0, 0.8109, 0.9996, 1.1764]
classes = ['C2', 'C3', 'C4', 'Special']
df = buildingClass(df, classes, thresholds, 'D')


# Start with simply assigning the modern building curve to all buildings, based on AS4055 classification.
# We'll overwrite specific groups at a later point. This is the quick option, since over 2/3rds of the 
# building population in the Cairns region is considered "modern" construction, so should conform 
# to AS4055 (i.e. constructed after 1981)

classes = ['C1', 'C2', 'C3', 'C4']
curves = ['dw317', 'dw318', 'dw319', 'dw320']
filter = df['YEAR_BUILT'].map(lambda x: x not in ['1982 - 1996', '1997 - present'])
for cls, curve in zip(classes, curves):
    idx = np.where(df['AS4055_CLASS'] == cls)[0]
    df['WIND_VULNERABILITY_FUNCTION_ID'][idx] = curve

classes = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']
curves = ['dw309', 'dw310', 'dw311', 'dw312', 'dw313', 'dw314']
filter = df['YEAR_BUILT'].map(lambda x: x not in ['1982 - 1996', '1997 - present'])
for cls, curve in zip(classes, curves):
    idx = np.where(df['AS4055_CLASS'] == cls)[0]
    df['WIND_VULNERABILITY_FUNCTION_ID'][idx] = curve


if NQ:
    # Then work through the other options. Basically, its just a mapping of age, 
    # roof type and wall type combinations to one of two options. 

    # The data provided by JCU indicates a small proportion of buildings with construction era 1947-1952. The NEXIS YEAR_BUILT
    # attribute has mapped this era to 1947-1961. This may generate some anomalies in the analysis. Re-mapping the source
    # construction era to a new grouping in the NEXIS era would likely address this issue

    # None in the Cairns NEXIS TCRM data (would have been mapped to Tile if any exist)
    df['WIND_VULNERABILITY_FUNCTION_ID'][df['ROOF_TYPE']=='Concrete'] = 'dw316'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Fibro / asbestos cement sheeting') & 
                                         (df.YEAR_BUILT.isin(['1947 - 1961', '1962 - 1981']))] = 'dw315'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Fibro / asbestos cement sheeting') &
                                         (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', 
                                                              '1914 - 1946']))] = 'dw316'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Metal Sheeting') & 
                                         (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', 
                                                              '1914 - 1946', '1947 - 1961', 
                                                              '1962 - 1981']))] = 'dw316'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Metal Sheeting') & 
                                         (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', 
                                                              '1914 - 1946'])) & 
                                         (df.WALL_TYPE.isin(['Timber', 
                                                             'Fibro / asbestos cement sheeting']))] = 'dw315'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Tiles') & 
                                         (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', 
                                                              '1914 - 1946', '1947 - 1961', 
                                                              '1962 - 1981']))] = 'dw315'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Tiles') & 
                                         (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', 
                                                              '1914 - 1946'])) &
                                         (df.WALL_TYPE.isin(['Brick Veneer', 'Double Brick']))] = 'dw316'

if GC:
    df['WIND_VULNERABILITY_FUNCTION_ID'][df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913',
                                                             '1914 - 1946','1947 - 1961',
                                                             '1962 - 1981'])] = 'dw310'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Fibro / asbestos cement sheeting') & 
                                        (df.WALL_TYPE.isin(['Fibro / asbestos cement sheeting', 'Timber'])) &
                                        (df.YEAR_BUILT.isin(['1962 - 1981']))] = 'dw309'

    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Metal Sheeting') & 
                                        (df.WALL_TYPE.isin([['Fibro / asbestos cement sheeting', 'Timber']])) &
                                        (df.YEAR_BUILT.isin(['1947 - 1961', '1962 - 1981']))] = 'dw309'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Metal Sheeting') & 
                                        (df.YEAR_BUILT.isin(['1840 - 1890', '1891 - 1913', '1914 - 1946'])) & 
                                        (df.WALL_TYPE.isin(['Timber', 'Fibro / asbestos cement sheeting']))] = 'dw315'
    df['WIND_VULNERABILITY_FUNCTION_ID'][(df.ROOF_TYPE=='Tiles') & 
                                        (df.WALL_TYPE.isin([['Fibro / asbestos cement sheeting', 'Timber']])) &
                                        (df.YEAR_BUILT.isin(['1947 - 1961', '1962 - 1981']))] = 'dw309'

# Do a basic plot of the resulting classification
#sns.countplot(x='AS4055_CLASS', data=df,
#              order=np.sort(df.AS4055_CLASS.unique()))

# Save to a new file

base, ext = os.path.splitext(inputfile)
outputfile = f"{base}_updated{ext}"
df.to_csv(outputfile, index=True)




