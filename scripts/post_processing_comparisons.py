import matplotlib
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from os.path import join as pjoin
from itertools import count
from scipy.stats import ttest_ind
from scipy.stats import ttest_ind_from_stats
from scipy.stats import chisquare
from matplotlib.lines import Line2D
from matplotlib.colors import LogNorm
matplotlib.use("Agg")
sns.set_context('talk', font_scale=1.5)

sns.set_style('ticks')
palette = sns.blend_palette(["#5E6A71", "#006983", "#72C7E7", "#A33F1F",
                             "#CA7700", "#A5D867", "#6E7645"], 7)
dmgpal = sns.blend_palette([(0.000, 0.627, 0.235), (0.412, 0.627, 0.235),
                            (0.663, 0.780, 0.282), (0.957, 0.812, 0.000),
                            (0.925, 0.643, 0.016), (0.835, 0.314, 0.118),
                            (0.780, 0.086, 0.118)], 5)
sns.set_palette(palette)

GA_colour = "#006983"

# change data path to whereever you want the files saved to
data_path = r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\retrofit\Comp"

# change events to whatever you are comparing or scenario numbers
events = ['retro_5_6LGA']

# input files for comparison (single building)
original_output = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\retrofit\None\004-08495\QFES_004-08495.csv")
new_output = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\retrofit\Retrofit5\004-08495\QFES_004-08495.csv")

# input files for comparison (aggregate)
original_output_agg = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\retrofit\None\004-08495\QFES_004-08495_agg.csv")
new_output_agg = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\8. USERS\u02618\retrofit\Retrofit5\004-08495\QFES_004-08495_agg.csv")

# vulnerability functions if needed
curve_data = pd.read_csv(r"X:\georisk\HaRIA_B_Wind\projects\qfes_swha\data\derived\vulnerability\domestic_wind_vul_curves_2022.csv")

LGAs_list = ['Noosa (S)','Sunshine Coast (R)','Moreton Bay (R)','Brisbane (C)','Gold Coast (C)','Redland (C)']

original_output = original_output[original_output.LGA_NAME.isin(LGAs_list) == True]
new_output = new_output[new_output.LGA_NAME.isin(LGAs_list) == True]

res = 600
context = 'paper'
fmt = "png"

# ###How do I make this work for multiple different input files????
# Made this a loop so that original output could be compared with
# multiple new outputs but can't figure out how to do this.
for event in events:
    print("Processing event {0}".format(event))

    output_path = pjoin(data_path, event)
    try:
        os.makedirs(output_path)
    except:
        pass

    YEAR_ORDER = ['None', 'Pre 1914', '1914 - 1946', '1947 - 1961',
                  '1962 - 1981', '1982 - 1996', '1997 - present']
    ROOF_TYPE_ORDER = ['None', 'Metal Sheeting', 'Tiles',
                       'Fibro / asbestos cement sheeting']
    WALL_TYPE_ORDER = ['None', 'Double Brick', 'Fibro / asbestos cement sheeting',
                       'Timber', 'Brick Veneer']
    DAMAGE_STATE_ORDER = ['None',
                          'Negligible',
                          'Slight',
                          'Moderate',
                          'Extensive',
                          'Complete']
    DAMAGE_STATE_ORDER2 = ['Negligible',
                           'Slight',
                           'Moderate',
                           'Extensive',
                           'Complete']

    wind_speed_bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    wind_speed_labels = ['<10',
                         '10 to 20',
                         '20 to 30',
                         '30 to 40',
                         '40 to 50',
                         '50 to 60',
                         '60 to 70',
                         '70 to 80',
                         '80 to 90',
                         '>=90']
    DS_bins = [0.0, 0.02, 0.1, 0.2, 0.5, 1.0]
    DS_dict = {'None': 0,
               'Negligible': 1,
               'Slight': 2,
               'Moderate': 3,
               'Extensive': 4,
               'Complete': 5}

    # rename columns in each dataset so that once they are
    # merged they will be easier to identify
    columns = list(original_output_agg.columns)
    columns[2:] = ["orig_" + c for c in original_output_agg.columns][2:]
    original_output_agg.columns = columns

    columns = list(new_output_agg.columns)
    columns[2:] = ["new_" + c for c in new_output_agg.columns][2:]
    new_output_agg.columns = columns

    columns = list(original_output.columns)
    columns[2:] = ["orig_" + c for c in original_output.columns][2:]
    original_output.columns = columns

    columns = list(new_output.columns)
    columns[2:] = ["new_" + c for c in new_output.columns][2:]
    new_output.columns = columns

    b = original_output.groupby('orig_SA1_CODE').count()
    b.drop(b.iloc[:, 1:], inplace=True, axis=1)
    b.columns.values[0] = 'orig_building_count'
    original_output_agg = pd.merge(original_output_agg, b,
                                   how='inner', left_on='SA1_CODE_',
                                   right_on='orig_SA1_CODE')

    c = new_output.groupby('new_SA1_CODE').count()
    c.drop(c.iloc[:, 1:], inplace=True, axis=1)
    c.columns.values[0] = 'new_building_count'
    new_output_agg = pd.merge(new_output_agg, c,
                              how='inner', left_on='SA1_CODE_',
                              right_on='new_SA1_CODE')

    # join the single building datasets and the agg datasets
    # merge on inner so that only buildings and SA1s that are present
    # in both data are compared.
    # if comparing different hazard scenarios merge on outer
    Comp_agg = pd.merge(original_output_agg, new_output_agg,
                        how='outer', on='SA1_CODE_')
    Comp_all = pd.merge(original_output, new_output,
                        how='outer', left_on='orig_LID',
                        right_on='new_LID')
    Comp_agg = Comp_agg.fillna(0)
    Comp_all = Comp_all.fillna({'orig_AS4055_CLASS': 'None',
                                'orig_ROOF_TYPE': 'None',
                                'orig_YEAR_BUILT': 'None',
                                'orig_LID': 'None',
                                'orig_MB_CAT': 'None',
                                'orig_SA2_NAME': 'None',
                                'orig_SA3_NAME': 'None',
                                'orig_SA4_NAME': 'None',
                                'orig_UCL_NAME': 'None',
                                'orig_GCC_CODE': 'None',
                                'orig_GCC_NAME': 'None',
                                'orig_SUBURB': 'None',
                                'orig_CONSTRUCTION_TYPE': 'None',
                                'orig_WALL_TYPE': 'None',
                                'orig_WIND_VULNERABILITY_FUNCTION_ID': 'None',
                                'orig_WIND_VULNERABILITY_SET': 'None',
                                'orig_Damage state': 'None',
                                'new_AS4055_CLASS': 'None',
                                'new_ROOF_TYPE': 'None',
                                'new_YEAR_BUILT': 'None',
                                'new_LID': 'None',
                                'new_MB_CAT': 'None',
                                'new_SA2_NAME': 'None',
                                'new_SA3_NAME': 'None',
                                'new_SA4_NAME': 'None',
                                'new_UCL_NAME': 'None',
                                'new_GCC_CODE': 'None',
                                'new_GCC_NAME': 'None',
                                'new_SUBURB': 'None',
                                'new_CONSTRUCTION_TYPE': 'None',
                                'new_WALL_TYPE': 'None',
                                'new_WIND_VULNERABILITY_FUNCTION_ID': 'None',
                                'new_WIND_VULNERABILITY_SET': 'None',
                                'new_Damage state': 'None'}).fillna(0)
    Comp_all['orig_LGA_NAME'] = np.where(Comp_all['orig_LGA_NAME'] == 0, Comp_all['new_LGA_NAME'], Comp_all['orig_LGA_NAME'])
    Comp_all['orig_LGA_CODE'] = np.where(Comp_all['orig_LGA_CODE'] == 0, Comp_all['new_LGA_CODE'], Comp_all['orig_LGA_CODE'])
    Comp_all['new_LGA_NAME'] = np.where(Comp_all['new_LGA_NAME'] == 0, Comp_all['orig_LGA_NAME'], Comp_all['new_LGA_NAME'])
    Comp_all['new_LGA_CODE'] = np.where(Comp_all['new_LGA_CODE'] == 0, Comp_all['orig_LGA_CODE'], Comp_all['new_LGA_CODE'])
    Comp_agg.drop(['FID_x', 'FID_y'], axis=1, inplace=True)

    # calculate the change in structural loss statistics for agg
    Comp_agg['dif_structural_mean'] = \
        Comp_agg['new_structural_mean'] - Comp_agg['orig_structural_mean']
    Comp_agg['dif_structural_max'] = \
        Comp_agg['new_structural_max'] - Comp_agg['orig_structural_max']
    Comp_agg['dif_structural_std'] = \
        Comp_agg['new_structural_std'] - Comp_agg['orig_structural_std']
    Comp_agg['dif_structural_loss_mean'] = \
        Comp_agg['new_structural_loss_mean'] - \
        Comp_agg['orig_structural_loss_mean']
    Comp_agg['dif_structural_loss_sum'] = \
        Comp_agg['new_structural_loss_sum'] - \
        Comp_agg['orig_structural_loss_sum']

    # calculate the damage state for original and new outputs
    # and see if there is a change in damage state for agg
    Comp_agg['orig_damage state'] = pd.cut(Comp_agg['orig_structural_mean'],
                                           DS_bins, right=False,
                                           labels=DAMAGE_STATE_ORDER2)
    Comp_agg['new_damage state'] = pd.cut(Comp_agg['new_structural_mean'],
                                          DS_bins, right=False,
                                          labels=DAMAGE_STATE_ORDER2)
    Comp_agg['dif_DS'] = np.where(Comp_agg['orig_damage state'] ==
                                  Comp_agg['new_damage state'], False, True)
    

    # calculate mean wind speed in each SA1 and bin
    fields = ['orig_SA1_CODE']
    w_agg = Comp_all.groupby(fields).\
        agg({'orig_0.2s gust at 10m height m/s': np.mean}).\
        dropna()
    w_agg = pd.DataFrame(w_agg)
    w_agg = w_agg.reset_index(level=0)
    w_agg = w_agg.rename({'orig_SA1_CODE': 'SA1_CODE_',
                          'orig_0.2s gust at 10m height m/s':
                          'mean 0.2s gust at 10m height m/s'}, axis='columns')
    Comp_agg = pd.merge(Comp_agg, w_agg, how='inner', on='SA1_CODE_')
    Comp_agg['wind_bins'] = pd.cut(
        Comp_agg['mean 0.2s gust at 10m height m/s'],
        wind_speed_bins, right=False,
        labels=wind_speed_labels)

    # calculating the difference between the structural loss ratio
    # and if there is a difference in damage state for all buildings
    Comp_all['dif_structural'] = \
        Comp_all['new_structural'] - Comp_all['orig_structural']
    Comp_all['dif_structural_loss'] = \
        Comp_all['new_structural_loss'] - Comp_all['orig_structural_loss']
    Comp_all['dif_DS'] = np.where(
        Comp_all['orig_Damage state'] == Comp_all['new_Damage state'],
        False, True)
    Comp_all['orig_DS'] = Comp_all['orig_Damage state']
    Comp_all['new_DS'] = Comp_all['new_Damage state']
    Comp_all.replace({'orig_DS': DS_dict}, inplace=True)
    Comp_all.replace({'new_DS': DS_dict}, inplace=True)
    Comp_all['DS_change'] = Comp_all['new_DS'] - Comp_all['orig_DS']
    Comp_all['wind_bins'] = pd.cut(
        Comp_all['orig_0.2s gust at 10m height m/s'],
        wind_speed_bins, right=False,
        labels=wind_speed_labels)

    LGA_agg1 = Comp_all.groupby('orig_LGA_NAME').agg({'orig_structural': ['mean', 'std', 'count']})
    LGA_agg1 = LGA_agg1.xs('orig_structural', axis=1, drop_level=True)
    LGA_agg1 = LGA_agg1.rename(columns={'mean': 'orig_mean', 'std': 'orig_std', 'count': 'orig_count'})
    LGA_agg2 = Comp_all.groupby('orig_LGA_NAME').agg({'new_structural': ['mean', 'std', 'count']})
    LGA_agg2 = LGA_agg2.xs('new_structural', axis=1, drop_level=True)
    LGA_agg2 = LGA_agg2.rename(columns={'mean': 'new_mean', 'std': 'new_std', 'count': 'new_count'})
    LGA_agg = pd.merge(LGA_agg1, LGA_agg2,
                       how='inner', on='orig_LGA_NAME')
    LGA_agg = LGA_agg.reset_index('orig_LGA_NAME')
    
    # assign names to dfs
    Comp_all.name = 'Comp_all'
    Comp_agg.name = 'Comp_agg'

    # save these files to csv
    Comp_all.to_csv(pjoin(output_path, 'general', f"{event}_Comp_all.csv"))
    Comp_agg.to_csv(pjoin(output_path, 'general', f"{event}_Comp_agg.csv"))

    # -----------------------------------------------------
    # ####Functions for figures and plots####
    # Groupby, pivot tables, some attribute change by damage state change (for if attributes and damage state have both changed)
    def groupby_pivot_table(df,orig_col,new_col,orig_DS,new_DS):
        n_df = df.groupby([orig_col,
                        new_col,
                        orig_DS,
                        new_DS]).\
                size().reindex(DAMAGE_STATE_ORDER, level=orig_DS).\
                reindex(DAMAGE_STATE_ORDER, level=new_DS).\
                reset_index(name='counts').\
                dropna()
        n_df[orig_DS] = n_df[orig_DS].\
            astype(pd.api.types.CategoricalDtype(categories=DAMAGE_STATE_ORDER))
        n_df[new_DS] = n_df[new_DS].\
            astype(pd.api.types.CategoricalDtype(categories=DAMAGE_STATE_ORDER))    
        n_df = n_df.pivot_table(index=[orig_col,
                                    new_col,
                                    orig_DS],
                            columns=new_DS,
                            values='counts',
                            fill_value=0)
        n_df.to_csv(pjoin(output_path, 'vulnerability',
                f"{event}_{df.name}_damage_state_change_{orig_col}_change.csv"),
                float_format="%0.3f")

    # groupby, pivot table, change in some attribute from original dataset to new dataset
    def single_cat_change(df,orig_col,new_col):
        n_df = df.groupby([orig_col,
                        new_col]).\
            size().reset_index(name='counts').\
            dropna()
        n_df = n_df.pivot_table(index=[orig_col],
                            columns=new_col,
                            values='counts',
                            fill_value=0)
        n_df.to_csv(pjoin(output_path, 'exposure',
                f"{event}_{df.name}_{orig_col}_change.csv"),
                float_format="%0.3f")

    # groupby, pivot table, change in damage state only
    def damage_state_change(df,orig_DS,new_DS):
        n_df = df.groupby([orig_DS,
                        new_DS]).size().\
            reindex(DAMAGE_STATE_ORDER, level=orig_DS).\
            reindex(DAMAGE_STATE_ORDER, level=new_DS).\
            reset_index(name='counts').\
            dropna()
        cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
        n_df[orig_DS] = n_df[orig_DS].astype(cat_type)
        n_df[new_DS] = n_df[new_DS].astype(cat_type)
        n_df = n_df.pivot_table(index=orig_DS,
                            columns=new_DS,
                            values='counts',
                            fill_value=0)
        n_df.to_csv(pjoin(output_path, 'general',
                f"{event}_{df.name}_damage_state_change.csv"),
                float_format="%0.3f")
    
    # groupby, pivot table, change in damage state by original single attribute (for is damage state has changed and attributes have not changed)
    def damage_state_change_by_cat(df, orig_col,orig_DS,new_DS):
        n_df = df.groupby([orig_col,
                        orig_DS,
                        new_DS]).size().\
            reindex(DAMAGE_STATE_ORDER, level=orig_DS).\
            reindex(DAMAGE_STATE_ORDER, level=new_DS).\
            reset_index(name='counts').\
            dropna()
        cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
        n_df[orig_DS] = n_df[orig_DS].astype(cat_type)
        n_df[new_DS] = n_df[new_DS].astype(cat_type)
        n_df = n_df.pivot_table(index=[orig_col, orig_DS],
                            columns=new_DS,
                            values='counts',
                            fill_value=0)
        n_df.to_csv(pjoin(output_path, 'vulnerability',
                f"{event}_{df.name}_damage_state_{orig_col}.csv"),
                float_format="%0.3f")

    # histograms for single attribute in all data and agg data
    def histogram_all(df,hist_col,x_lab):
        fig, ax = plt.subplots(figsize=(16, 9))
        g = sns.histplot(data=[hist_col],
                        bins=int(len(df)/500),
                        stat=('count'),
                        facecolor=GA_colour)
        ax.set_ylabel("count")
        ax.set_xlabel(x_lab)
        ax.set_yscale('log')
        plt.savefig(pjoin(output_path, 'general',
                    f"{event}_{df.name}_Hist_{hist_col}".format(fmt)), dpi=res)
        plt.close(fig)

    def histogram_agg(df,hist_col,x_lab):
        fig, ax = plt.subplots(figsize=(16, 9))
        g = sns.histplot(data=[hist_col],
                        stat=('count'),
                        facecolor=GA_colour)
        ax.set_ylabel("count")
        ax.set_xlabel(x_lab)
        ax.set_yscale('log')
        plt.savefig(pjoin(output_path, 'general',
                    f"{event}_{df.name}_Hist_{hist_col}".format(fmt)), dpi=res)
        plt.close(fig)

    # boxplot comparison of single attribute and histograms using boxplot data
    def box_plot(df,orig_col,new_col,ID,x_lab,y_lab):
        box_data = df.rename(columns={orig_col: 'original', new_col: 'new'})
        box_data = pd.melt(box_data, id_vars=[ID], value_vars=['original', 'new'])
        fig, ax = plt.subplots(figsize=(16, 9))
        g2 = sns.boxplot(data=box_data,
                        x='variable',
                        y='value')
        ax.set_xlabel(x_lab)
        ax.set_ylabel(y_lab)
        plt.savefig(pjoin(output_path, 'general',
                    f"{event}_{df.name}_box_plot_{orig_col}".format(fmt)),
                    dpi=res, bbox_inches="tight")

    # Comparison density histogram (can compare data sets with
    # different sample size)
    def density_hist(df,orig_col,new_col,ID,x_lab):
        box_data = df.rename(columns={orig_col: 'original', new_col: 'new'})
        box_data = pd.melt(box_data, id_vars=[ID], value_vars=['original', 'new'])
        fig2, ax2 = plt.subplots(figsize=(16, 9))
        g4 = sns.histplot(data=box_data,
                        x='value',
                        hue='variable',
                        stat='density',
                        common_norm=False)
        ax.set_xlabel(x_lab)
        ax.set_yscale('log')
        plt.savefig(pjoin(output_path, 'general',
                    f"{event}_{df.name}_hist_{orig_col}".format(fmt)),
                    dpi=res, bbox_inches="tight")
        plt.close(fig)

    # Kernel density comparison plots individual buildings
    def kernel_density(df,orig_col,new_col,ID,x_lab):
        box_data = df.rename(columns={orig_col: 'original', new_col: 'new'})
        box_data = pd.melt(box_data, id_vars=[ID], value_vars=['original', 'new'])
        fig, ax = plt.subplots(figsize=(16, 9))
        g6 = sns.kdeplot(data=box_data,
                        x='value',
                        hue='variable',
                        common_norm=False)
        ax.set_xlabel(x_lab)
        plt.savefig(pjoin(output_path, 'general',
                    f"{event}_kernel_structural_all".format(fmt)),
                    dpi=res, bbox_inches="tight")
    
    #end of functions
    # -----------------------------------------------------
    
    
    
    
    # The following tables and plots can be used for
    # most comparisons

    # ######Change in structural loss ratio#######

    # canculate statistics (min, mean, etc) for the difference in
    # structural loss ratio for all buildings and the
    # structural loss ratio mean for the aggregate SA1 dataset
    Max_agg = Comp_agg['dif_structural_mean'].max()
    Min_agg = Comp_agg['dif_structural_mean'].min()
    Mean_agg = Comp_agg['dif_structural_mean'].mean()
    Mode_agg = Comp_agg['dif_structural_mean'].mode()
    Mode_agg = Mode_agg.to_numpy()[0]
    Median_agg = Comp_agg['dif_structural_mean'].median()
    Std_agg = Comp_agg['dif_structural_mean'].std()
    Count_neg_agg = (Comp_agg['dif_structural_mean'] < 0).sum()
    Count_pos_agg = (Comp_agg['dif_structural_mean'] > 0).sum()
    Count_zero_agg = (Comp_agg['dif_structural_mean'] == 0).sum()

    Max_all = Comp_all['dif_structural'].max()
    Min_all = Comp_all['dif_structural'].min()
    Mean_all = Comp_all['dif_structural'].mean()
    Mode_all = Comp_all['dif_structural'].mode()
    Mode_all = Mode_all.to_numpy()[0]
    Median_all = Comp_all['dif_structural'].median()
    Std_all = Comp_all['dif_structural'].std()
    Count_neg_all = (Comp_all['dif_structural'] < 0).sum()
    Count_pos_all = (Comp_all['dif_structural'] > 0).sum()
    Count_zero_all = (Comp_all['dif_structural'] == 0).sum()

    Stats = pd.DataFrame({"Dataset": ["Agg", "All"],
                          "Max": [Max_agg, Max_all],
                          "Min": [Min_agg, Min_all],
                          "Mean": [Mean_agg, Mean_all],
                          "Mode": [Mode_agg, Mode_all],
                          "Median": [Median_agg, Median_all],
                          "Std": [Std_agg, Std_all],
                          "Count negative": [Count_neg_agg, Count_neg_all],
                          "Count positive": [Count_pos_agg, Count_pos_all],
                          "Count zero": [Count_zero_agg, Count_zero_all]})
    Stats.set_index("Dataset", inplace=True)
    Stats.to_csv(pjoin(output_path, 'general',
                 f"{event}_dif_structural_loss_ratio_stats.csv"))

    # Plotting the difference in structural loss ratio
    # as a histogram. All buildings
    histogram_all(Comp_all,'dif_structural',"Difference in structural loss ratio")

    # Plotting the difference in structural loss ratio mean as a histogram
    # SA1 aggregate
    histogram_agg(Comp_agg,'dif_structural_mean',"Difference in structural loss ratio mean")

    # box plot comparisons of structural loss ratio
    # for individual buildings
    # Comparison density histogram (can compare data sets with
    # different sample size) of structural loss ratio for individual buildings
    # Kernel density comparison plots individual buildings
    box_plot(Comp_all,'orig_structural','new_structural','orig_SA1_CODE','Data set','Structural loss ratio')
    density_hist(Comp_all,'orig_structural','new_structural','orig_SA1_CODE','Structural loss ratio')
    kernel_density(Comp_all,'orig_structural','new_structural','orig_SA1_CODE','Structural loss ratio')

    # box plot comparisons of structural loss ratio
    # for SA1 agg
    # Comparison density histogram (can compare data sets with
    # different sample size) of structural loss ratio for SA1 agg
    # Kernel density comparison plots SA1 agg
    box_plot(Comp_agg,'orig_structural_mean','new_structural_mean','SA1_CODE_','Data set','Structural loss ratio')
    density_hist(Comp_agg,'orig_structural_mean','new_structural_mean','SA1_CODE_','Structural loss ratio')
    kernel_density(Comp_agg,'orig_structural_mean','new_structural_mean','SA1_CODE_','Structural loss ratio')

    # t test individual buildings
    box_data = Comp_all.rename(columns={'orig_structural': 'original', 'new_structural': 'new'})
    box_data = pd.melt(box_data, id_vars=['orig_SA1_CODE'], value_vars=['original', 'new'])
    struc_loss = box_data['value'].values
    struc_loss_O = box_data.loc[box_data.variable == 'original', 'value'].values
    struc_loss_N = box_data.loc[box_data.variable == 'new', 'value'].values
    g8 = stat, p_value = ttest_ind(struc_loss_O, struc_loss_N)
    t1 = [g8[0],g8[1]]
    t2 = pd.DataFrame(t1).transpose()
    t2.columns = ['statisitc','pvalue']
    t2.to_csv(pjoin(output_path, 'general',
              f"{event}_t_test_all.csv"),
              float_format="%0.7f")

    # t test SA1 agg
    def func_t(x):
        try:
            return ttest_ind_from_stats(mean1=x['orig_structural_mean'],
                                        std1=x['orig_structural_std'],
                                        nobs1=x['orig_building_count'],
                                        mean2=x['new_structural_mean'],
                                        std2=x['new_structural_std'],
                                        nobs2=x['new_building_count'],)
        except ZeroDivisionError:
            return 0

    ttest = Comp_agg.set_index('SA1_CODE_').apply(lambda x: func_t(x), axis=1, result_type='expand')
    ttest.rename(columns={ttest.columns[0]: 't statistic'}, inplace=True)
    ttest.rename(columns={ttest.columns[1]: 'p-value'}, inplace=True)
    Comp_agg_t_test = pd.merge(Comp_agg, ttest, how='inner', on='SA1_CODE_')
    Comp_agg_t_test.to_csv(pjoin(output_path, 'general',
                    f"{event}_t_test_SA1_agg.csv"),
                    float_format="%0.7f")

    # t test LGA agg
    def func_t(x):
        try:
            return ttest_ind_from_stats(mean1=x['orig_mean'],
                                        std1=x['orig_std'],
                                        nobs1=x['orig_count'],
                                        mean2=x['new_mean'],
                                        std2=x['new_std'],
                                        nobs2=x['new_count'])
        except ZeroDivisionError:
            return 0

    ttest2 = LGA_agg.set_index('orig_LGA_NAME').apply(lambda x: func_t(x), axis=1, result_type='expand')
    ttest2.rename(columns={ttest2.columns[0]: 't statistic'}, inplace=True)
    ttest2.rename(columns={ttest2.columns[1]: 'p-value'}, inplace=True)
    LGA_agg = pd.merge(LGA_agg, ttest2, how='inner', on='orig_LGA_NAME')
    LGA_agg.to_csv(pjoin(output_path, 'general',
                   f"{event}_t_test_LGA_agg.csv"),
                   float_format="%0.7f")

    # histogram of p-value distribution
    fig, ax = plt.subplots(figsize=(16, 9))
    g9 = sns.histplot(data=Comp_agg_t_test['p-value'],
                      stat=('count'),
                      bins=50,
                      facecolor=GA_colour)
    ax.set_ylabel("count")
    ax.set_xlabel("p-value")
    plt.savefig(pjoin(output_path, 'general',
                f"{event}_Hist_p_value_agg".format(fmt)), dpi=res)
    plt.close(fig)

    # p-value stats
    Max_p = Comp_agg_t_test['p-value'].max()
    Min_p = Comp_agg_t_test['p-value'].min()
    Mean_p = Comp_agg_t_test['p-value'].mean()
    Mode_p = Comp_agg_t_test['p-value'].mode()
    Mode_p = Mode_p.to_numpy()[0]
    Median_p = Comp_agg_t_test['p-value'].median()
    Std_p = Comp_agg_t_test['p-value'].std()
    Count_total = (Comp_agg_t_test['p-value'] > 0).sum()
    Count_less_0_01 = (Comp_agg_t_test['p-value'] < 0.01).sum()
    Count_less_0_05 = (Comp_agg_t_test['p-value'] < 0.05).sum()
    Count_less_0_1 = (Comp_agg_t_test['p-value'] < 0.1).sum()

    pStats = pd.DataFrame({"Index": ["p-value"],
                           "Max": [Max_p],
                           "Min": [Min_p],
                           "Mean": [Mean_p],
                           "Mode": [Mode_p],
                           "Median": [Median_p],
                           "Std": [Std_p],
                           "count total": [Count_total],
                           "Count less than 0.01": [Count_less_0_01],
                           "Count less than 0.05": [Count_less_0_05],
                           "Count less than 0.1": [Count_less_0_1]})
    pStats.set_index("Index", inplace=True)
    pStats.to_csv(pjoin(output_path, 'general',
                  f"{event}_p_value_stats.csv"))

    # chi squared test
    # Init dataframe
    df_bins = pd.DataFrame()
    # Generate bins from control group
    _, bins = pd.qcut(struc_loss_O, q=10, retbins=True, duplicates='drop')
    df_bins['bin'] = pd.cut(struc_loss_O, bins=bins).value_counts().index
    # Apply bins to both groups
    df_bins['struc_loss_O_observed'] = pd.cut(struc_loss_O, bins=bins).value_counts().values
    df_bins['struc_loss_N_observed'] = pd.cut(struc_loss_N, bins=bins).value_counts().values
    # Compute expected frequency in the treatment group
    df_bins['struc_loss_N_expected'] = df_bins['struc_loss_O_observed'] / np.sum(df_bins['struc_loss_O_observed']) * np.sum(df_bins['struc_loss_N_observed'])
    df_bins
    g9 = stat, p_value = chisquare(df_bins['struc_loss_N_observed'], df_bins['struc_loss_N_expected'])

    # LGAs
    LGAs = LGAs_list
    Noosa = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Noosa (S)']
    Noosa.name = 'Noosa'
    Sunshine_Coast = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Sunshine Coast (R)']
    Sunshine_Coast.name = 'Sunshine_Coast'
    Moreton_Bay = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Moreton Bay (R)']
    Moreton_Bay.name = 'Moreton_Bay'
    Brisbane = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Brisbane (C)']
    Brisbane.name = 'Brisbane'
    Gold_Coast = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Gold Coast (C)']
    Gold_Coast.name = 'Gold_Coast'
    Redland = Comp_all.loc[Comp_all['orig_LGA_NAME'] == 'Redland (C)']
    Redland.name = 'Redland'

    # damage state change
    damage_state_change(Comp_all,'orig_Damage state','new_Damage state')

    # damage state change agg
    damage_state_change(Comp_agg,'orig_damage state','new_damage state')

    # damage state change by vuln function
    damage_state_change_by_cat(Comp_all, "orig_WIND_VULNERABILITY_FUNCTION_ID", "orig_Damage state", "new_Damage state")

    # damage state change by wind speed with min max, structural loss ratio
    fields = ['orig_SA1_CODE',
              'orig_WIND_VULNERABILITY_FUNCTION_ID',
              'orig_Damage state',
              'new_Damage state']
    Comp_all.groupby(fields).\
        agg({'orig_0.2s gust at 10m height m/s': [np.min, np.max, np.mean],
             'orig_structural': [np.min, np.max, np.mean],
             'new_structural': [np.min, np.max, np.mean],
             'orig_SA1_CODE': len}).\
        dropna().\
        to_csv(pjoin(output_path, 'general',
               f"{event}_mean_dmg_windspeed_SA1.csv"),
               float_format="%0.3f")

    # ######Individual building and SA1 damage state comparison plots#######

    original_DS = Comp_all.groupby(['orig_Damage state']).size().\
        reset_index(name='counts').\
        dropna()
    cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
    original_DS['orig_Damage state'] = \
        original_DS['orig_Damage state'].astype(cat_type)
    original_DS['comparison'] = 'Original damage State'
    original_DS = original_DS. \
        rename(columns={'orig_Damage state': 'Damage state'})

    new_DS = Comp_all.groupby(['new_Damage state']).size().\
        reset_index(name='counts').\
        dropna()
    cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
    new_DS['new_Damage state'] = new_DS['new_Damage state'].astype(cat_type)
    new_DS['comparison'] = 'New damage State'
    new_DS = new_DS.rename(columns={'new_Damage state': 'Damage state'})

    DS_plot = pd.concat([original_DS, new_DS])

    fig, ax = plt.subplots()
    g = sns.catplot(kind='bar',
                    x='Damage state',
                    order=DAMAGE_STATE_ORDER,
                    y='counts',
                    data=DS_plot,
                    hue='comparison',
                    legend=False,
                    height=9,
                    aspect=16/9)
    plt.title('Damage state comparison')
    plt.legend(title="", loc='upper right')
    plt.savefig(pjoin(output_path, 'general',
                f"{event}_damage_state_plot".format(fmt)),
                dpi=res, bbox_inches="tight")
    plt.close(fig)

    original_DS_agg = Comp_agg.groupby(['orig_damage state']).size().\
        reset_index(name='counts').\
        dropna()
    cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
    original_DS_agg['orig_damage state'] = \
        original_DS_agg['orig_damage state'].astype(cat_type)
    original_DS_agg['comparison'] = 'Original damage State'
    original_DS_agg = original_DS_agg.\
        rename(columns={'orig_damage state': 'Damage state'})

    new_DS_agg = Comp_agg.groupby(['new_damage state']).size().\
        reset_index(name='counts').\
        dropna()
    cat_type = pd.CategoricalDtype(categories=DAMAGE_STATE_ORDER, ordered=True)
    new_DS_agg['new_damage state'] = new_DS_agg['new_damage state'].\
        astype(cat_type)
    new_DS_agg['comparison'] = 'New damage State'
    new_DS_agg = new_DS_agg.\
        rename(columns={'new_damage state': 'Damage state'})

    DS_plot_agg = pd.concat([original_DS_agg, new_DS_agg])

    fig, ax = plt.subplots()
    g = sns.catplot(kind='bar',
                    x='Damage state',
                    order=DAMAGE_STATE_ORDER,
                    y='counts',
                    data=DS_plot_agg,
                    hue='comparison',
                    legend=False,
                    height=9,
                    aspect=16/9)
    plt.title('Damage state comparison, SA1 aggrigated')
    plt.legend(title="", loc='upper right')
    plt.savefig(pjoin(output_path, 'general',
                f"{event}_damage_state_plot_agg".format(fmt)),
                dpi=res, bbox_inches="tight")
    plt.close(fig)

    # ---------------------------------------------
    # The following can be used for comparisons where
    # vulnerability models have been changed
    # (these assume exposure and hazard remain the same)

    # damage state change by age
    damage_state_change_by_cat(Comp_all,"orig_YEAR_BUILT","orig_Damage state","new_Damage state")

    # damage state change by roof type
    damage_state_change_by_cat(Comp_all,"orig_ROOF_TYPE","orig_Damage state","new_Damage state")

    # damage state change by wall type
    damage_state_change_by_cat(Comp_all,"orig_WALL_TYPE","orig_Damage state","new_Damage state")

    # damage state change by wind speed
    damage_state_change_by_cat(Comp_all,"wind_bins","orig_Damage state","new_Damage state")

    # damage state change by wind speed agg
    damage_state_change_by_cat(Comp_agg,"wind_bins","orig_damage state","new_damage state")

    # vulnerability model change
    single_cat_change(Comp_all,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID")

    # damage state change by vulnerability model change
    groupby_pivot_table(Comp_all,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")

    # ---------------------------------------------
    # The following can be used for comparisons where
    # exposure data have been changed

    # roof type change
    single_cat_change(Comp_all,'orig_ROOF_TYPE','new_ROOF_TYPE')
    
    # wall type change
    single_cat_change(Comp_all,'orig_WALL_TYPE','new_WALL_TYPE')

    # year built change
    single_cat_change(Comp_all,'orig_YEAR_BUILT','new_YEAR_BUILT')

    # use cat change
    single_cat_change(Comp_all,'orig_MB_CAT','new_MB_CAT')

    # damage state change by AS4055 change
    groupby_pivot_table(Comp_all,"orig_AS4055_CLASS","new_AS4055_CLASS","orig_Damage state","new_Damage state")

    # AS4055 class change
    single_cat_change(Comp_all,'orig_AS4055_CLASS','new_AS4055_CLASS')

    # damage state change by roof type change
    groupby_pivot_table(Comp_all,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    
    # damage state change by wall type change    
    groupby_pivot_table(Comp_all,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")

    # damage state change by age type change
    groupby_pivot_table(Comp_all,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")

    # damage state change by use cat type change
    groupby_pivot_table(Comp_all,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")

    # damage state change each of 6 LGAs
    damage_state_change(Brisbane,'orig_Damage state','new_Damage state')
    damage_state_change(Gold_Coast,'orig_Damage state','new_Damage state')
    damage_state_change(Moreton_Bay,'orig_Damage state','new_Damage state')
    damage_state_change(Noosa,'orig_Damage state','new_Damage state')
    damage_state_change(Redland,'orig_Damage state','new_Damage state')
    damage_state_change(Sunshine_Coast,'orig_Damage state','new_Damage state')

    # damage state change by roof type change
    groupby_pivot_table(Brisbane,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Gold_Coast,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Noosa,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Moreton_Bay,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Redland,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Sunshine_Coast,"orig_ROOF_TYPE","new_ROOF_TYPE","orig_Damage state","new_Damage state")

    # damage state change by wall type change
    groupby_pivot_table(Brisbane,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Gold_Coast,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Noosa,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Moreton_Bay,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Redland,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")
    groupby_pivot_table(Sunshine_Coast,"orig_WALL_TYPE","new_WALL_TYPE","orig_Damage state","new_Damage state")

    # damage state change by age type change
    groupby_pivot_table(Brisbane,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Gold_Coast,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Noosa,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Moreton_Bay,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Redland,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Sunshine_Coast,"orig_YEAR_BUILT","new_YEAR_BUILT","orig_Damage state","new_Damage state")

    # damage state change by use cat type change
    groupby_pivot_table(Brisbane,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Gold_Coast,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Noosa,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Moreton_Bay,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Redland,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")
    groupby_pivot_table(Sunshine_Coast,"orig_MB_CAT","new_MB_CAT","orig_Damage state","new_Damage state")

    # damage state change by use wind vulnerability function
    groupby_pivot_table(Brisbane,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")
    groupby_pivot_table(Gold_Coast,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")
    groupby_pivot_table(Noosa,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")
    groupby_pivot_table(Moreton_Bay,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")
    groupby_pivot_table(Redland,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")
    groupby_pivot_table(Sunshine_Coast,"orig_WIND_VULNERABILITY_FUNCTION_ID","new_WIND_VULNERABILITY_FUNCTION_ID","orig_Damage state","new_Damage state")

    # roof type change
    single_cat_change(Brisbane,'orig_ROOF_TYPE','new_ROOF_TYPE')
    single_cat_change(Gold_Coast,'orig_ROOF_TYPE','new_ROOF_TYPE')
    single_cat_change(Moreton_Bay,'orig_ROOF_TYPE','new_ROOF_TYPE')
    single_cat_change(Noosa,'orig_ROOF_TYPE','new_ROOF_TYPE')
    single_cat_change(Redland,'orig_ROOF_TYPE','new_ROOF_TYPE')
    single_cat_change(Sunshine_Coast,'orig_ROOF_TYPE','new_ROOF_TYPE')
    
    # wall type change
    single_cat_change(Brisbane,'orig_WALL_TYPE','new_WALL_TYPE')
    single_cat_change(Gold_Coast,'orig_WALL_TYPE','new_WALL_TYPE')
    single_cat_change(Moreton_Bay,'orig_WALL_TYPE','new_WALL_TYPE')
    single_cat_change(Noosa,'orig_WALL_TYPE','new_WALL_TYPE')
    single_cat_change(Redland,'orig_WALL_TYPE','new_WALL_TYPE')
    single_cat_change(Sunshine_Coast,'orig_WALL_TYPE','new_WALL_TYPE')

    # year built change
    single_cat_change(Brisbane,'orig_YEAR_BUILT','new_YEAR_BUILT')
    single_cat_change(Gold_Coast,'orig_YEAR_BUILT','new_YEAR_BUILT')
    single_cat_change(Moreton_Bay,'orig_YEAR_BUILT','new_YEAR_BUILT')
    single_cat_change(Noosa,'orig_YEAR_BUILT','new_YEAR_BUILT')
    single_cat_change(Redland,'orig_YEAR_BUILT','new_YEAR_BUILT')
    single_cat_change(Sunshine_Coast,'orig_YEAR_BUILT','new_YEAR_BUILT')

    # use cat change
    single_cat_change(Brisbane,'orig_MB_CAT','new_MB_CAT')
    single_cat_change(Gold_Coast,'orig_MB_CAT','new_MB_CAT')
    single_cat_change(Moreton_Bay,'orig_MB_CAT','new_MB_CAT')
    single_cat_change(Noosa,'orig_MB_CAT','new_MB_CAT')
    single_cat_change(Redland,'orig_MB_CAT','new_MB_CAT')
    single_cat_change(Sunshine_Coast,'orig_MB_CAT','new_MB_CAT')