#!/bin/bash
# A simple script to submit job scripts for all events listed 
# in the scenario lookup table. This will run the shell script  
# run_hazimp.sh, setting the required 
#
# Contact: Craig Arthur <craig.arthur@ga.gov.au>
# 2020-05-24

BASEPATH=/g/data/w85/QFES_SWHA/configuration
BASEOUTPUT=/g/data/w85/QFES_SWHA/impact
SOFTWARE=/g/data/w85/software
LOGDIR=/g/data/w85/QFES_SWHA/logs/impact
source ~/pythonenv.sh
export PYTHONPATH=$PYTHONPATH:$SOFTWARE/hazimp


sed 1d $BASEPATH/scenario_lookup_table.csv | while IFS=, read -r ID category location
do 
    echo "Running HazImp post analysis for scenario $ID, a category $category event at $location"

    INPUTFILE=$BASEOUTPUT/NEXISV10/$ID/QFES\_$ID.csv
    echo "Processing $INPUTFILE"
    python3 $SOFTWARE/hazimp/post/impact_analysis.py -i $INPUTFILE -f 'png'

done
