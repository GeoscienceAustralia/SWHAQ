import os
import pandas as pd
import numpy as np
from scipy.integrate import simpson
from matplotlib import pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')
sns.set_context('talk')

LOSSFIELD = "structural_loss_sum"
BASEPATH = "C:/workspace/swhaq/data/risk"
ARIS = [1, 2, 3, 4, 5, 10, 15, 20, 30, 35, 40, 45, 50, 75,
        100, 150, 200, 250, 300, 350, 400, 450, 500, 1000,
        2000, 2500, 5000, 10000]
lossdf = pd.DataFrame(columns=["SA1_CODE", *ARIS])

def probability(ari):
    """Return an annual probability given a return period"""
    aep = 1.0 - np.exp(-1.0/ari)
    return aep

firstdf = pd.read_csv(os.path.join(BASEPATH, f"windspeed_2_yr_agg.csv"))
lossdf['SA1_CODE'] = firstdf['SA1_CODE_']
lossdf.set_index('SA1_CODE', inplace=True)

for ARI in ARIS:
    if ARI == 1: continue
    tmpdf = pd.read_csv(os.path.join(BASEPATH, f"windspeed_{ARI:d}_yr_agg.csv"))
    tmpdf.set_index('SA1_CODE_', inplace=True)
    lossdf = lossdf.join(tmpdf[LOSSFIELD])
    lossdf[ARI] = lossdf[LOSSFIELD]
    lossdf.drop(LOSSFIELD, axis=1, inplace=True)
lossdf[1] = 0

aeps = probability(np.array(lossdf.columns.to_list()))
lossdf['AAL'] = lossdf.apply(simpson, axis=1, x=-1*aeps)

fig, ax = plt.subplots(figsize=(12, 8))
sns.histplot(lossdf['AAL'], ax=ax)
ax.set_yscale('log')
plt.savefig(os.path.join(BASEPATH, f"AAL_{LOSSFIELD}.png"))

lossdf.to_csv(os.path.join(BASEPATH, f"AAL_{LOSSFIELD}.csv"))
