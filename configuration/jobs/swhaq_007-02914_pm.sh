#!/bin/bash
#PBS -Pw85
#PBS -qnormalbw
#PBS -N tc-007-02914
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=01:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85

#module purge
#module load pbs
#module load dot
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

SOFTWARE=/g/data/w85/software

module list
DATE=`date +%Y%m%d%H%M`
SIMULATION=007-02914
OUTPUT=/g/data/w85/QFES_SWHA/wind/local/$SIMULATION
CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/pm/QLD_$SIMULATION\_pm.ini
PYTHONPATH=$PYTHONPATH:$SOFTWARE/tcrm/master:$SOFTWARE/tcrm/master/Utilities
echo $PYTHONPATH
echo $CONFIGFILE
echo $OUTPUT
echo $GEOS_ROOT
# Run the complete simulation:
python3 $SOFTWARE/tcrm/master/ProcessMultipliers/processMultipliers.py -c $CONFIGFILE > $OUTPUT/$SIMULATION.stdout.$DATE 2>&1

cd $OUTPUT
cp $CONFIGFILE ./$SIMULATION.$DATE.ini

