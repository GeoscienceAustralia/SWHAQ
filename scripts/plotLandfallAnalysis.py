import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
sns.set_palette('PuBuGn_d')

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
ticks = np.arange(0, 49, 2)
fig, ax = plt.subplots(1, 1, figsize=(16,9))
for p in periods:
    ax.plot(df.xs(['GROUP1', 'RCP45', p])['count_nanmean'], label=p)
    ax.set_xticks(ticks)
    ax.set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')

ax.legend()
plt.show()

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)

for i, r in enumerate(rcps):
    for p in periods:
        ax[i].plot(df.xs(['GROUP1', r, p])['count_nanmean'], label=p)
        ax[i].set_title(r)

ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[0].legend()
plt.show()

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)

for i, g in enumerate(groups):
    for p in periods:
        ax[i].plot(df.xs([g, 'RCP45', p])['count_nanmean'], label=p)
        ax[i].set_title(f"{g} - RCP 4.5")

ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[0].legend()
plt.show()

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)
for i, g in enumerate(groups):
    for p in periods:
        ax[i].plot(df.xs([g, 'RCP85', p])['count_nanmean'], label=p)
        ax[i].set_title(f"{g} - RCP 8.5")

ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[0].legend()
plt.show()
