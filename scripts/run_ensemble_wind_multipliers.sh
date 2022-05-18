#!/bin/bash
#PBS -P w85
#PBS -N mult_16_threads
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=48:00:00
#PBS -lmem=64GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85+gdata/v10

# This job script is used to run the `processMultipliers.py`
# script on gadi. It has been tailored for use in the Severe
# Wind Hazard Assessment project for Queensland, which means
# some of the paths and file names are specific to that project
#
#  * To use: 
#  - Ensure there is a correctly specified configuration file
#    for `processMultipliers.py`. This will include setting the list
#    of tiles to be sampled.
#  - make appropriate changes to the PBS options above
#  - submit the job with the appropriate value of EVENTID, eg:
#     `qsub -v EVENTID=001-00406 run_processMultipliers.sh`


module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2

# Need to ensure we get the correct paths to access the local version of gdal bindings. 
# The module versions are compiled against Python3.6
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

# Needs to be resolved, but this suppresses an error related to HDF5 libs
export HDF5_DISABLE_VERSION_CHECK=2

module list
# Add path to where TCRM is installed.
SOFTWARE=/g/data/w85/software
BRANCH=master

export PYTHONPATH=$PYTHONPATH:$SOFTWARE/tcrm/$BRANCH:$SOFTWARE/tcrm/$BRANCH/Utilities

echo $PYTHONPATH
echo $CONFIGFILE
echo $OUTPUT
echo $GEOS_ROOT

# Record the version of code used
REV=`git -C $SOFTWARE/tcrm/$BRANCH/ log -1 --pretty=format:'%h %ci'`
echo "Using TCRM revision: $REV"

DATE=`date +%Y%m%d%H%M`
EXTENTAPPLIED='no'
for i in {000..100}
do
    EVENTID="$i-00$i"

    OUTPUT=/scratch/w85/yasi/output/multipliers/$EVENTID
    CONFIGFILE=/scratch/w85/kr4383/yasi/$EVENTID\_pm.ini

    if [ ! -d "$OUTPUT" ]; then
        mkdir $OUTPUT
    fi

    # Substitute the paths into the template configuration file:
    sed 's|EVENTID|'$EVENTID'|g' /scratch/w85/kr4383/yasi/pm_template.ini > $CONFIGFILE
    sed -i 's|OUTPUTPATH|'$OUTPUT'|g' $CONFIGFILE
    sed -i 's|EXTENTAPPLIED|'$EXTENTAPPLIED'|g' $CONFIGFILE

    if [ $EXTENTAPPLIED == 'yes' ]
    then
        sed -i '/Multipliers=/c\Multipliers=/scratch/w85/yasi/output/multipliers/000-00000/m4_source.tif' $CONFIGFILE
    fi

    EXTENTAPPLIED='yes'

    # Run the complete simulation:
    python3 $SOFTWARE/tcrm/$BRANCH/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1
    python3 ~/tcrm/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1
done

# EVENTID="000-00000"
# OUTPUT=/scratch/w85/yasi/output/multipliers/$EVENTID
# CONFIGFILE=/scratch/w85/kr4383/yasi/$EVENTID\_pm.ini
# nohup python3 ~/tcrm/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1

# EVENTID="001-00001"
# OUTPUT=/scratch/w85/yasi/output/multipliers/$EVENTID
# CONFIGFILE=/scratch/w85/kr4383/yasi/$EVENTID\_pm.ini
# nohup python3 ~/tcrm/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1
# echo "wo"
