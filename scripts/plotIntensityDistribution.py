import os
import logging
from os.path import join as pjoin
from datetime import datetime
from itertools import product
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


sns.set_style("whitegrid")

datapath = "X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/tracks/ensemble/20200828"
groups = ["GROUP1", "GROUP2"]
rcps = ["RCP45", "RCP85"]
periods = ["1981-2010", "2021-2040", "2041-2060", "2061-2080", "2081-2100"]

palette = sns.blend_palette(["#5E6A71", "#006983", "#72C7E7", "#A33F1F",
                             "#CA7700", "#A5D867", "#6E7645"], 7)

def load_tracks(filename):
    logging.debug(f"Loading data from {filename}")
    columns = "datetime,num,year,month,day,hour,lon,lat,pmin,vorticity,vmax,tanomsum,tanomdiff,pmslanom,poci,reff,ravg,asym,dt,age,pdiff,ni".split(",")
    df = pd.read_csv(filename, delimiter=',', skipinitialspace=True, names=columns, header=0,
                     dtype={'year':int, 'month':int, 'day':int})
    maxdf = df[df.ni==1.0]
    
    return maxdf

logging.info("Plotting intensity distribution")
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(12, 8))
ax = axes.flatten()

for i, (g, r) in enumerate(product(groups, rcps)):
    for j, p in enumerate(periods):
        scenario = f"{g}_{r}_{p}"
        filename = f"{scenario}.dat"
        df = load_tracks(pjoin(datapath, filename))
        sns.kdeplot(df.vmax, ax=ax[i], color=palette[j], label=p)
        m = df.vmax.median()
        ax[i].axvline(m, linestyle='--', color=palette[j], alpha=0.5)
        ax[i].set_xlabel("Maximum wind speed")
        ax[i].set_xlim((0, 100))
        ax[i].set_title(f"{g} - {r}")
ax[i].legend()
plt.savefig("X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/figures/intensity_distribution.png", bbox_inches='tight', dpi=600)
plt.close(fig)

logging.info("Plotting cumulative distribution")
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(12, 8))
ax = axes.flatten()

for i, (g, r) in enumerate(product(groups, rcps)):
    for j, p in enumerate(periods):
        scenario = f"{g}_{r}_{p}"
        filename = f"{scenario}.dat"
        df = load_tracks(pjoin(datapath, filename))
        sns.kdeplot(df.vmax, ax=ax[i], color=palette[j], label=p, cumulative=True)
        m = df.vmax.median()
        ax[i].axvline(m, linestyle='--', color=palette[j], alpha=0.5)
        ax[i].set_xlabel("Maximum wind speed")
        ax[i].set_xlim((0, 100))
        ax[i].set_title(f"{g} - {r}")
ax[i].legend()
plt.savefig("X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/figures/intensity_cdf.png", bbox_inches='tight', dpi=600)
plt.close(fig)

logging.info("Plotting survival function")
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(12, 8))
ax = axes.flatten()
for i, (g, r) in enumerate(product(groups, rcps)):
    for j, p in enumerate(periods):
        scenario = f"{g}_{r}_{p}"
        filename = f"{scenario}.dat"
        df = load_tracks(pjoin(datapath, filename))
        sns.ecdfplot(df.vmax, ax=ax[i], color=palette[j], label=p, complementary=True,)
        m = df.vmax.median()
        ax[i].axvline(m, linestyle='--', color=palette[j], alpha=0.5)
        ax[i].set_xlabel("Maximum wind speed")
        ax[i].set_xlim((0, 100))
        ax[i].set_title(f"{g} - {r}")
ax[i].legend()
plt.savefig("X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/figures/intensity_sf.png", bbox_inches='tight', dpi=600)
plt.close(fig)

logging.info("Plotting distribution of latitude of LMI")
fig, axes = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(12, 8))
ax = axes.flatten()
for i, (g, r) in enumerate(product(groups, rcps)):
    for j, p in enumerate(periods):
        scenario = f"{g}_{r}_{p}"
        filename = f"{scenario}.dat"
        df = load_tracks(pjoin(datapath, filename))
        sns.kdeplot(df.lat, ax=ax[i], color=palette[j], label=p)
        m = df.lat.median()
        ax[i].axvline(m, linestyle='--', color=palette[j], alpha=0.5)
        ax[i].set_xlabel("Latitude")
        ax[i].set_xlim((-30, 0))
        ax[i].set_title(f"{g} - {r}")
ax[i].legend()
plt.savefig("X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/figures/latitude_lmi.png", bbox_inches='tight', dpi=600)
plt.close(fig)

logging.info("Plotting quantile trends")
# Now plot up quantiles
qdf = pd.DataFrame(columns=['group', 'rcp', 'period', 'q', 'qval'])

quantiles = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
for i, (g, r) in enumerate(product(groups, rcps)):
    for j, p in enumerate(periods):
        scenario = f"{g}_{r}_{p}"
        filename = f"{scenario}.dat"
        df = load_tracks(pjoin(datapath, filename))
        qvals = df.vmax.quantile(quantiles)
        for q, qval in zip(quantiles, qvals):
            qdf = qdf.append({'group':g, 'rcp':r, 'period':p, 'q':q, 'qval':qval}, ignore_index=True)
            
            
g = sns.FacetGrid(qdf, col='rcp', row='group', height=4, aspect=1 )
g.map(sns.scatterplot, "period", "qval", "q", palette=palette)
g.map(sns.lineplot, "period","qval", "q", palette=palette)
g.set_ylabels("Wind speed [m/s]")
g.set_xlabels("Period")
g.add_legend(title="Quantile")

plt.savefig("X:/georisk/HaRIA_B_Wind/projects/qfes_swha/data/derived/TCLV/figures/intensity_quantiles.png", bbox_inches='tight', dpi=600)