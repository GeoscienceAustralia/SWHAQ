#!/bin/bash
# A simple script to submit job scripts for all events listed 
# in the scenario lookup table. This will run the shell script  
# run_hazimp.sh, setting the required 
#
# Contact: Craig Arthur <craig.arthur@ga.gov.au>
# 2020-05-24

BASEPATH=/g/data/w85/QFES_SWHA/configuration

sed 1d $BASEPATH/scenario_lookup_table.csv | while IFS=, read -r ID category location
do 
    echo "Running HazImp for scenario $ID, a category $category event at $location"
    
    $BASEPATH/jobs/run_hazimp.sh $ID
    sleep 5

done
