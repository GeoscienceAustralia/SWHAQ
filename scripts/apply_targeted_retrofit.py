"""
This code is used to assign retrofit
functions to buildings based on the vulnerability
model currently assigned to them.

retrofit_percent can be changed to whatever rate of
retrofit uptake is required.
"""

import os
import pandas as pd

# read in exposure data
datapath = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\exposure\2021"
filename = "SEQ_ResidentialExposure_NEXIS_2021_M4_updated_v2.csv"
df = pd.read_csv(os.path.join(datapath, filename))
df.drop(['Unnamed: 0', 'MB_CAT', 'SA3_CODE', 'SA3_NAME', 'SA4_CODE',
         'SA4_NAME', 'UCL_CODE', 'UCL_NAME', 'GCC_CODE', 'GCC_NAME',
         'POSTCODE', 'CONSTRUCTION_TYPE', 'CONTENTS_VALUE',
         'WIND_VULNERABILITY_MODEL_NUMBER', 'M42'], axis=1, inplace=True)
# read in retrofit eligability data
datapath2 = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u12161\retrofit"
filename2 = "targeted_retrofit_eligibility.csv"
df2 = pd.read_csv(os.path.join(datapath2, filename2),)
df2.set_index(["SA2_MAIN16"], inplace=True)

# merge df and df2
# Rather than an inner join, we use an outer join to merge the dataframes
# - this covers the situation where there are duplicate
# SA2_MAIN16 values in the eligibility data.
df_retro = pd.merge(df, df2[["Targeted_Retrofit"]], 
                    left_on=["SA2_CODE"],
                    right_index=True,
                    how="outer",
                    sort=False)
df_retro = df_retro.sort_values("Targeted_Retrofit").drop_duplicates()
df_retro = df_retro[~df_retro['Targeted_Retrofit'].isna()]

retrofit_percent_new = 0.113
retrofit_percent_old = 0.819

# Set some aliases for column names to make the code easier to read
WVC = 'WIND_VULNERABILITY_FUNCTION_ID'
ACC = 'AS4055_CLASS'
TRC = 'Targeted_Retrofit'

# legacy buildings original vuln functions: retrofit functions (windows)
# dic_old_RF1 = {
#    'dw350': 'dw450',
#    'dw351': 'dw451',
#    'dw352': 'dw452',
# }

# legacy buildings original vuln functions: retrofit functions (structural)
# dic_old_RF2 = {
#    'dw350': 'dw550',
#    'dw351': 'dw551',
#    'dw352': 'dw552',
#  }

# legacy buildings original vuln functions: retrofit functions (wind and struc)
dic_old_RF3 = {
    'dw350': 'dw650',
    'dw351': 'dw651',
    'dw352': 'dw652',
}

# modern buildings original vuln functions: retrofit functions (windows)
dic_new = {
    'dw353': 'dw453',
    'dw354': 'dw454',
    'dw355': 'dw455',
    'dw356': 'dw456',
    'dw357': 'dw457',
    'dw358': 'dw458',
    'dw359': 'dw459',
    'dw360': 'dw460',
    'dw361': 'dw461',
    'dw362': 'dw462',
    'dw363': 'dw463',
    'dw364': 'dw464',
}

rc1 = ["Eligible"]
rc2 = ["N3", "N4"]

# create a list of the current vuln function so that the can be used
# to find buildings assigned these functions
# list_old_RF1 = list(dic_old_RF1.keys())
# list_old_RF2 = list(dic_old_RF2.keys())
list_old_RF3 = list(dic_old_RF3.keys())
list_new = list(dic_new.keys())
list_retrofit = list(rc1)
list_retrofit2 = list(rc2)

for i in range(10):
    df_retro = pd.merge(df, df2[[TRC]],
                        left_on=["SA2_CODE"],
                        right_index=True,
                        how="outer",
                        sort=False)
    df_retro = df_retro.sort_values(TRC).drop_duplicates()
    df_retro = df_retro[~df_retro[TRC].isna()]

    # find relevent buildings and sample a percent of them (retrofit_percent)
    df_new = df_retro[(df_retro[TRC].isin(rc1)) &
                      (df_retro[ACC].isin(rc2)) &
                      (df_retro[WVC].isin(list_new))]
    df_new = df_new.sample(frac=retrofit_percent_new)

    # three retrofit options with equal probability
    # df_old_RF1 = df_retro[(df_retro['Targeted_Retrofit'].isin(list_retrofit))]
    # df_old_RF1 = df_old_RF1[(df_old_RF1['Wind_func'].isin(list_old_RF1))]
    # df_old_RF1 = df_old_RF1.sample(frac=(retrofit_percent_old/3))

    # df_old_RF2 = df_retro[(df_retro['Targeted_Retrofit'].isin(list_retrofit))]
    # df_old_RF2 = df_old_RF2[(df_old_RF2['Wind_func'].isin(list_old_RF2))]
    # df_old_RF2 = df_old_RF2.sample(frac=(retrofit_percent_old/3))

    df_old_RF3 = df_retro[(df_retro[TRC].isin(rc1)) &
                          (df_retro[ACC].isin(rc2)) &
                          (df_retro[WVC].isin(list_old_RF3))]
    df_old_RF3 = df_old_RF3.sample(frac=(retrofit_percent_old))



    # change original vuln func to retrofit vuln func for the selected
    # retrofit_percent
    df_new[WVC] = df_new[WVC].map(dic_new)
    # df_old_RF1['Wind_func'] = df_old_RF1['Wind_func'].map(dic_old_RF1)
    # df_old_RF2['Wind_func'] = df_old_RF2['Wind_func'].map(dic_old_RF2)
    df_old_RF3[WVC] = df_old_RF3[WVC].map(dic_old_RF3)

    # overwrite the original datafrom with the retrofitted buildings
    df_retro.update(df_new)
    # df_retro.update(df_old_RF1)
    # df_retro.update(df_old_RF2)
    df_retro.update(df_old_RF3)

    # save
    outputfile = f"targeted_retrofit.{i:03d}.csv"
    df_retro.to_csv(os.path.join(datapath2, outputfile))
