#!/usr/bin/env python
"""
Split a full state NEXIS input file into selected communities

Based on SA2 codes for locations in the previous version of community NEXIS files.
"""

import os
from os.path import join as pjoin
import pandas as pd
import numpy as np
datapath = "C:/WorkSpace/swhaq/data/exposure"
kowdf = pd.read_csv(pjoin(datapath, "Kowanyama_and_Pompuraaw_ResidentialExposure_NEXISV10_M4_updated.csv"))
cnsdf = pd.read_csv(pjoin(datapath, "Cairns_ResidentialExposure_NEXISV10_M4_updated.csv"))
tsvdf = pd.read_csv(pjoin(datapath, "Townsville_ResidentialExposure_NEXISV10_M4_updated.csv"))
mkydf = pd.read_csv(pjoin(datapath, "Mackay_ResidentialExposure_NEXISV10_M4_updated.csv"))
gstdf = pd.read_csv(pjoin(datapath, "Gladstone_ResidentialExposure_NEXISV10_M4_updated.csv"))
glddf = pd.read_csv(pjoin(datapath, "GoldCoast_ResidentialExposure_NEXISV10_M4_updated.csv"))
kow_sa2_code = kowdf.SA2_CODE.unique()
cns_sa2_code = cnsdf.SA2_CODE.unique()
cns_sa2_code = np.append(cns_sa2_code, 318011462)
tsv_sa2_code = tsvdf.SA2_CODE.unique()

tsv_sa2_code = np.append(tsv_sa2_code, 318011462)
mky_sa2_code = mkydf.SA2_CODE.unique()
gst_sa2_code = gstdf.SA2_CODE.unique()
gld_sa2_code = glddf.SA2_CODE.unique()

qlddf = pd.read_csv(pjoin(datapath, "QLD_TILES_Residential_Wind_Exposure_2020_TCRM_M4.CSV"))
qlddf.drop("M4_2", axis=1, inplace=True)
qlddf[qlddf.SA2_CODE.isin(kow_sa2_code)].to_csv(pjoin(datapath, "Kowanyama_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(cns_sa2_code)].to_csv(pjoin(datapath, "Cairns_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(tsv_sa2_code)].to_csv(pjoin(datapath, "Townsville_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(mky_sa2_code)].to_csv(pjoin(datapath, "Mackay_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(gst_sa2_code)].to_csv(pjoin(datapath, "Gladstone_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(gld_sa2_code)].to_csv(pjoin(datapath, "GoldCoast_ResidentialExposure_NEXIS_2020_M4.csv"), index=False)

qlddf = pd.read_csv(pjoin(datapath, "QLD_TILES_Residential_Wind_Exposure_LUO_2020_TCRM_M4.CSV"))
qlddf.drop("M4_2", axis=1, inplace=True)
qlddf[qlddf.SA2_CODE.isin(kow_sa2_code)].to_csv(pjoin(datapath, "Kowanyama_ResidentialExposure_NEXIS_2020_LUO_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(cns_sa2_code)].to_csv(pjoin(datapath, "Cairns_ResidentialExposure_NEXIS_2020_LUO_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(tsv_sa2_code)].to_csv(pjoin(datapath, "Townsville_ResidentialExposure_NEXIS_2020_LUO_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(mky_sa2_code)].to_csv(pjoin(datapath, "Mackay_ResidentialExposure_NEXIS_2020_LUO_M4_.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(gst_sa2_code)].to_csv(pjoin(datapath, "Gladstone_ResidentialExposure_NEXIS_2020_LUO_M4.csv"), index=False)
qlddf[qlddf.SA2_CODE.isin(gld_sa2_code)].to_csv(pjoin(datapath, "GoldCoast_ResidentialExposure_NEXIS_2020_LUO_M4.csv"), index=False)

