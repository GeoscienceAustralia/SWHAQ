"""
Calculate AAL for SA regions, and plot results.

Takes a probabilistic retrofit analysis, where multiple iterations have been run
to understand the range of outcomes arising from the random selection of
buildings for retrofit (with some criteria applied).


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
BASEPATH = "/g/data/w85/QFES_SWHA/risk_pp/retro_prob"
OUTPATH = "/g/data/w85/QFES_SWHA/risk_pp/AAL/"
TYPE = "retro_prob"
ARIS = os.listdir(BASEPATH)
ARIS = list(map(int, ARIS))
ARIS = sorted(ARIS)
#ARIS = [1] + ARIS
__eps__ = 1.0e-6
lossdfmin = pd.DataFrame(columns=["SA1_CODE", *ARIS])
lossdfmed = pd.DataFrame(columns=["SA1_CODE", *ARIS])
lossdfmax = pd.DataFrame(columns=["SA1_CODE", *ARIS])
lossdfout = pd.DataFrame(columns=["SA1_CODE", "0.05", "0.5", "0.95"])

# LGAs
df = pd.read_csv(os.path.join(BASEPATH, f"2/quantiles.csv"))
df.drop(df.columns.difference(['SA1_CODE','LGA_CODE','LGA_NAME']), axis=1, inplace=True)
df.drop_duplicates(subset=['SA1_CODE'], inplace=True)
df.set_index('SA1_CODE', inplace=True)

LGAs_6 = ['Noosa (S)', 'Sunshine Coast (R)', 'Moreton Bay (R)',
          'Brisbane (C)', 'Gold Coast (C)', 'Redland (C)']
LGAs = df[df['LGA_NAME'].isin(LGAs_6)]
LGAs = LGAs.drop_duplicates(subset=['LGA_NAME'])
LGAs = LGAs.reset_index()
LGAs = LGAs.drop(['SA1_CODE'],axis=1)
LGA_codes = df[df['LGA_NAME'].isin(LGAs_6)]

# calculating aep (probability) from ari (average recurrence)
def probability(ari):
    """
    Return an annual probability given a return period

    $$AEP = 1 - \exp{-1/ARI}$$

    :param ari: `float` or `np.array` of floats representing avrage recurrence
        intervals.
    """
    aep = 1.0 - np.exp(-1.0/ari)
    return aep

def calculateAAL(df: pd.DataFrame, aeps: np.ndarray) -> pd.Series:
    """
    Calculate average annual loss based on the losses for each AEP. The AAL is
    the integral of the loss exceedance probablity curve

    $$EP_i = L_i * p_i$$

    $$AAL = \int_{0}^{1} L \,dp$$

    :param df: `pd.DataFrame` containing losses at defined AEPs. Each row
        represents an asset (could be a region, or individual asset).
    :param aeps: Array of annual exceedance probability values. Must be
        monotonically descending.

    :returns: `pd.Series` of AAL values
    """
    if (np.max(aeps) > 1.0) or (np.min(aeps) < 0.0):
        raise ValueError("AEP values not in range [0, 1]")
    if np.any(np.diff(aeps) > 0):
        raise ("AEP values are not monotonically descending")

    # Perform the integration - we negate the AEPs, we expect them to be
    # monotonically descending. The order of the integration is transposed,
    # as we `apply` the integration along rows (not columns)
    aal = df.apply(simpson, axis=1, x=-1*aeps)
    return aal

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
SA1_CODES = LGA_codes.index
firstdf = pd.read_csv(os.path.join(BASEPATH, f"2/aggregated_quantiles.csv"))
lossdfmin['SA1_CODE'] = firstdf['SA1_CODE_']
lossdfmed['SA1_CODE'] = firstdf['SA1_CODE_']
lossdfmax['SA1_CODE'] = firstdf['SA1_CODE_']
lossdfout['SA1_CODE'] = firstdf['SA1_CODE_']
lossdfmin.set_index('SA1_CODE', inplace=True)
lossdfmed.set_index('SA1_CODE', inplace=True)
lossdfmax.set_index('SA1_CODE', inplace=True)
lossdfout.set_index('SA1_CODE', inplace=True)

# importing all ari output flies
for ARI in ARIS:
    if ARI == 1: continue
    tmpdf = pd.read_csv(os.path.join(BASEPATH, f"{ARI:d}/aggregated_quantiles.csv"))
    tmpdf.set_index('SA1_CODE_', inplace=True)
    lossdfmin = lossdfmin.join(tmpdf['0.05_mean'])
    lossdfmin[ARI] = lossdfmin['0.05_mean']
    lossdfmed = lossdfmed.join(tmpdf['0.5_mean'])
    lossdfmed[ARI] = lossdfmed['0.5_mean']
    lossdfmax = lossdfmax.join(tmpdf['0.95_mean'])
    lossdfmax[ARI] = lossdfmax['0.95_mean']
    
    lossdfmin.drop('0.05_mean', axis=1, inplace=True)
    lossdfmed.drop('0.5_mean', axis=1, inplace=True)
    lossdfmax.drop('0.95_mean', axis=1, inplace=True)

lossdfmin[1] = 0
lossdfmed[1] = 0
lossdfmax[1] = 0

# calculating average annualised loss
aeps = probability(np.array(lossdfmin.columns.to_list()))

lossdfmin['AAL'] = calculateAAL(lossdfmin, aeps)
lossdfmed['AAL'] = calculateAAL(lossdfmed, aeps)
lossdfmax['AAL'] = calculateAAL(lossdfmax, aeps)

lossdfout = lossdfout.join(lossdfmin['AAL'])
lossdfout['0.05'] = lossdfout['AAL']
lossdfout.drop('AAL', axis=1, inplace=True)
lossdfout = lossdfout.join(lossdfmed['AAL'])
lossdfout['0.5'] = lossdfout['AAL']
lossdfout.drop('AAL', axis=1, inplace=True)
lossdfout = lossdfout.join(lossdfmax['AAL'])
lossdfout['0.95'] = lossdfout['AAL']
lossdfout.drop('AAL', axis=1, inplace=True)

lossdfout.to_csv(pjoin(OUTPATH, TYPE, f"SA1_CODE_AAL.csv"), float_format="%.6f")

aeps_save = pd.DataFrame(aeps)
aeps_save.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_aeps.csv"))

# plotting count against AAL (structural loss ratio)
# SA1 agg
fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdfmax['AAL'], ax=ax, element='step', color='g')
sns.histplot(lossdfmed['AAL'], ax=ax, element='step', color='b')
sns.histplot(lossdfmin['AAL'], ax=ax, element='step', color='r')
ax.set_yscale('log')
plt.xlim(left=0)
ax.set_xlabel('AAL')
ax.set_ylabel('Count')
ax.set_title('SA1 aggregate')
plt.savefig(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_SA1.png"))

# grouping by LGA


lossdfmin_LGA = lossdfmin.join(df)
lossdfmin_LGA = lossdfmin_LGA.drop(['LGA_NAME','AAL'], axis=1)
fields = ['LGA_CODE']
lossdfmin_LGA = lossdfmin_LGA.groupby(fields).mean()
lossdfmin_LGA['AAL'] = calculateAAL(lossdfmin_LGA, aeps)
lossdfmed_LGA = lossdfmed.join(df)
lossdfmed_LGA = lossdfmed_LGA.drop(['LGA_NAME','AAL'], axis=1)
fields = ['LGA_CODE']
lossdfmed_LGA = lossdfmed_LGA.groupby(fields).mean()
lossdfmed_LGA['AAL'] = calculateAAL(lossdfmed_LGA, aeps)
lossdfmax_LGA = lossdfmax.join(df)
lossdfmax_LGA = lossdfmax_LGA.drop(['LGA_NAME','AAL'], axis=1)
fields = ['LGA_CODE']
lossdfmax_LGA = lossdfmax_LGA.groupby(fields).mean()
lossdfmax_LGA['AAL'] = calculateAAL(lossdfmax_LGA, aeps)

LGAdf = pd.merge(LGAs, lossdfmin_LGA['AAL'], how='inner', left_on="LGA_CODE", right_index=True).rename(columns={"AAL":"0.05"})
LGAdf = pd.merge(LGAdf, lossdfmed_LGA['AAL'], how='inner', left_on="LGA_CODE", right_index=True).rename(columns={"AAL":"0.5"})
LGAdf = pd.merge(LGAdf, lossdfmax_LGA['AAL'], how='inner', left_on="LGA_CODE", right_index=True).rename(columns={"AAL":"0.95"})
LGAdf.to_csv(pjoin(OUTPATH, TYPE, f"LGA_CODE_AAL.csv"), float_format="%.6f")

"""
lossdf_LGA.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_LGA.csv"))

# plotting count against AAL (structural loss ratio)
# LGA agg
fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf_LGA['AAL'], ax=ax)
plt.xlim(left=0)
ax.set_xlabel('AAL')
ax.set_ylabel('Count')
ax.set_title('LGA aggregate')
plt.savefig(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_LGA"))

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
plt.savefig(pjoin(OUTPATH, TYPE, f"{LOSSFIELD}_SA1_probability_loss"))

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
lossdf2['AAL'] = calculateAAL(lossdf2, aeps)
lossdf2.to_csv(pjoin(OUTPATH, TYPE, f"{LOSSFIELD2}_SA1.csv"))
lossdf2 = lossdf2.div(1_000_000)

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
lossdf2_LGA = lossdf2_LGA.groupby(fields).sum()
lossdf2_LGA['AAL'] = calculateAAL(lossdf2_LGA, aeps)
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
lossdf2 = lossdf2.div(1_000)

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


"""