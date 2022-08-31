import os
import sys
import logging
from os.path import join as pjoin
from matplotlib import pyplot as plt

import numpy as np
import pandas as pd
import seaborn as sns

import scipy.stats as stats

sns.set_style('whitegrid')
sns.set_context("talk")

from git import Repo, InvalidGitRepositoryError

try:
    r = Repo('', search_parent_directories=True)
    commit = str(r.commit('HEAD'))
except InvalidGitRepositoryError:
    commit = 'unknown'

LOGGER = logging.getLogger()
logFormat = "%(asctime)s: %(funcName)s: %(message)s"
logging.basicConfig(level='INFO', 
                    format=logFormat,
                    filename='plotQDMDistributions.log', 
                    filemode='w',
                    datefmt="%Y-%m-%d %H:%M:%S")
console = logging.StreamHandler(sys.stdout)
console.setLevel(getattr(logging, 'INFO'))
formatter = logging.Formatter(logFormat,
                              datefmt='%H:%M:%S', )
console.setFormatter(formatter)
LOGGER.addHandler(console)
LOGGER.info(f"Started {sys.argv[0]} (pid {os.getpid()})")
LOGGER.info(f"Code version: {commit}")

metadata = {"git commit": commit,
            "script": sys.argv[0],}


def plotDistByScenario(data, obs, scenario, start, end, plotpath, title):
    LOGGER.info(f"Plotting distribution for {scenario}, {start}-{end}, {title}")
    fig, ax = plt.subplots(1, 1, figsize=(6, 5))
    x = np.arange(0, 100)
    b = np.arange(0, 100, 5)
    h = np.arange(0, 100, 5).astype(str).tolist()
    for index, row in data.iterrows():
        popt = (row.mu, row.sigma, row.zeta)
        fitline = stats.lognorm.pdf(x, *popt)
        if index == 1:
            ax.plot(x, fitline, color='k', label=title.capitalize())
        if row.Model == 'ENS':
            ax.plot(x, fitline, color='b', label="Ensemble")
        else:
            ax.plot(x, fitline, color='k')

    ax.plot(x, stats.lognorm.pdf(x, obs.mu, obs.sigma, obs.zeta),
            'r', label="IBTrACS")
    ax.set_title(scenario)
    ax.set_xlabel(r"$\Delta p_c$ (hPa)")
    ax.set_ylabel("Probability")
    ax.legend()
    fig.tight_layout()
    plt.savefig(pjoin(plotpath, f"distribution_{scenario}_{title}.{start}-{end}.png"), bbox_inches='tight')
    return

def plotModelDistChanges(refparams, futparams, obsparams, scenario, start, end, plotpath, title):
    fig, axes = plt.subplots(3, 4, figsize=(20, 12), sharex=True, sharey=True)
    ax = axes.flatten()
    obsopt = (obsparams.mu, obsparams.sigma, obsparams.zeta)

    x = np.arange(0, 101)
    b = np.arange(0, 100, 5)
    h = np.arange(0, 100, 5).astype(str).tolist()
    for i, row in enumerate(refparams.itertuples()):
        m = row.Model
        r = row.RCP
        if m.startswith("Group"): continue
        LOGGER.info(f"Model: {m}, RCP: {r}")
        refpopt = (row.mu, row.sigma, row.zeta)
        futrow = futparams[(futparams.Model==m) & (futparams.RCP==r)]
        futpopt = (futrow.mu, futrow.sigma, futrow.zeta)
        refpdf = stats.lognorm.pdf(x, *refpopt)
        futpdf = stats.lognorm.pdf(x, *futpopt)
        ks, pv = stats.ks_2samp(refpdf, futpdf)
        titlestr = f"{m} {r}*" if pv < 0.05 else f"{m} {r}"
        ax[i].plot(x, refpdf, 'k', label='Reference')
        ax[i].plot(x, futpdf, 'r', label='Future')
        ax[i].plot(x, stats.lognorm.pdf(x, *obsopt), 'g', lw=1, label='IBTrACS')
        ax[i].set_title(titlestr)
        sns.despine(ax=ax[i])

        if i==0: ax[i].legend(loc=1)

    plt.subplots_adjust(left=0.05)
    fig.text(0.5, 0.01, r"$\Delta p_c$ [hPa]", ha='center', va='center')
    fig.text(0.01, 0.5, "Probability", ha='center', va='center', rotation='vertical')
    #fig.tight_layout()
    plt.savefig(pjoin(plotpath, f"{scenario}_{title}.{start}-{end}.png"), bbox_inches='tight')

plotpath = "../figures/20210210"

params = pd.read_csv(pjoin(plotpath, "fitparameters.csv"))
obsparams = params[params['Model']=='Obs']
scenario = 'RCP45'

refparams = params[params['period']=='1981-2010'][params['RCP']==scenario][params['bc']==0]
plotDistByScenario(refparams, obsparams, scenario, 1981, 2010, plotpath, "reference-raw")
futparams = params[params['period']=='2081-2100'][params['RCP']==scenario][params['bc']==0]
plotDistByScenario(futparams, obsparams, scenario, 1981, 2010, plotpath, "future-raw")

refbcparams = params[params['period']=='1981-2010'][params['RCP']==scenario][params['bc']==1.0]
plotDistByScenario(refbcparams, obsparams, scenario, 1981, 2010, plotpath, "reference-bc")
futbcparams = params[params['period']=='2081-2100'][params['RCP']==scenario][params['bc']==1.0]
plotDistByScenario(futbcparams, obsparams, scenario, 1981, 2010, plotpath, "future-bc")

plotModelDistChanges(refparams, futparams, obsparams, scenario, 2081, 2100, plotpath, 'raw')
plotModelDistChanges(refbcparams, futbcparams, obsparams, scenario, 2081, 2100, plotpath, 'bc')