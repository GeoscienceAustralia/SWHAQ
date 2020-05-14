#!/bin/bash
#PBS -Pw85
#PBS -qexpress
#PBS -N swhaqmultipliers
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=01:00:00
#PBS -lmem=32GB,ncpus=1,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85
#PBS -v EVENTID


#  * To use: 
#  - make appropriate changes to the PBS options above
#  - submit the job with the appropriate value of EVENTID, eg:
#     `qsub -v EVENTID=001-00406 swhaq_apply_multipliers.sh`

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
DATE=`date +%Y%m%d%H%M`
SIMULATION=001-00406
OUTPUT=/g/data/w85/QFES_SWHA/wind/local/$EVENTID
CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/pm/QLD_$EVENTID\_pm.ini

# Add path to where TCRM is installed.
SOFTWARE=/g/data/w85/software
BRANCH=master

# Add to the Python path. We need to ensure we set the paths in the correct order
# to access the locally installed version of the GDAL bindings
export PYTHONPATH=$PYTHONPATH:$SOFTWARE/tcrm/$BRANCH:$SOFTWARE/tcrm/$BRANCH/Utilities

echo $PYTHONPATH
echo $CONFIGFILE
echo $OUTPUT
echo $GEOS_ROOT

if [ ! -d "$OUTPUT" ]; then
   mkdir $OUTPUT
fi

if [ ! -f "$CONFIGFILE" ]; then
    echo "Configuration file does not exist:"
    echo $CONFIGFILE
    exit 1
fi

# Run the complete simulation:
python3 $SOFTWARE/tcrm/$BRANCH/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1

cd $OUTPUT
cp $CONFIGFILE ./$EVENTID.$DATE.ini
