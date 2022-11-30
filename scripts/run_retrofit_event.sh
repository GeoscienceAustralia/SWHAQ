#!/bin/bash
#PBS -Pw85
#PBS -qhugemem
#PBS -N hazimpretro
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=2:00:00
#PBS -lmem=128GB,ncpus=32,jobfs=4000MB
#PBS -joe
#PBS -W umask=0002
#PBS -lstorage=gdata/w85
#PBS -v EVENTID

# Run an iterative version of hazimp, where we randomly select a subset of
# building for a virtual retrofit.
#
# This script takes an event id number as either a command line argument or
# a n environment variable, which determines the required hazard file to read
# in. It is passed directly to the python script


# Fix permissions for all files/folders created so the group can access them
umask 002
DATE=`date +%Y%m%d%H%M`

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2

# Need to ensure we get the correct paths to access the local version of gdal bindings.
# The module versions are compiled against Python3.6, so we can't use them
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

export HDF5_DISABLE_VERSION_CHECK=2

# Suppress GDAL warnings
export CPL_LOG=/dev/null

if [ $# -eq 0 ]; then
    # Use an environment variable
    EVENTID=$EVENTID
else
    EVENTID=$1
    echo "Running hazimp for scenario $EVENTID"
fi

SOFTWARE=/g/data/w85/software
BASEOUTPUT=/g/data/w85/QFES_SWHA/impact/RETROFIT
# Add HazImp code to the path:
export PYTHONPATH=$SOFTWARE/hazimp:$PYTHONPATH

OUTPUT=$PBS_JOBFS/output
if [ ! -d "$OUTPUT" ]; then
    mkdir $OUTPUT
fi

cd /g/data/w85/QFES_SWHA/scripts
echo "Processing impact for scenario $EVENTID"

if [ ! -d "$BASEOUTPUT/$EVENTID" ]; then
    mkdir -m 775 $BASEOUTPUT/$EVENTID
fi

python3 iterate_vulnerability_scenario.py $EVENTID > $BASEOUTPUT/$EVENTID/hazimp_retrofit_event.stdout.$DATE 2>&1
python3 retrofit_impact_analysis.py $EVENTID >> $BASEOUTPUT/$EVENTID/hazimp_retrofit_event.stdout.$DATE 2>&1