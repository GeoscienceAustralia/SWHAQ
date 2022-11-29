"""
update_as4055_class.py - update the AS4055 classification for an exposure
    dataset

The origina scenarios included the N1 AS4055 site classification for
a large number of buildings. This was not correct, but there were other
anomalies as well for other site classifications (N3 and above).

To ensure consistency of the AS4055 classification between the original
("baseline") scenarios and a virtual retrofit, we merge the updated AS4055
classification from the most recent exposure data onto the exposure data
used for the previous scenario analyses.

This should be run prior to running the `run_retrofit_event.sh` job script
to ensure data is updated.

Author: Craig Arthur
Date: 2022-11-29

"""

import pandas as pd
df_old = pd.read_csv("/g/data/w85/QFES_SWHA/exposure/2021/SEQ_ResidentialExposure_NEXIS_2021_M4_updated_v2.csv")
df_new = pd.read_csv("/g/data/w85/QFES_SWHA/exposure/2022/SEQ_Residential_Wind_Exposure_2021_TCRM_2022_VulnCurves_AS4055_M4_updated.csv")
LGAs_6 = ['Noosa (S)', 'Sunshine Coast (R)', 'Moreton Bay (R)',
          'Brisbane (C)', 'Gold Coast (C)', 'Redland (C)']
LGAs = df_new[df_new['LGA_NAME'].isin(LGAs_6)]
LGAs = LGAs.drop_duplicates(subset=['LGA_NAME'])
LGAs = LGAs.reset_index()
LGAs = LGAs.drop(['SA1_CODE'],axis=1)
LGA_codes = LGAs[['LGA_CODE', 'LGA_NAME']].set_index('LGA_CODE')

df_old[df_old['LGA_CODE'].isin(LGA_codes.index)].groupby(['LGA_CODE', 'AS4055_CLASS']).count()['LID']
df_new[df_new['LGA_CODE'].isin(LGA_codes.index)].groupby(['LGA_CODE', 'AS4055_CLASS']).count()['LID']
df_old = df_old[df_old.LGA_CODE.isin(LGA_codes.index)]
df_new = df_new[df_new.LGA_CODE.isin(LGA_codes.index)]

new_lid = pd.DataFrame(df_new[['LID', 'AS4055_CLASS']])

updated_df = df_old.merge(new_lid, how='outer', on='LID', suffixes=("_old", '_new'))
updated_df.drop('AS4055_CLASS_old', inplace=True, axis=1)
updated_df.rename({'AS4055_CLASS_new':'AS4055_CLASS'}, inplace=True, axis=1)

updated_df.groupby(['LGA_CODE', 'AS4055_CLASS']).count()

df_new[df_new['LGA_CODE'].isin(LGA_codes.index)].groupby(['LGA_CODE', 'AS4055_CLASS']).count()

updated_df.to_csv('/g/data/w85/QFES_SWHA/exposure/2022/SEQ_Residential_Wind_Exposure_2021_TCRM_2022_VulnCurves_AS4055_SA1_2021.csv')