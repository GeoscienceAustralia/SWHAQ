# This code creates comparison plots for for two AAL sets
# (e.g. comparing baseline AAL with retrofit AAL)

# it assumes that AAL_calculations.py has already been run

import os
import pandas as pd
import numpy as np
from scipy.integrate import simpson
from matplotlib import pyplot as plt
import seaborn as sns
from os.path import join as pjoin
sns.set_style('whitegrid')
sns.set_context('talk')

# import tables for structural loss mean for AAL set 1 and 2, for both SA1 and LGA aggregation
orig_SLR_SA1 = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_baseline\structural_mean_SA1.csv", index_col=0)
new_SLR_SA1 = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_retro_5\structural_mean_SA1.csv", index_col=0)
orig_SLR_LGA = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_baseline\structural_mean_LGA.csv", index_col=0)
new_SLR_LGA = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_retro_5\structural_mean_LGA.csv", index_col=0)

# import tables for structural loss sum for AAL set 1 and 2, for both SA1 and LGA aggregation
orig_SLV_SA1 = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_baseline\structural_loss_sum_SA1.csv", index_col=0)
new_SLV_SA1 = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_retro_5\structural_loss_sum_SA1.csv", index_col=0)
orig_SLV_LGA = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_baseline\structural_loss_sum_LGA.csv", index_col=0)
new_SLV_LGA = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_retro_5\structural_loss_sum_LGA.csv", index_col=0)

# import the list of AEPs from one of the AAL sets (AEPs should be the same for both AAL sets)
aeps = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_baseline\structural_mean_aeps.csv", index_col=0)
# set the location to save outputs
OUTPATH = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\AAL\pp_comp"

# LGAs
# input a random AAL run to extract the list of LGAs
df = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\DRAFT DATA STRUCTURES\1. Work Unit Assessment\SOUTH EAST QUEENSLAND\Risk\risk_baseline\2\windspeed_2_yr.csv")
df.drop(df.columns.difference(['SA1_CODE','LGA_CODE','LGA_NAME']), axis=1, inplace=True)
df.drop_duplicates(subset=['SA1_CODE'], inplace=True)
df.set_index('SA1_CODE', inplace=True)

# identify the LGAs of interest
LGAs_6 = ['Noosa (S)', 'Sunshine Coast (R)', 'Moreton Bay (R)', 'Brisbane (C)', 'Gold Coast (C)', 'Redland (C)']
LGAs = df[df['LGA_NAME'].isin(LGAs_6)]
LGAs = LGAs.drop_duplicates(subset=['LGA_NAME'])
LGAs = LGAs.reset_index()
LGAs = LGAs.drop(['SA1_CODE'],axis=1)
LGA_codes = df[df['LGA_NAME'].isin(LGAs_6)]

# transform AEPs to usable format
aeps = aeps.iloc[:,0]
aeps = aeps.to_numpy()

# finding mean of structural loss ratio mean
# the average SLR across all SA1s for each AEP
# to create AAL prob plot
# SA1 agg
orig_SLR_SA1_ratio = orig_SLR_SA1.mean(axis=0)
orig_SLR_SA1_ratio = orig_SLR_SA1_ratio.drop(['AAL'])

new_SLR_SA1_ratio = new_SLR_SA1.mean(axis=0)
new_SLR_SA1_ratio = new_SLR_SA1_ratio.drop(['AAL'])

# creating AAL prob plot
# comparison of probability of mean SLR occuring for each AEP
# both AAL sets
fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=orig_SLR_SA1_ratio, y=aeps, ax=ax, color="#006983")
sns.lineplot(x=new_SLR_SA1_ratio, y=aeps, ax=ax, color="#5FACBF")
ax.set_yscale('log')
plt.xlim([0,0.75])
plt.ylim(bottom=0.0001)
ax.set_xlabel('Structural loss ratio')
ax.set_ylabel('Annual probability')
ax.set_title('SA1 aggregate')
plt.legend(orig_SLR_SA1_ratio, new_SLR_SA1_ratio, labels=['baseline', 'retrofit 5%'])
ax.fill_between(orig_SLR_SA1_ratio, aeps, alpha=0.2)
ax.fill_between(new_SLR_SA1_ratio, aeps, alpha=0.2, color="#5FACBF")
plt.savefig(pjoin(OUTPATH,
                f"SA1_probability_ratio"))

# summing total SLV across all SA1s for each AEP
# divide by 1000000000 so that value is in billions
orig_SLV_SA1_loss = orig_SLV_SA1.sum(axis=0)
orig_SLV_SA1_loss = orig_SLV_SA1_loss.drop(['AAL'])
orig_SLV_SA1_loss = orig_SLV_SA1_loss.div(1000000000)

new_SLV_SA1_loss = new_SLV_SA1.sum(axis=0)
new_SLV_SA1_loss = new_SLV_SA1_loss.drop(['AAL'])
new_SLV_SA1_loss = new_SLV_SA1_loss.div(1000000000)

# creating AAL prob plot
# comparison of probability of total SLV occuring for each AEP
# both AAL sets
fig, ax = plt.subplots(figsize=(12, 8))
sns.lineplot(x=orig_SLV_SA1_loss, y=aeps, ax=ax, color="#006983")
sns.lineplot(x=new_SLV_SA1_loss, y=aeps, ax=ax, color="#5FACBF")
ax.set_yscale('log')
plt.xlim(left=0)
plt.ylim(bottom=0.0001)
ax.set_xlabel('Loss (Billions)')
ax.set_ylabel('Annual probability')
ax.set_title('SA1 aggregate')
ax.fill_between(orig_SLV_SA1_loss, aeps, alpha=0.2)
ax.fill_between(new_SLV_SA1_loss, aeps, alpha=0.2, color="#5FACBF")
plt.legend(orig_SLV_SA1_loss, new_SLV_SA1_loss, labels=['baseline', 'retrofit 5%'])
plt.savefig(pjoin(OUTPATH,
                f"SA1_probability_loss"))

# define a plot function for comparison of
# probability of SLR occuring for each AEP
# using average SLR for each LGA 
def plotaal_prob_ratio(df1,df2,lga_name,outpath):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x=df1, y=aeps, ax=ax, color="#006983")
    sns.lineplot(x=df2, y=aeps, ax=ax, color="#5FACBF")
    ax.set_yscale('log')
    plt.xlim([0,0.75])
    plt.ylim(bottom=0.0001)
    ax.set_xlabel('Structural loss ratio')
    ax.set_ylabel('Annual probability')
    ax.set_title(lga_name)
    ax.fill_between(df1, aeps, alpha=0.2)
    ax.fill_between(df2, aeps, alpha=0.2, color="#5FACBF")
    plt.legend(labels=['baseline', 'retrofit 5%'])
    plt.savefig(pjoin(outpath,
                    f"{lga_name}_probability_ratio.png"))

# seperating the 6 LGAs of interest
# looping through each LGA to create count plot and prob plot
for index, LGA_code in LGAs.iterrows():
    LGAdf = df.loc[df['LGA_CODE'] == LGA_code['LGA_CODE']]
    LGAdf = LGAdf.reset_index()
    LGAdf = LGAdf.drop(LGAdf.index.to_list()[1:],axis = 0 )
    LGAname = LGA_code['LGA_NAME']
    LGAname = LGAname[:-4]
    orig_SLR_LGA_ratio = orig_SLR_LGA.merge(LGAdf, left_index=True, right_on='LGA_CODE')
    orig_SLR_LGA_ratio = orig_SLR_LGA_ratio.drop(['AAL','SA1_CODE','LGA_CODE','LGA_NAME'], axis=1)
    orig_SLR_LGA_ratio = orig_SLR_LGA_ratio.transpose()
    orig_SLR_LGA_ratio = orig_SLR_LGA_ratio.iloc[:,0]
    new_SLR_LGA_ratio = new_SLR_LGA.merge(LGAdf, left_index=True, right_on='LGA_CODE')
    new_SLR_LGA_ratio = new_SLR_LGA_ratio.drop(['AAL','SA1_CODE','LGA_CODE','LGA_NAME'], axis=1)
    new_SLR_LGA_ratio = new_SLR_LGA_ratio.transpose()
    new_SLR_LGA_ratio = new_SLR_LGA_ratio.iloc[:,0]
    plotaal_prob_ratio(orig_SLR_LGA_ratio,new_SLR_LGA_ratio,LGAname,OUTPATH)

# define a plot function for comparison of
# probability of SLV occuring for each AEP
# using average SLV for each LGA 
def plotaal_prob_loss(df1,df2,lga_name,outpath):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(x=df1, y=aeps, ax=ax, color="#006983")
    sns.lineplot(x=df2, y=aeps, ax=ax, color="#5FACBF")
    ax.set_yscale('log')
    plt.xlim([0,90])
    plt.ylim(bottom=0.0001)
    ax.set_xlabel('Loss (Billions)')
    ax.set_ylabel('Annual probability')
    ax.fill_between(df1, aeps, alpha=0.2)
    ax.fill_between(df2, aeps, alpha=0.2, color="#5FACBF")
    ax.set_title(lga_name)
    plt.legend(labels=['baseline', 'retrofit 5%'])
    plt.savefig(pjoin(outpath,
                    f"{lga_name}_probability_loss.png"))

# seperating the 6 LGAs of interest
# looping through each LGA to create count plot and prob plot
for index, LGA_code in LGAs.iterrows():
    LGAdf = df.loc[df['LGA_CODE'] == LGA_code['LGA_CODE']]
    LGAdf = LGAdf.reset_index()
    LGAdf = LGAdf.drop(LGAdf.index.to_list()[1:],axis = 0 )
    LGAname = LGA_code['LGA_NAME']
    LGAname = LGAname[:-4]
    orig_SLV_LGA_loss = orig_SLV_LGA.merge(LGAdf, left_index=True, right_on='LGA_CODE')
    orig_SLV_LGA_loss = orig_SLV_LGA_loss.drop(['AAL','SA1_CODE','LGA_CODE','LGA_NAME'], axis=1)
    orig_SLV_LGA_loss = orig_SLV_LGA_loss.div(1000)
    orig_SLV_LGA_loss = orig_SLV_LGA_loss.transpose()
    orig_SLV_LGA_loss = orig_SLV_LGA_loss.iloc[:,0]
    new_SLV_LGA_loss = new_SLV_LGA.merge(LGAdf, left_index=True, right_on='LGA_CODE')
    new_SLV_LGA_loss = new_SLV_LGA_loss.drop(['AAL','SA1_CODE','LGA_CODE','LGA_NAME'], axis=1)
    new_SLV_LGA_loss = new_SLV_LGA_loss.div(1000)
    new_SLV_LGA_loss = new_SLV_LGA_loss.transpose()
    new_SLV_LGA_loss = new_SLV_LGA_loss.iloc[:,0]
    plotaal_prob_loss(orig_SLV_LGA_loss,new_SLV_LGA_loss,LGAname,OUTPATH)