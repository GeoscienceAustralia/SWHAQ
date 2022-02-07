
# coding: utf-8

# # Impact scenario quality control
# 
# This notebook is intended to provide a review of the impact
# scenarios generated in the Severe Wind Hazard Assessment project.
# 
# The impact results are generated using the
# [_HazImp_](https://github.com/GeoscienceAustralia/hazimp) tool, with
# TC wind footprints generated from
# [TCRM](https://github.com/GeoscienceAustralia/tcrm). Scenarios were
# selected in consultation with Department of Fire and Emergency
# Services (Western Australia) and the Bureau of Meteorology (Western
# Australia Regional Office).
# 
# ### Dependencies
# 
# 1. Numpy
# 2. Pandas
# 3. GeoPandas
# 4. Matplotlib
# 5. Seaborn
# 6. HazImp
# 
# NOTE: I have only successfully installed GeoPandas on a Python 3.6
# installation (on a Windows environment). 

import matplotlib

matplotlib.use("Agg")
import os 
from os.path import join as pjoin
import numpy as np
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt

import seaborn as sns
sns.set_context('talk',font_scale=1.5)
                #rc={"xtick.labelsize":"large", 
                #    "ytick.labelsize":"large"})
                
sns.set_style('ticks')
palette = sns.blend_palette(["#5E6A71", "#006983", "#72C7E7", "#A33F1F",
                             "#CA7700", "#A5D867", "#6E7645"], 7)
dmgpal = sns.blend_palette([(0.000, 0.627, 0.235), (0.412, 0.627, 0.235), 
                            (0.663, 0.780, 0.282), (0.957, 0.812, 0.000), 
                            (0.925, 0.643, 0.016), (0.835, 0.314, 0.118),
                            (0.780, 0.086, 0.118)], 5)
sns.set_palette(palette)


# The output files for the impact scenarios are stored in the project
# directory, and are stored as csv files.

data_path = "../data/impact"
data_path = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\impact\2020"

events = ['007-02914', '016-04518', '011-01326']
events = ['020-07522', '004-08495', '003-00562', '010-08276', '014-01920']

res = 600
context='paper'
fmt = "png"

# To review an event, change the event number in the following
# line. This will load the different output file for inspection.
for event_num in events:
    print("Processing event {0}".format(event_num))

    output_path = pjoin(data_path, event_num, 'paper')
    try:
        os.makedirs(output_path)
    except:
        pass

    event_file = pjoin(data_path, event_num, f"QFES_{event_num}.csv")

    YEAR_ORDER = ['Pre 1914', '1914 - 1946', '1947 - 1961',
                  '1962 - 1981', '1982 - 1996', '1997 - present']
    ROOF_TYPE_ORDER = ['Metal Sheeting', 'Tiles',
                       'Fibro / asbestos cement sheeting']
    WALL_TYPE_ORDER = ['Double Brick', 'Fibro / asbestos cement sheeting',
                       'Timber', 'Brick Veneer']


    df = pd.read_csv(event_file)


    # Start with plotting the structural loss ratio against 10m wind
    # speed. This should intuitively follow the vulnerability functions
    # used in _HazImp_. Points are coloured by the construction age.
    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.)
    g = sns.lmplot(x='0.2s gust at 10m height m/s',
                   y='structural', 
                   hue='YEAR_BUILT',
                   hue_order=YEAR_ORDER,
                   data=df,
                   fit_reg=False,
                   aspect=2, legend_out=False)

    g.ax.set_ylabel("Structural loss ratio")
    g.ax.set_ylim((0, 1))
    g.ax.set_xlim((20, 90))
    g.ax.legend(title="Construction era", frameon=True)
    plt.savefig(pjoin(output_path, "SLR_Windspeed_by_age.{0}".format(fmt)), dpi=res)
    plt.close(fig)

    # Examine the distribution of structural loss ratio within each
    # contruction era, and colour the points by roof type (out of
    # interests sake). For lower intensity events, we expect the newer
    # construction (post-1982) to experience very low or no damage, since
    # these events will generate wind speeds that are well below the
    # design wind speeds for the region.

    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.5)

    sns.stripplot(x='YEAR_BUILT', y='structural', 
                  hue='ROOF_TYPE', order=YEAR_ORDER, 
                  data=df, jitter=True, ax=ax)
    ax.set_xlabel("Construction era", fontsize='large')
    #ax.set_ylim((0, 1))

    ax.set_ylabel("Structural loss ratio", fontsize='large')
    ax.legend(title="Roof material", frameon=True)
    fig.savefig(pjoin(output_path, "SLR_by_age.{0}".format(fmt)), dpi=res,
                bbox_inches="tight")
    plt.close(fig)

    # Now look at the structural loss in dollar terms. This is less
    # important for an EM perspective, but serves as a cursory check that
    # the outputs are sensible. Replacement costs are based on quantity
    # surveyor data and represent 2017 values.
    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.)

    g = sns.lmplot(x='0.2s gust at 10m height m/s',
                  y='structural_loss', 
                  hue='YEAR_BUILT', 
                  hue_order=YEAR_ORDER,
                  data=df,
                  fit_reg=False,
                  aspect=2, legend_out=False)

    ylabels = g.ax.get_yticks()
    g.ax.set_yticklabels(["${:0,.0f}".format(y) for y in ylabels])
    g.ax.set_ylabel("Structural loss ($)")
    g.ax.set_xlim((20, 90))
    g.ax.legend(title="Construction era", frameon=True)
    plt.savefig(pjoin(output_path, "SLC_Windspeed_by_age.{0}".format(fmt)), dpi=res,
                bbox_inches="tight")
    plt.close(fig)

    bins=[0.0, 0.02, 0.1, 0.2, 0.5, 1.0]
    labels=['Negligible', 'Slight', 'Moderate', 'Extensive', 'Complete']
    df['Damage state'] = pd.cut(df['structural'], bins,
                                right=True, labels=labels)

    # Save a table of number of buildings in each damage state per LGA:
    df.pivot_table(index='LGA_NAME',
                   columns='Damage state',
                   aggfunc='size',
                   fill_value=0).to_excel(pjoin(output_path, "{0}_damage_state_lga.xlsx".format(event_num)))

    df.pivot_table(index=["LGA_NAME", "YEAR_BUILT"],
                   columns='Damage state',
                   aggfunc='size',
                   fill_value=0).to_excel(pjoin(output_path, "{0}_damage_state_lga_age.xlsx".format(event_num)))
    # Save a table of number of buildings in each damage state, broken
    # down by construction era, roof type and wall type:
    df.pivot_table(index=['Damage state', 'YEAR_BUILT'], 
                   columns=['WALL_TYPE', 'ROOF_TYPE'], 
                   aggfunc='size', fill_value=0).to_excel(pjoin(output_path, "{0}_damage_state_type.xlsx".format(event_num)))

    # Save a table of number of buildings in each damage state, broken
    # down by construction era
    df.pivot_table(index='YEAR_BUILT', 
                   columns='Damage state',
                   aggfunc='size', 
                   fill_value=0).to_excel(pjoin(output_path, "{0}_dmgstate.xlsx".format(event_num)))
    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.5)

    sns.countplot(x='Damage state', data=df, order=labels, palette=dmgpal)
    ax.set_ylabel("Number")
    plt.savefig(pjoin(output_path, "damage_state.{0}".format(fmt)), 
                dpi=res, bbox_inches="tight")
    plt.close(fig)


    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.5)
    ax = sns.countplot(x='Damage state', data=df, order=labels, hue='YEAR_BUILT', hue_order=YEAR_ORDER)
    ax.legend(title="Construction era", frameon=True, loc=1)
    ax.set_ylabel("Number")
    plt.savefig(pjoin(output_path, "damage_state_by_age.{0}".format(fmt)),
                dpi=res, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.5)
    ax = sns.pointplot(x='Damage state', y='structural',
                       data=df, order=labels,
                       hue='YEAR_BUILT', hue_order=YEAR_ORDER)
    ax.set_ylabel("Structural loss ratio")
    ax.set_ylim((0, 1))
    ax.legend(title="Construction era", frameon=True)
    plt.savefig(pjoin(output_path, "SLR_by_damage_state.{0}".format(fmt)), 
                dpi=res, bbox_inches="tight")
    plt.close(fig)

    # Building age profile for the community. 
    fig, ax = plt.subplots(figsize=(16,9))
    sns.set_context(context,font_scale=1.5)
    sns.countplot(x='YEAR_BUILT', order=YEAR_ORDER, data=df, ax=ax)
    ax.set_xlabel("Construction era")
    ax.set_ylabel("Number")
    plt.savefig(pjoin(output_path, "building_age_profile.{0}".format(fmt)),
                dpi=res, bbox_inches="tight")
    plt.close(fig)
