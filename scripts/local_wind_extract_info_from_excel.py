######################################################################
# Name: local_wind_extract_info_from_excel.py.py
# Author:  R. Coghlan
# Date: 2018-01-23
# Desc: Processes a folder of NEXIS exposure report outputs by extracting
# required data from spreadsheets for each event-category and summarising 
# them in a new table ready to include in map products
#
# 2019-03-19: Updated by C. Arthur to read in new format exposure reports
#             generated via AEIP. 
# 2019-11-12: Updated to Python 3 (C. Arthur)
#
# NOTES:
# This assumes the filenames are like AEIP_Data_<Locality> Cat<#> <eventId> Cat[1-5].xlsx
# where <Locality> is the name of the location, <#> represents the nominal category of the TC event 
# (i.e. the intended maximum category), <eventId> is the scenario number (from TCHA) and Cat[1-5] is used
# to identify which wind zone is being processed. For example:
#    AIEP_Data_Cairns Cat5 013-03564 Cat3.xlsx represents the area exposed to category 3 wind speeds, for 
#    a TC in Cairns with a maximum intenisty of category 5, and event Id number 013-03564.
#
######################################################################

import os
import logging
import xlrd 
import numpy as np
import pandas as pd
import re
from builtins import str
import pdb

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)


# function to transpose table
def transpose(inputList):
    tmptest = []
    for i in range(len(max(inputList, key=len))):
        tmptest.append([(c[i] if i<len(c) else '') for c in inputList])
    return tmptest
    
########################################################################
# input directory where exposure .xls files for each category exist
dir = "data/exposure"
########################################################################

dirlist =  [x[0] for x in os.walk(dir)]
dirlist.pop(0)
for dir in dirlist:
    logging.info(('Processing {}'.format(dir)))

    fileList = []
    uniqueNameList = []
    nameCheck = re.compile('AEIP_Data_.*Cat[0-9].*\.xlsx')
    logging.debug((os.listdir(dir)))
    # create a list of all excel files that match the regex above
    for file in [f for f in os.listdir(dir) if nameCheck.search(f)]:
        fileList.append(os.path.join(dir, file))
        
    logging.debug(fileList)
    # for each file, remove the category off the filename and store if list if not there already    
    for file in fileList:
        eventName = os.path.basename(file).split(".")[0].rsplit('_', 1)[0]
        eventName = os.path.basename(file).split(".")[0].rsplit('_', 1)[1].rsplit(' ', 1)[0]
        logging.info(eventName)
        if eventName not in uniqueNameList:
            uniqueNameList.append(eventName)
    
    # loop through each item in uniqueNameList
    for uniqueEvent in uniqueNameList:
        logging.info(('Processing {}'.format(uniqueEvent)))
        # create an empty dataframe results from each category will be appended to
        masterdf = pd.DataFrame(columns=['Description','Cat1','Cat2','Cat3','Cat4','Cat5','Order'])
        # loop through each file    
        for file in fileList:
            # if file matchs uniqueEvent, continue processing
            if uniqueEvent in file:
                logging.info(('Extracting info from {}'.format(os.path.basename(file))))
                # extract the cat number and store in a variable
                cat = os.path.basename(file).split(".")[0].split(" ")[-1]
    
                # open the workbook
                workbook = xlrd.open_workbook(file, encoding_override='utf-8') 
                all_worksheets = workbook.sheet_names() 
                for worksheet_name in all_worksheets:
                    logging.info(worksheet_name)
                    # if the worksheet is Building Exposure extract the info and the transpose the table
                    if worksheet_name == 'Building Exposure':
                        BldExposure = []
                        worksheet = workbook.sheet_by_name(worksheet_name) 
                        worksheetAsAList = []
                        for rownum in range(worksheet.nrows): 
                            worksheetAsAList.append([str(entry).encode("utf-8") for entry in worksheet.row_values(rownum)]) 
                   
                        #transposedWorksheet = transpose(worksheetAsAList)
                        
                        # extract the following fields and append to list
                        fieldsToExtract = ['Population count',
                                           'Building count',
                                           'Commercial Building Count',
                                           'Industrial Building Count']
                        #for row in transposedWorksheet:
                        for row in worksheetAsAList:
                            if row[1].decode('utf-8') in fieldsToExtract:
                                BldExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8'))])
                        # create a dataframe of the extracted info        
                        BldExposuredf = pd.DataFrame(BldExposure, columns=['CAT', 'COUNT'])

                    # if worksheet is Infrastructure Exposure extract the relevent fields to a list
                    if worksheet_name == 'Institution Exposure':
                        InstitutionExposure = []
                        worksheet = workbook.sheet_by_name(worksheet_name)
                        worksheetAsAList = []
                        for rownum in range(worksheet.nrows):
                            worksheetAsAList.append([str(entry).encode("utf-8") for entry in worksheet.row_values(rownum)])
                        EdfieldsToExtract = ['School - Pre/Primary',
                                           'School - Secondary',
                                           'School - Tertiary',
                                           'School - Other']
                        HealthfieldsToExtract = ['Hospital - Public',
                                           'Hospital - Private',
                                           'Nursing Home',
                                           'Retirement Home']        
                        EmergencyfieldsToExtract = ['Police Station',
                                           'Fire Station',
                                           'Ambulance Station',
                                           'SES Facility',
                                           'Rural/Country Fire Facility',]
                        for row in worksheetAsAList:
                            if row[1].decode('utf-8') in EdfieldsToExtract:
                                InstitutionExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Education'])
                            if row[1].decode('utf-8') in HealthfieldsToExtract:
                                InstitutionExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Health'])
                            if row[1].decode('utf-8') in EmergencyfieldsToExtract:
                                InstitutionExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Emergency'])

                    if worksheet_name == 'Infrastructure Exposure':
                        InfrastructureExposure = []
                        worksheet = workbook.sheet_by_name(worksheet_name) 
                        worksheetAsAList = []
                        for rownum in range(worksheet.nrows): 
                            worksheetAsAList.append([str(entry).encode("utf-8") for entry in worksheet.row_values(rownum)])
                        EdfieldsToExtract = ['School - Pre/Primary',
                                           'School - Secondary',
                                           'School - Tertiary',
                                           'School - Other (Combined, Special)']
                        HealthfieldsToExtract = ['Hospital - Public',
                                           'Hospital - Private',
                                           'Nursing Home',
                                           'Retirement Home']        
                        EmergencyfieldsToExtract = ['Police Station',
                                           'Fire Station',
                                           'Ambulance Station',
                                           'SES Facility',
                                           'Emergency Management Facility',]
                        RoadfieldsToExtract = ['Road - Major (km)',
                                            'Road - Arterial and Sub-arterial (km)']
                        RailfieldsToExtract = ['Railway - Tracks (km)']
                        EleclfieldsToExtract = ['Transmission - Electricity Lines (km)']
                        
                        # append extracted info to list and add catagory field
                        for row in worksheetAsAList:
                            if row[1].decode('utf-8') in EdfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Education'])
                            if row[1].decode('utf-8') in HealthfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Health'])
                            if row[1].decode('utf-8') in EmergencyfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Emergency'])    
                            if row[1].decode('utf-8') in RoadfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Roads'])
                            if row[1].decode('utf-8') in RailfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Rail'])
                            if row[1].decode('utf-8') in EleclfieldsToExtract:
                                InfrastructureExposure.append([row[1].decode('utf-8'), float(row[2].decode('utf-8')), 'Elec'])
                    
                
                institutiondf = pd.DataFrame(InstitutionExposure, columns=['FEATURE_TYPE', 'COUNT', 'CAT'])
                institutiondf = institutiondf.replace('-', np.nan)
                institutiondf['COUNT'] = institutiondf.COUNT.astype(float)
                # create dataframe from list
                infrastructuredf = pd.DataFrame(InfrastructureExposure, columns=['FEATURE_TYPE', 'COUNT', 'CAT'])
                # replace any dashs with NaN            
                infrastructuredf = infrastructuredf.replace('-', np.nan)
                # make sure count field is float no object
                infrastructuredf['COUNT'] = infrastructuredf.COUNT.astype(float)
                 
                # replace any dashs with NaN            
                BldExposuredf = BldExposuredf.replace('-', np.nan)
                # make sure count field is float no object
                BldExposuredf['COUNT'] = BldExposuredf.COUNT.astype(float)  
                
                # merge dataframes to form new one
                df_new = pd.concat([BldExposuredf, institutiondf, infrastructuredf], sort=False)
                
                # group by the CAT field and sum the counts
                finalDf = df_new.groupby('CAT')[['COUNT']].sum()

                # convert the index field to a new field called Description
                finalDf['Description'] = finalDf.index
                # reset the infex
                finalDf.reset_index(drop=True, inplace=True)
                # setup columns for new dataframe
                cols = ['Description', 'COUNT']
                # create new dataqframe using columns above
                finalDf = finalDf[cols] 
                # add in empty field to store row order
                finalDf["Order"] = ""
                
                # calculate row order based on description text
                for i, row in finalDf.iterrows():
                    if row['Description'] == 'Population count':
                        finalDf.at[i,'Order'] = 1
                    if row['Description'] == 'Building count':
                        finalDf.at[i,'Order'] = 2
                    if row['Description'] == 'Commercial Building Count':
                        finalDf.at[i,'Order'] = 3        
                    if row['Description'] == 'Industrial Building Count':
                        finalDf.at[i,'Order'] = 4        
                    if row['Description'] == 'Emergency':
                        finalDf.at[i,'Order'] = 5        
                    if row['Description'] == 'Health':
                        finalDf.at[i,'Order'] = 6        
                    if row['Description'] == 'Education':
                        finalDf.at[i,'Order'] = 7        
                    if row['Description'] == 'Roads':
                        finalDf.at[i,'Order'] = 8        
                    if row['Description'] == 'Rail':
                        finalDf.at[i,'Order'] = 9        
                    if row['Description'] == 'Elec':
                        finalDf.at[i,'Order'] = 10        
                
                # rename the count field to the cat number extract from the spreadsheet filename            
                finalDf = finalDf.rename(columns={'COUNT': '{0}'.format(cat)})
                # append results to the master dataframe created at the beginning
                masterdf = masterdf.append(finalDf)
    
                
        logging.info('\tMerging extracted data')

        # ensure all count and order fields are flaot not object
        for col in ['Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5', 'Order']:
            masterdf[col] = masterdf[col].astype('float')
        
        # convert any NaN values to 0    
        masterdf.fillna(0, inplace=True)
        # groupby the Description field to shrink the table down to single rows
        masterdf = masterdf.groupby(['Description']).max()
      
        # convert the index field to a new field called Description
        masterdf['Description'] = masterdf.index
        # reset the infex
        masterdf.reset_index(drop=True, inplace=True)
        # change the order of the columns back to what we want
        cols = ['Description','Cat1','Cat2','Cat3','Cat4','Cat5','Order']
        masterdf = masterdf[cols] 
    
        
    
        # replace the description text with what is required for the output table
        masterdf['Description'].replace('Population count', 'Number of people', inplace=True)
        masterdf['Description'].replace('Building count', 'Number of residential buildings', inplace=True)
        masterdf['Description'].replace('Commercial Building Count', 'Number of commercial buildings', inplace=True)
        masterdf['Description'].replace('Industrial Building Count', 'Number of industrial buildings', inplace=True)
        masterdf['Description'].replace('Emergency', 'Number of Emergency facilities', inplace=True)
        masterdf['Description'].replace('Health', 'Number of health facilities', inplace=True)
        masterdf['Description'].replace('Education', 'Number of school facilities', inplace=True)
        masterdf['Description'].replace('Roads', 'Length of major roads (km)', inplace=True)
        masterdf['Description'].replace('Rail', 'Length of railway lines (km)', inplace=True)
        masterdf['Description'].replace('Elec', 'Length of electricity transmission Lines (km)', inplace=True)
        
        # sort the table based on the order field
        masterdf.sort_values(by=['Order'], inplace=True)
        # drop the order field from the table
        masterdf = masterdf.drop(['Order'], axis=1)
        
        
        #setup output filename and write output file
        outputFile = '{}_local_wind_summary.xlsx'.format(uniqueEvent)
        writer = pd.ExcelWriter(os.path.join(dir, outputFile))
        masterdf.to_excel(writer,'Exposure_Summary', index=False)
        writer.save()
        logging.info(('Output written: {}'.format(os.path.join(dir, outputFile))))
    

logging.info('Complete')
