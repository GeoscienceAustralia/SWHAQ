# the aim of this script is to classify AAL and combined AAL ADRI scores into the same number of categories
#AAL_class as in df is presented in three categories based on quartiles <25th quartile = low, 25-75th quartile = moderate, >75th quartile = high
#combined class is presented in 5 categories.

#plan
#re-categorise AAL into 5 categories based on equal intervals
#label categories for both AAL and combined as 1, 2, 3, 4, 5
#average new categories to SA2 level (currently at SA1)
#rank each SA2 by AAL category and by combined category
#compare rankings

import os
import pandas as pd
import numpy as np
from os.path import join as pjoin

# import the csv with both AAL, ADRI, and combined AAL ADRI value
df = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\ADRI_AAL_Combined.csv", index_col=0)

# re-classify the AAL categories
# was as the description above 
Max = df['AAL_ratio'].max()
Min = df['AAL_ratio'].min()
Diff = Max-Min
Diff5 = Diff/5
Cat1_max = Min+Diff5
Cat2_max = Cat1_max+Diff5
Cat3_max = Cat2_max+Diff5
Cat4_max = Cat3_max+Diff5
Cat5_max = Max

col         = 'AAL_ratio'
conditions  = [ df[col] <= Cat1_max, (df[col] > Cat1_max) & (df[col] <= Cat2_max), (df[col] > Cat2_max) & (df[col] <= Cat3_max), (df[col] > Cat3_max) & (df[col] <= Cat4_max), (df[col] > Cat4_max) & (df[col] <= Cat5_max)]
choices     = ['Low','Low-Moderate','Moderate','High-Moderate','High']
    
df['AAL_reclass'] = np.select(conditions, choices, default=np.nan)

df['AAL_reclass_num'] = df["AAL_reclass"]
df['comb_class_num'] = df["comb_class"]

df.loc[(df.AAL_reclass_num == 'Low'),'AAL_reclass_num'] = 1
df.loc[(df.AAL_reclass_num == 'Low-Moderate'),'AAL_reclass_num'] = 2
df.loc[(df.AAL_reclass_num == 'Moderate'),'AAL_reclass_num'] = 3
df.loc[(df.AAL_reclass_num == 'High-Moderate'),'AAL_reclass_num'] = 4
df.loc[(df.AAL_reclass_num == 'High'),'AAL_reclass_num'] = 5

df.loc[(df.comb_class_num == 'Low'),'comb_class_num'] = 1
df.loc[(df.comb_class_num == 'Low-Moderate'),'comb_class_num'] = 2
df.loc[(df.comb_class_num == 'Moderate'),'comb_class_num'] = 3
df.loc[(df.comb_class_num == 'High-Moderate'),'comb_class_num'] = 4
df.loc[(df.comb_class_num == 'High'),'comb_class_num'] = 5

df2 = df.groupby(['SA2_MAIN16'])[['AAL_reclass_num', 'comb_class_num']].mean()
breakpoint()
df2.to_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\ADRI_AAL_Combined_rank.csv")
