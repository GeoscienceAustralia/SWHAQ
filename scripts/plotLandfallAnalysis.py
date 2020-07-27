import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
ticks = np.arange(0, 49, 2)

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)

for i, r in enumerate(rcps):
    for p in periods:
        ax[i].plot(df.xs(['GROUP1', r, p])['count_nanmean'], label=p)
        ax[i].set_title(f"GROUP1 - {r}")
        ax[i].set_xlim((22, 49))


ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1].set_xlim((22, 49))
ax[0].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rates_by_RCP.GROUP1.png"), bbox_inches='tight')

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)

for i, r in enumerate(rcps):
    for p in periods:
        ax[i].plot(df.xs(['GROUP2', r, p])['count_nanmean'], label=p)
        ax[i].set_title(f"GROUP2 - {r}")
        ax[i].set_xlim((22, 49))


ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP2', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1].set_xlim((22, 49))
ax[0].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rates_by_RCP.GROUP2.png"), bbox_inches='tight')

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)

for i, g in enumerate(groups):
    for p in periods:
        ax[i].plot(df.xs([g, 'RCP45', p])['count_nanmean'], label=p)
        ax[i].set_title(f"{g} - RCP45")
        ax[i].set_xlim((22, 49))

ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP45', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1].set_xlim((22, 49))

ax[0].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rates_by_group.RCP45.png"), bbox_inches='tight')

fig, ax = plt.subplots(2, 1, figsize=(16,9), sharex=True)
for i, g in enumerate(groups):
    for p in periods:
        ax[i].plot(df.xs([g, 'RCP85', p])['count_nanmean'], label=p)
        ax[i].set_title(f"{g} - RCP85")
        ax[i].set_xlim((22, 49))

ax[1].set_xticks(ticks)
ax[1].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1].set_xlim((22, 49))

ax[0].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rates_by_group.RCP85.png"), bbox_inches='tight')



var = 'count_nanmean'

fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharex=True, sharey=True)

for i, g in enumerate(groups):
    for j, r in enumerate(rcps):
        for p in periods:
            prjrate = df.xs([g, r, p])[var]
            ax[i, j].plot(prjrate, label=p)
        ax[i, j].set_title(f"{g} - {r}")
        ax[i, j].set_xlim((22, 46))


ax[1, 0].set_xticks(ticks)
ax[1, 0].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 0].set_xlim((22, 46))
ax[1, 1].set_xticks(ticks)
ax[1, 1].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 1].set_xlim((22, 46))
ax[0, 0].set_ylim((0, 1))
ax[0, 0].set_ylabel("Landfall rate (TCs/yr)")
ax[1, 0].set_ylim((0, 1))
ax[1, 0].set_ylabel("Landfall rate (TCs/yr)")

ax[0, 1].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rate_by_group_RCP.png"), bbox_inches='tight')

fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharex=True, sharey=True)

for i, g in enumerate(groups):
    for j, r in enumerate(rcps):
        baseidx = [g, r, '1981-2010']
        baserate = df.xs(baseidx)[var]
        for p in periods[1:]:
            prjrate = df.xs([g, r, p])[var]
            delta = 100 * (prjrate - baserate) / baserate
            ax[i, j].plot(delta, label=p)
        ax[i, j].set_title(f"{g} - {r}")
        ax[i, j].set_xlim((22, 46))


ax[1, 0].set_xticks(ticks)
ax[1, 0].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 0].set_xlim((22, 46))
ax[1, 1].set_xticks(ticks)
ax[1, 1].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 1].set_xlim((22, 46))
ax[0, 0].set_ylim((-100, 200))
ax[0, 0].set_ylabel("Relative change (%)")
ax[1, 0].set_ylim((-100, 200))
ax[1, 0].set_ylabel("Relative change (%)")

ax[0, 1].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rate_relative_change.png"), bbox_inches='tight')


var = 'count_nanmean'

fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharex=True, sharey=True)

for i, g in enumerate(groups):
    for j, r in enumerate(rcps):
        for p in periods:
            prjrate = df.xs([g, r, p])[['cat3_nanmean', 'cat4_nanmean', 'cat5_nanmean']].sum(axis=1)
            ax[i, j].plot(prjrate, label=p)
        ax[i, j].set_title(f"{g} - {r}")
        ax[i, j].set_xlim((22, 46))


ax[1, 0].set_xticks(ticks)
ax[1, 0].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 0].set_xlim((22, 46))
ax[1, 1].set_xticks(ticks)
ax[1, 1].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 1].set_xlim((22, 46))
ax[0, 0].set_ylim((0, 1))
ax[0, 0].set_ylabel("Landfall rate (TCs/yr)")
ax[1, 0].set_ylim((0, 1))
ax[1, 0].set_ylabel("Landfall rate (TCs/yr)")

ax[0, 1].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rate_by_group_RCP.STC.png"), bbox_inches='tight')

fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharex=True, sharey=True)

for i, g in enumerate(groups):
    for j, r in enumerate(rcps):
        baserate = df.xs([g, r, '1981-2010'])[['cat3_nanmean', 'cat4_nanmean', 'cat5_nanmean']].sum(axis=1)
        for p in periods[1:]:
            prjrate = df.xs([g, r, p])[['cat3_nanmean', 'cat4_nanmean', 'cat5_nanmean']].sum(axis=1)
            delta = 100 * (prjrate - baserate) / baserate
            ax[i, j].plot(delta, label=p)
        ax[i, j].set_title(f"{g} - {r}")
        ax[i, j].set_xlim((22, 46))


ax[1, 0].set_xticks(ticks)
ax[1, 0].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 0].set_xlim((22, 46))
ax[1, 1].set_xticks(ticks)
ax[1, 1].set_xticklabels(df.xs(['GROUP1', 'RCP85', p])['label'][ticks].fillna(''), rotation='vertical')
ax[1, 1].set_xlim((22, 46))
ax[0, 0].set_ylim((-100, 200))
ax[0, 0].set_ylabel("Relative change (%)")
ax[1, 0].set_ylim((-100, 200))
ax[1, 0].set_ylabel("Relative change (%)")

ax[0, 1].legend()
fig.tight_layout()
plt.savefig(os.path.join(basepath, "landfall_rate_relative_change.STC.png"), bbox_inches='tight')

