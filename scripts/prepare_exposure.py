import os
import pandas as pd
datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\exposure\2021"
filename = "SEQ_ResidentialExposure_NEXIS_2021_M4.csv"
df = pd.read_csv(os.path.join(datapath, filename))

# Set any data < 0 to default value - assume N2 classification
df.loc[df['M41'] < 0., 'M41'] = 0.8
df.drop('M42', axis=1, inplace=True)

# Assign AS4055 classes - overwrite existing data!!!
thresholds = [0.0, 0.747, 0.8278, 0.973, 1.147, 1.3412, 2.]
classes = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']
df['AS4055_CLASS'] = pd.cut(df['M41'], bins=thresholds, right=True, labels=classes)


# THIS ONLY COVERS A LIMITED SET OF ROOF AND WALL TYPES OBSERVED IN THE DATA
# ALSO EXCLUDES pre-1980's CONSTRUCTION
curvemap = {
    ('N1', 'Metal Sheeting', '1997 - present'): 'dw353',
    ('N2', 'Metal Sheeting', '1997 - present'): 'dw354',
    ('N3', 'Metal Sheeting', '1997 - present'): 'dw355',
    ('N4', 'Metal Sheeting', '1997 - present'): 'dw356',
    ('N5', 'Metal Sheeting', '1997 - present'): 'dw357',
    ('N6', 'Metal Sheeting', '1997 - present'): 'dw358',
    ('N1', 'Tiles', '1997 - present'): 'dw359',
    ('N2', 'Tiles', '1997 - present'): 'dw360',
    ('N3', 'Tiles', '1997 - present'): 'dw361',
    ('N4', 'Tiles', '1997 - present'): 'dw362',
    ('N5', 'Tiles', '1997 - present'): 'dw363',
    ('N6', 'Tiles', '1997 - present'): 'dw364',
    ('N1', 'Metal Sheeting', '1982 - 1996'): 'dw353',
    ('N2', 'Metal Sheeting', '1982 - 1996'): 'dw354',
    ('N3', 'Metal Sheeting', '1982 - 1996'): 'dw355',
    ('N4', 'Metal Sheeting', '1982 - 1996'): 'dw356',
    ('N5', 'Metal Sheeting', '1982 - 1996'): 'dw357',
    ('N6', 'Metal Sheeting', '1982 - 1996'): 'dw358',
    ('N1', 'Tiles', '1982 - 1996'): 'dw359',
    ('N2', 'Tiles', '1982 - 1996'): 'dw360',
    ('N3', 'Tiles', '1982 - 1996'): 'dw361',
    ('N4', 'Tiles', '1982 - 1996'): 'dw362',
    ('N5', 'Tiles', '1982 - 1996'): 'dw363',
    ('N6', 'Tiles', '1982 - 1996'): 'dw364',
        
}


df2 = df.set_index(['AS4055_CLASS', 'ROOF_TYPE', 'YEAR_BUILT'])
df2['idx'] = df2.index
df2['WIND_VULNERABILITY_FUNCTION_ID'] = df2['idx'].map(curvemap)
df2.drop('idx', axis=1, inplace=True)

# Buggered if I know why this can't be more compact, but anyway
df2 = df2.reset_index([1, 2]).reset_index()

### Now do the legacy buildings:
df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) &
       (df2.ROOF_TYPE=='Metal Sheeting') & 
       (df2.WALL_TYPE=='Brick Veneer'), 'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw352'

df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) &
       (df2.ROOF_TYPE=='Tiles') & 
       (df2.WALL_TYPE=='Brick Veneer'), 'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw351'

df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) &
       (df2.ROOF_TYPE=='Metal Sheeting') & 
       (df2.WALL_TYPE=='Timber'), 'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw350'

df2['TMPFUNC'] = df2.apply(lambda x: f"dw{x.WIND_VULNERABILITY_MODEL_NUMBER}", axis=1)
df2.WIND_VULNERABILITY_FUNCTION_ID.fillna(df2.TMPFUNC, inplace=True)
df2.drop('TMPFUNC', axis=1, inplace=True)


outputfile ="SEQ_ResidentialExposure_NEXIS_2021_M4_updated.csv"
df2.to_csv(os.path.join(datapath, outputfile))


