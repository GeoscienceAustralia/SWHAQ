# This script takes AAL output that has been aggregated to SA1
# (and was repeated multiple times producing AAL mean and 90% CI)
# and links LGA code to each SA1

import pandas as pd

# import AAL SA1 aggregated data
# and exposure dataset with LGA and SA1 
AAL = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\retro_prob\SA1_CODE_AAL.csv")
Exposure = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\exposure\2022\SEQ_Residential_Wind_Exposure_2021_TCRM_2022_VulnCurves_AS4055_retrofit5_eligible.csv")

# drop all columns in exposure data other than LGA and SA1
Exposure.drop(Exposure.columns.difference(['SA1_CODE','LGA_CODE','LGA_NAME']), axis=1, inplace=True)
# drop any duplicates where SA1 and LGA are the same
Exposure_2 = Exposure.drop_duplicates(['SA1_CODE', 'LGA_CODE'], keep='first')
# a couple of SA1s spanned over 2 LGAs, I wasn't sure what to do about this so I just dropped the first instance of the SA1
Exposure_2 = Exposure_2.drop_duplicates(['SA1_CODE'], keep='last')
# merge the exposure df with the AAL df based on SA1
AAL_merge = Exposure_2.merge(AAL, how='inner', on='SA1_CODE')

#save output
AAL_merge.to_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\SA1_CODE_LGA_AAL.csv")