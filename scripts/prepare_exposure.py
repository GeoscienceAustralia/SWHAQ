"""
prepare_exposure.py

This script reads in a NEXIS TCRM exposure file, and assigns a vulnerability
function based on the supplied suite of curves from JCU CTS and VRMS. 

To do this, we first assign a nominal site classification based on AS 4055
(i.e. N1-N6 and C1-C4) to each building. The values used for defining the site
classification are taken from GA's site exposure product
(http://pid.geoscience.gov.au/dataset/ga/145891). The values in that dataset
were determined using definitions in AS/NZS 1170.2 (2011), which are (largely)
the same as for AS 4055. 

Once the AS4055 classification is complete, a combination of that class, the
roof type and construction era are used to set the vulnerability function. 

The mapping of (AS4055 class, roof type, construction era) to vulnerability
function is set out in a spreadsheet supplied by JCU CTS and VRMS (Martin
Wehner [GA], David Henderson [JCU CTS]).

We only address region B buildings, and then only building stock commonly
found in southeast Queensland. Arguably this script could be used to assign
curves to other regional building stock (e.g. north Queensland), but that would
require updating the `curvemap` dict with appropriate mappings. The building 
attributes may also be different from those used here.

Finally, this is a hack. A more robust technique that is built into the 
NEXIS TCRM extraction process (Location Information Section) is being
considered. 

Contact:
Craig Arthur
2022-02-22 ;)

"""

import os
import pandas as pd

def buildingClass(df, classes, thresholds, AS1170='C'):
    """
    Assign a site classification (AS4055) based on wind loading region 
    (AS1170.2) and local site multiplier value ('M4')

    :param df: :class:`pd.DataFrame` containing exposure data, with minimum set
        of attributes in the list ['WIND_REGION_CLASSIFCATION', 'AS4055_CLASS',
        'M4']
    :param list classes: Labels to apply to each category
    :param list thresholds: Values that define the categories
    :param str AS1170: AS/NZS 1170.2 wind region. 

    :NOTE: the label for the wind region classification in some versions of the
        NEXIS TCRM files omits an 'I' in 'CLASSIFICATION'. Check the attribute
        names!

    """
    df.loc[df['WIND_REGION_CLASSIFCATION'] == AS1170, 'AS4055_CLASS'] = \
        pd.cut(df[df['WIND_REGION_CLASSIFCATION']==AS1170]['M4'],
               bins=thresholds,
               right=True,
               labels=classes)
    return df
    
datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\exposure\2021"
filename = "SEQ_ResidentialExposure_NEXIS_2021_M4.csv"
df = pd.read_csv(os.path.join(datapath, filename), low_memory=False)

# Set any data < 0 to default value - assume N2 classification
df.loc[df['M4'] < 0., 'M4'] = 0.8
#df.drop('M42', axis=1, inplace=True)

# Assign AS4055 classes - overwrite existing data!!!
thresholds = [0.0, 0.8109, 1.0063, 1.2209, 1.4334, 2.]
classes = ['N2', 'N3', 'N4', 'N5', 'N6']

# Only working with Region B in this case. If there's any region A buildings, we leave them alone.
df = buildingClass(df, classes, thresholds, 'B')



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

# Buggered if I know why this can't be more compact, but anyway. 
# This just reverts the MultiIndex back to columns in the dataframe
df2 = df2.reset_index([1, 2]).reset_index()

### Now do the legacy buildings:
df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) & \
        df2.ROOF_TYPE.isin(['Metal Sheeting', 'Fibro / asbestos cement sheeting']) & \
        df2.WALL_TYPE.isin(['Brick Veneer', 'Double Brick']), 'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw352'

df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) &
       (df2.ROOF_TYPE=='Tiles'), 
       'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw351'

df2.loc[~df2.YEAR_BUILT.isin(['1997 - present', '1982 - 1996']) &
       df2.ROOF_TYPE.isin(['Metal Sheeting', 'Fibro / asbestos cement sheeting']) & 
       df2.WALL_TYPE.isin(['Timber', 'Fibro / asbestos cement sheeting']),
       'WIND_VULNERABILITY_FUNCTION_ID'] = 'dw350'

df2['TMPFUNC'] = df2.apply(lambda x: f"dw{x.WIND_VULNERABILITY_MODEL_NUMBER}", axis=1)
df2.WIND_VULNERABILITY_FUNCTION_ID.fillna(df2.TMPFUNC, inplace=True)
df2.drop('TMPFUNC', axis=1, inplace=True)


outputfile ="SEQ_ResidentialExposure_NEXIS_2021_M4_updated_v2.csv"
df2.to_csv(os.path.join(datapath, outputfile))
