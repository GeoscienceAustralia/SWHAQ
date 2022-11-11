#!/bin/bash

# Run an iterative version of hazimp, where we randomly select a subset of
# building for a virtual retrofit. 
#
# This script takes an ARI as a command line argument, which determines the
# required hazard file to read in. It is passed directly to the python script 

pid=$(grep ^Pid /proc/self/status)
corelist=$(grep Cpus_allowed_list: /proc/self/status | awk '{print $2}')
host=$(hostname | sed 's/.gadi.nci.org.au//g')
echo subtask $1 running in $pid using core $corelist on compute node $host

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

ARI=$1

SOFTWARE=/g/data/w85/software
BASEOUTPUT=/g/data/w85/QFES_SWHA/risk_pp/retro_prob_v2
# Add HazImp code to the path:
export PYTHONPATH=$SOFTWARE/hazimp:$PYTHONPATH

OUTPUT=$PBS_JOBFS/output
if [ ! -d "$OUTPUT" ]; then
    mkdir $OUTPUT
fi

cd /g/data/w85/QFES_SWHA/scripts
echo "Processing impact for $ARI-year ARI wind speed"

if [ ! -d "$BASEOUTPUT/$ARI" ]; then
    mkdir -m 775 $BASEOUTPUT/$ARI
fi

python3 iterate_vulnerability.py $ARI > $BASEOUTPUT/$ARI/hazimp_retrofit.stdout.$DATE 2>&1
