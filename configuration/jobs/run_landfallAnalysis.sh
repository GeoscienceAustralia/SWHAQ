#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N landfall
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=2:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85+scratch/w85
#PBS -v DATAPATH
#PBS -o /g/data/w85/QFES_SWHA/logs/tcrm/hazard
#PBS -e /g/data/w85/QFES_SWHA/logs/tcrm/hazard

# This job script is used to run `tcrm.py`on gadi. It has been  
# tailored for use in the Severe Wind Hazard Assessment project
# for Queensland, which means some of the paths and file names 
# are specific to that project
#
#  * To use: 
#  - Ensure there is a correctly specified configuration file
#    for `tcrm.py`. 
#  - make appropriate changes to the PBS options above
#  - submit the job with the appropriate value of CONFIGFILE, eg:
#     `qsub -v DATAPATH=/g/data/w85/QFES_SWHA/hazard/output/GROUP1_RCP45_1981-2010 run_landfallAnalysis.sh`
# 
# Contact:
# Craig Arthur, craig.arthur@ga.gov.au
# 2020-07-17

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2
module load openmpi

# Need to ensure we get the correct paths to access the local version of gdal bindings. 
# The module versions are compiled against Python3.6
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

# Needs to be resolved, but this suppresses an error related to HDF5 libs
export HDF5_DISABLE_VERSION_CHECK=2


module list
DATE=`date +%Y%m%d%H%M`

OUTPUTBASE=/g/data/w85/QFES_SWHA/hazard/tcrm

# Add path to where TCRM is installed. 
SOFTWARE=/g/data/w85/software

# Add to the Python path. e need to ensure we set the paths in the correct order
# to access the locally installed version of the GDAL bindings
export PYTHONPATH=$PYTHONPATH:$HOME/tcrm:$HOME/tcrm/Utilities

# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2


# Ensure datapath directory exists. If not, abort:

if [ $# -eq 0 ]; then
    # Use an environment variable
    DATAPATH=$DATAPATH
    echo "Running landfall analysis using $DATAPATH from environment variables"
else
    DATAPATH=$1
    echo "Running landfall analysis using $DATAPATH"
fi

if [ ! -d $DATAPATH ]; then
    echo "$DATAPATH is missing - aborting"
    exit 1
fi    



python3 $HOME/tcrm/Evaluate/landfallIntensity.py -p $DATAPATH > $DATAPATH/log/landfall.stdout 2>&1


if [[ $? -ne 0 ]]; then
    echo "Landfall analysis simulation using $DATAPATH has failed unexpectedly"
    echo "Check the log file (path specified in the config file)"
    exit 1
fi
#cd $OUTPUTBASE
#cp $CONFIGFILE ./$SIMULATION.$DATE.ini

