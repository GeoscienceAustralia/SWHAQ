"""
Calculate AAL for SA regions, and plot results

- structural loss ratio
- structural loss values
- aggregate for LGAs

"""


import os
import pandas as pd
import numpy as np
from scipy.integrate import simpson
from matplotlib import pyplot as plt
import seaborn as sns
from os.path import join as pjoin
sns.set_style('whitegrid')
sns.set_context('talk')

LOSSFIELD = "structural_mean"
LOSSFIELD2 = "structural_loss_sum"
BASEPATH = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\risk_pp_retro2pt5"
OUTPATH = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\test"
TYPE = "pp_retro_2pt5"
ARIS = os.listdir(BASEPATH)
ARIS = list(map(int, ARIS))
ARIS = sorted(ARIS)
ARIS = [1] + ARIS
__eps__ = 1.0e-6
lossdf = pd.DataFrame(columns=["SA1_CODE", *ARIS])
lossdf2 = pd.DataFrame(columns=["SA1_CODE", *ARIS])

# LGAs
df = pd.read_csv(os.path.join(BASEPATH, f"2\windspeed_2_yr.csv"))
df.drop(df.columns.difference(['SA1_CODE','LGA_CODE','LGA_NAME']), axis=1, inplace=True)
df.drop_duplicates(subset=['SA1_CODE'], inplace=True)
df.set_index('SA1_CODE', inplace=True)

LGAs_6 = ['Noosa (S)', 'Sunshine Coast (R)', 'Moreton Bay (R)', 'Brisbane (C)', 'Gold Coast (C)', 'Redland (C)']
LGAs = df[df['LGA_NAME'].isin(LGAs_6)]
LGAs = LGAs.drop_duplicates(subset=['LGA_NAME'])
LGAs = LGAs.reset_index()
LGAs = LGAs.drop(['SA1_CODE'],axis=1)
LGA_codes = df[df['LGA_NAME'].isin(LGAs_6)]

# calculating aep (probability) from ari (average recurrence)
def probability(ari):
    """Return an annual probability given a return period"""
    aep = 1.0 - np.exp(-1.0/ari)
    return aep

#AAL stats
def AAL_loss_stats(df,LGA_name,lossfield,outpath,type):
    Max = df['AAL'].max()
    Min = df['AAL'].min()
    Mean = df['AAL'].mean()
    Median = df['AAL'].median()
    Std = df['AAL'].std()
    loss_stats = pd.DataFrame({"Dataset": [f"{LOSSFIELD}_{LGA_name}"],
                               "Max": [Max],
                               "Min": [Min],
                               "Mean": [Mean],
                               "Median": [Median],
                               "Std": [Std]})
    loss_stats.set_index("Dataset", inplace=True)
    loss_stats.to_csv(pjoin(outpath,type,
                    f"{lossfield}_{LGA_name}_loss_stats.csv"))

# defining functions for plots

def plotaal_count_ratio(df,lga_name,lossfield,outpath,type):
    med_loss = df['AAL'].median()
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.histplot(df['AAL'], ax=ax)
    plt.xlim([0,0.00015])
    ax.set_yscale('log')
    ax.set_xlabel('AAL')
    ax.set_ylabel('Count')
    plt.axvline(med_loss, color='k', linestyle='dashed', linewidth=1.5)
    ax.set_title(lga_name)
    plt.savefig(pjoin(outpath, type,
                    f"{lossfield}_{lga_name}_AAL.png"))

def plotaal_count_loss(df,lga_name,lossfield,outpath,type):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.histplot(df['AAL'], ax=ax)
    plt.xlim(left=0)
    ax.set_yscale('log')
    ax.set_xlabel('AAL (Millions)')
    ax.set_ylabel('Count')
    ax.set_title(lga_name)
    plt.savefig(pjoin(outpath, type,
                    f"{lossfield}_{lga_name}_AAL.png"))

#for structural loss ratio
def plotaal_prob_ratio(df,lga_name,lossfield,outpath,type):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x=df, y=aeps, ax=ax)
    ax.set_yscale('log')
    plt.xlim([0,0.75])
    plt.ylim(bottom=0.0001)
    ax.set_xlabel('Structural Loss Ratio')
    ax.set_ylabel('Annual Probability')
    ax.set_title(lga_name)
    ax.fill_between(df, aeps, alpha=0.2)
    plt.savefig(pjoin(outpath, type,
                    f"{lossfield}_{lga_name}_probability_loss.png"))

# for structural loss (cost)
def plotaal_prob_loss(df,lga_name,lossfield,outpath,type):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x=df, y=aeps, ax=ax)
    ax.set_yscale('log')
    plt.xlim([0,95])
    plt.ylim(bottom=0.0001)
    ax.set_xlabel('Structural Loss Value (Billions)')
    ax.set_ylabel('Annual Probability')
    ax.fill_between(df, aeps, alpha=0.2)
    ax.set_title(lga_name)
    plt.savefig(pjoin(outpath, type,
                    f"{lossfield}_{lga_name}_probability_loss.png"))

# setting SA1 code for loss dataframe
firstdf = pd.read_csv(os.path.join(BASEPATH, f"2\windspeed_2_yr_agg.csv"))
lossdf['SA1_CODE'] = firstdf['SA1_CODE_']
lossdf.set_index('SA1_CODE', inplace=True)

# importing all ari output flies
for ARI in ARIS:
    if ARI == 1: continue
    tmpdf = pd.read_csv(os.path.join(BASEPATH, f"{ARI:d}\windspeed_{ARI:d}_yr_agg.csv"))
    tmpdf.set_index('SA1_CODE_', inplace=True)
    lossdf = lossdf.join(tmpdf[LOSSFIELD])
    lossdf[ARI] = lossdf[LOSSFIELD]
    lossdf.drop(LOSSFIELD, axis=1, inplace=True)
lossdf[1] = 0

# calculating average annualised loss
aeps = probability(np.array(lossdf.columns.to_list()))
lossdf['AAL'] = (lossdf*aeps).apply(simpson, axis=1, x=-1*aeps)
lossdf.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_SA1.csv"))
aeps_save = pd.DataFrame(aeps)
aeps_save.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_aeps.csv"))

# plotting count against AAL (structural loss ratio)
# SA1 agg
fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf['AAL'], ax=ax)
ax.set_yscale('log')
plt.xlim(left=0)
ax.set_xlabel('AAL')
ax.set_ylabel('Count')
ax.set_title('SA1 aggregate')
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD}_SA1"))

# grouping by LGA
lossdf_LGA = lossdf.join(df)
lossdf_LGA = lossdf_LGA.drop(['LGA_NAME','AAL'], axis=1)
fields = ['LGA_CODE']
lossdf_LGA = lossdf_LGA.groupby(fields).\
    mean()
lossdf_LGA['AAL'] = (lossdf_LGA*aeps).apply(simpson, axis=1, x=-1*aeps)
lossdf_LGA.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_LGA.csv"))

# plotting count against AAL (structural loss ratio)
# LGA agg
fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf_LGA['AAL'], ax=ax)
plt.xlim(left=0)
ax.set_xlabel('AAL')
ax.set_ylabel('Count')
ax.set_title('LGA aggregate')
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD}_LGA"))

# seperating the 6 LGAs of interest
#creating count plot and prob plot
for index, LGA_code in LGAs.iterrows():
    LGAdf = df.loc[df['LGA_CODE'] == LGA_code['LGA_CODE']]
    LGAname = LGA_code['LGA_NAME']
    LGAname = LGAname[:-4]
    lossdf4 = lossdf.merge(LGAdf, left_index=True, right_index=True)
    AAL_loss_stats(lossdf4,LGAname,LOSSFIELD,OUTPATH,TYPE)
    plotaal_count_ratio(lossdf4,LGAname,LOSSFIELD,OUTPATH,TYPE)
    lossdf4 = lossdf4.drop(['AAL','LGA_CODE','LGA_NAME'], axis=1)
    lossdf4 = lossdf4.mean(axis=0)
    plotaal_prob_ratio(lossdf4,LGAname,LOSSFIELD,OUTPATH,TYPE)

# finding mean of structural loss ratio mean
# to create AAL prob plot
# SA1 agg
lossdf = lossdf.mean(axis=0)
lossdf = lossdf.drop(['AAL'])

# creating AAL prob plot
fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=lossdf, y=aeps, ax=ax)
ax.set_yscale('log')
plt.xlim([0,0.75])
plt.ylim(bottom=0.0001)
ax.set_xlabel('Structural Loss Ratio')
ax.set_ylabel('Annual Probability')
ax.set_title('SA1 aggregate')
ax.fill_between(lossdf, aeps, alpha=0.2)
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD}_SA1_probability_loss"))

# finding mean of structural loss ratio mean
# to create AAL prob plot
# LGA agg
lossdf_LGA = lossdf_LGA.mean(axis=0)
lossdf_LGA = lossdf_LGA.drop(['AAL'])

# creating AAL prob plot
fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=lossdf_LGA, y=aeps, ax=ax)
ax.set_yscale('log')
plt.xlim([0,0.75])
plt.ylim(bottom=0.0001)
ax.set_xlabel('Structural Loss Ratio')
ax.set_ylabel('Annual Probability')
ax.set_title('LGA aggregate')
ax.fill_between(lossdf_LGA, aeps, alpha=0.2)
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD}_LGA_probability_loss"))

# Structural loss
firstdf2 = pd.read_csv(os.path.join(BASEPATH, f"2\windspeed_2_yr_agg.csv"))
lossdf2['SA1_CODE'] = firstdf2['SA1_CODE_']
lossdf2.set_index('SA1_CODE', inplace=True)

for ARI in ARIS:
    if ARI == 1: continue
    tmpdf2 = pd.read_csv(os.path.join(BASEPATH, f"{ARI:d}\windspeed_{ARI:d}_yr_agg.csv"))
    tmpdf2.set_index('SA1_CODE_', inplace=True)
    lossdf2 = lossdf2.join(tmpdf2[LOSSFIELD2])
    lossdf2[ARI] = lossdf2[LOSSFIELD2]
    lossdf2.drop(LOSSFIELD2, axis=1, inplace=True)
lossdf2[1] = 0

aeps = probability(np.array(lossdf2.columns.to_list()))
lossdf2['AAL'] = lossdf2.apply(simpson, axis=1, x=-1*aeps)
lossdf2.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD2}_SA1.csv"))
lossdf2 = lossdf2.div(1000000)

fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf2['AAL'], ax=ax)
ax.set_yscale('log')
plt.xlim(left=0)
ax.set_xlabel('AAL (Millions)')
ax.set_ylabel('Count')
ax.set_title('SA1 aggregate')
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD2}_SA1"))

lossdf2_LGA = lossdf2.join(df)
lossdf2_LGA = lossdf2_LGA.drop(['LGA_NAME','AAL'], axis=1)
fields = ['LGA_CODE']
lossdf2_LGA = lossdf2_LGA.groupby(fields).\
    sum()
lossdf2_LGA['AAL'] = lossdf2_LGA.apply(simpson, axis=1, x=-1*aeps)
lossdf2_LGA.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD2}_LGA.csv"))

# plotting count against AAL (structural loss ratio)
# LGA agg
fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf2_LGA['AAL'], ax=ax)
plt.xlim(left=0)
ax.set_xlabel('AAL (Millions)')
ax.set_ylabel('Count')
ax.set_title('LGA aggregate')
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD2}_LGA"))

for index, LGA_code in LGAs.iterrows():
    LGAdf = df.loc[df['LGA_CODE'] == LGA_code['LGA_CODE']]
    LGAname = LGA_code['LGA_NAME']
    LGAname = LGAname[:-4]
    lossdf3 = lossdf2.merge(LGAdf, left_index=True, right_index=True)
    plotaal_count_loss(lossdf3,LGAname,LOSSFIELD2,OUTPATH,TYPE)
    lossdf3 = lossdf3.drop(['AAL','LGA_CODE','LGA_NAME'],axis=1)
    lossdf3 = lossdf3.sum(axis=0)
    lossdf3 = lossdf3.div(1000)
    plotaal_prob_loss(lossdf3,LGAname,LOSSFIELD2,OUTPATH,TYPE)

lossdf2 = lossdf2.sum(axis=0)
lossdf2 = lossdf2.drop(['AAL'])
lossdf2 = lossdf2.div(1000)

fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=lossdf2, y=aeps, ax=ax)
ax.set_yscale('log')
plt.xlim(left=0)
plt.ylim(bottom=0.0001)
ax.set_xlabel('Structural Loss Value (Billions)')
ax.set_ylabel('Annual Probability')
ax.set_title('SA1 aggregate')
ax.fill_between(lossdf2, aeps, alpha=0.2)
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD2}_SA1_probability_loss"))

lossdf2_LGA = lossdf2_LGA.sum(axis=0)
lossdf2_LGA = lossdf2_LGA.drop(['AAL'])
lossdf2_LGA = lossdf2_LGA.div(1000)

fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=lossdf2_LGA, y=aeps, ax=ax)
ax.set_yscale('log')
plt.xlim(left=0)
plt.ylim(bottom=0.0001)
ax.set_xlabel('Structural Loss Value (Billions)')
ax.set_ylabel('Annual Probability')
ax.set_title('LGA aggregate')
ax.fill_between(lossdf2_LGA, aeps, alpha=0.2)
plt.savefig(pjoin(OUTPATH, TYPE,
                f"{LOSSFIELD2}_LGA_probability_loss"))


