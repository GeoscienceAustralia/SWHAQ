"""
Calculate AAL for each iteration and aggregate to LGA level


"""

import os
import numpy as np
import pandas as pd
from scipy.integrate import simpson
from matplotlib import pyplot as plt
import seaborn as sns
from os.path import join as pjoin
sns.set_style('whitegrid')
sns.set_context('talk')

LOSSFIELD = "structural_mean"
BASEPATH = "/g/data/w85/QFES_SWHA/risk_pp/retro_prob_v2"
OUTPATH = "/g/data/w85/QFES_SWHA/risk_pp/AAL/"
TYPE = "retro_prob_v2"
ARIS = os.listdir(BASEPATH)
ARIS = list(map(int, ARIS))
ARIS = sorted(ARIS)

LGA_NAMES = ['Brisbane (C)', 'Gold Coast (C)', 'Moreton Bay (R)',
             'Redland (C)', 'Sunshine Coast (R)', 'Noosa (S)']
LGA_CODES = [31000, 33430, 35010, 36250, 36720, 35740]
LGAs = pd.DataFrame(data={"LGA_CODE": LGA_CODES,
                          "LGA_NAME": LGA_NAMES})

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

def probability(ari):
    """
    Return an annual probability given a return period

    $$AEP = 1 - \exp{-1/ARI}$$

    :param ari: `float` or `np.array` of floats representing avrage recurrence
        intervals.
    """
    aep = 1.0 - np.exp(-1.0/ari)
    return aep


def load_iterations(filepath, group, filters=None):
    """
    Load a hazimp output file that contains multiple iterations of loss
    calculations and aggregate to a given level (given by the `group` arg). Rows
    can be filtered for specific groups (e.g. pass a list of LGA codes to
    `filters` and set the `group` arg to the corresponding attribute)

    :param str filepath: path to the file containing the data
    :param group: str or list of str containing attribute names used to
        aggregate the data
    :param list filters: (optional) list of attribute values to include in the
        aggregations.

    :returns: `pd.DataFrame` containing aggregated data (typically mean values
        for each group)
    """
    cols = [f"{x:03d}" for x in range(100)]
    cols.append(group)
    df = pd.read_csv(filepath)
    if filters:
        df = df.loc[df[group].isin(filters)]
    aggdf = df[cols].groupby(group).agg('mean')
    return aggdf

fulldflist = []
for ARI in ARIS:
    filepath = pjoin(BASEPATH, str(ARI), "iterations.csv")
    print(f"Loading {filepath}")
    df = load_iterations(filepath, "LGA_CODE", filters=LGA_CODES)
    df['ARI'] = ARI
    fulldflist.append(df)
    
fulldf = pd.concat(fulldflist)
fulldf = fulldf.set_index('ARI', append=True)

AALdf = pd.DataFrame()
aeps = probability(np.array(ARIS))

for idx, (LGA_CODE, LGA_NAME) in LGAs.iterrows():
    AALdf[LGA_NAME] = calculateAAL(fulldf.loc[LGA_CODE].drop('ARI', axis=1).T, aeps)
    
AALdf.to_csv(pjoin(OUTPATH, f"{TYPE}.AAL.LGA.csv"), ignore_index=True)
