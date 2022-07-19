#!/bin/bash
#PBS -Pw85
#PBS -qexpress
#PBS -N hazimp
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=02:00:00
#PBS -lmem=16GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85
#PBS -v EVENTID

# This job script is used to run the `hazimp.py`
# script on gadi. It has been tailored for use in the Severe
# Wind Hazard Assessment project for Queensland, which means
# some of the paths and file names are specific to that project
#
#  * To use: 
#  - Ensure there is a correctly specified HazImp configuration
#    file at /g/data/w85/QFES_SWHA/configuration/hazimp/
#  - make appropriate changes to the PBS options above, specifically
#    consider: 
#
#    #PBS -M <email address>
#    #PBS -lwalltime
#
#  - submit the job with the appropriate value of EVENTID, eg:
#     `qsub -v EVENTID=001-00406 run_hazimp.sh`
# 
# Contact:
# Craig Arthur, craig.arthur@ga.gov.au
# 2020-05-23

umask 002

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2 
module load openmpi/4.0.1

# Need to ensure we get the correct paths to access the local version of gdal bindings. 
# The module versions are compiled against Python3.6, so we can't use them
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

# Needs to be resolved, but this suppresses an error related to HDF5 libs
export HDF5_DISABLE_VERSION_CHECK=2

SOFTWARE=/g/data/w85/software

# Add HazImp code to the path:
export PYTHONPATH=$SOFTWARE/hazimp:$PYTHONPATH

cd $SOFTWARE/hazimp/

DATE=`date +%Y%m%d%H%M`

if [ $# -eq 0 ]; then
    # Use an environment variable
    EVENTID=$EVENTID
else
    EVENTID=$1
    echo "Running hazimp for scenario $EVENTID"
fi

CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/hazimp/$EVENTID.yaml
OUTPUT=/g/data/w85/QFES_SWHA/impact/2021UV/$EVENTID


if [ ! -f "$CONFIGFILE" ]; then
    echo "Configuration file does not exist: $CONFIGFILE"
    exit 1
else
    echo $CONFIGFILE
fi

# Ensure output directory exists. If not, create it:
if [ ! -d "$OUTPUT" ]; then
   mkdir $OUTPUT
fi


# Run the complete simulation:
python3 $SOFTWARE/hazimp/hazimp/main.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1

cp $CONFIGFILE $OUTPUT/$EVENTID.$DATE.yaml

