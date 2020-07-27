import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import ttest_ind_from_stats as ttest

sns.set_style('whitegrid')
sns.set_palette('PuBuGn_d')
sns.set_context('talk')
basepath = "C:/WorkSpace/swhaq/data/tclv/landfall"

groups = ['GROUP1', 'GROUP2']
rcps = ['RCP45', 'RCP85']
periods = ['1981-2010', '2021-2040', '2041-2060', '2061-2080', '2081-2100']

df = pd.read_csv(os.path.join(basepath, 'GROUP1', 'RCP45', '1981-2010', 'simulated_landfall_rates.csv'))

df['model'] = 'GROUP1'
df['RCP'] = 'RCP45'
df['period'] = '1981-2010'

df = pd.DataFrame(columns=df.columns)

for g in groups:
    for r in rcps:
        for p in periods:
            d = pd.read_csv(os.path.join(basepath, g, r, p, 'simulated_landfall_rates.csv'))
            d['model'] = g
            d['RCP'] = r
            d['period'] = p
            df = df.append(d, ignore_index=True)

df = df.set_index(['model', 'RCP', 'period', 'gate'])

stats = pd.DataFrame(columns=['model', 'RCP', 'period', 'gate', 'label', 'pval', 'sig'])
for i, g in enumerate(groups):
    for j, r in enumerate(rcps):
        baseidx = [g, r, '1981-2010']
        baserate = df.xs(baseidx)
        for p in periods[1:]:
            prjrate = df.xs([g, r, p])
            for r1, r2 in zip(baserate.itertuples(), prjrate.itertuples()):
                tstat, pstat = ttest(r1.count_nanmean,
                                     r1.count_nanstd, 1000,
                                     r2.count_nanmean,
                                     r2.count_nanstd, 1000)
                stats = stats.append({'model': g,
                                      'RCP': r,
                                      'period': p,
                                      'gate': r1.Index,
                                      'label': r1.label,
                                      'pval': pstat,
                                      'sig': (pstat < 0.05)}, ignore_index=True)

stats.to_csv(os.path.join(basepath, "significance.csv"))