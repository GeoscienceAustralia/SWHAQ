import os
import xarray as xr
import pandas as pd
import geopandas as gpd


IN_DIR = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\hazard\projections"

GROUPS = ["GROUP1","GROUP2"]
RCPLIST=["RCP45","RCP85"]
PERIODS=["2021-2040","2041-2060","2061-2080","2081-2100"]
filename = os.path.join(IN_DIR, f"GROUP1_RCP45_2081-2100/hazard", "hazard_rel.nc")

stndf = gpd.read_file(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\reference_data\SEQ_station_list.shp")
stndf = pd.DataFrame(stndf.drop("geometry", axis=1))

ds = xr.open_dataset(filename)
ari = ds.ari.values
outdf = pd.DataFrame(columns=["stnID", "Place", "period", "RCP", *ari,])
outdf.set_index(['stnID', "Place", "period", "RCP"], inplace=True)
for GROUP in GROUPS:
    for RCP in RCPLIST:
        for PER in PERIODS:
            filename = os.path.join(IN_DIR, f"{GROUP}_{RCP}_{PER}/hazard", "hazard_rel.nc")
            print(filename)
            ds = xr.open_dataset(filename)
            for idx, row in stndf.iterrows():
                try:
                    df = ds.sel(lat=row.Latitude, lon=row.Longitude, method='nearest').to_dataframe()
                except:
                    breakpoint()
                relchange = df['wspd']
                outdf.loc[(idx, row.Place, PER, RCP),:] = relchange.values.T

    outdf.to_csv(os.path.join(IN_DIR, f"station_hazard_change_{GROUP}.csv"))
