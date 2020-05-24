#!/bin/bash
# A simple script to submit job scripts for all events listed 
# in the scenario lookup table. This will submit a job to run 
# tcevent.py, based on teh job submission script "run_tcevent.sh"
#
# Contact: Craig Arthur <craig.arthur@ga.gov.au>
# 2020-05-24

BASEPATH=/g/data/w85/QFES_SWHA/configuration

sed 1d $BASEPATH/scenario_lookup_table.csv | while IFS=, read -r ID category location
do 
    echo "Submitting job for scenario $ID, a category $category event at $location"
    
    qsub -v EVENTID=$ID $BASEPATH/jobs/run_tcevent.sh
    sleep 5

done
