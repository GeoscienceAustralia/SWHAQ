#!/bin/bash
#PBS -Pw85
#PBS -qexpress
#PBS -N tc-007-09962
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=05:00:00
#PBS -lmem=16GB,ncpus=1,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85

module purge
module load pbs
module load dot

module load openmpi/4.0.1
module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2


module list
DATE=`date +%Y%m%d%H%M`
SIMULATION=007-09962-2d
OUTPUT=/g/data/w85/QFES_SWHA/wind/regional/$SIMULATION
CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/tcrm/$SIMULATION.ini

# Add path to where TCRM is installed. Separate installations
# for py3 branch
SOFTWARE=/g/data/w85/software

# Add to the Python path. e need to ensure we set the paths in the correct order
# to access the locally installed version of the GDAL bindings
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$SOFTWARE/tcrm/master:$SOFTWARE/tcrm/master/Utilities:$PYTHONPATH

# Suppresses an error related to HDF5 libraries:
export HDF5_DISABLE_VERSION_CHECK=2


echo $PYTHONPATH
echo $CONFIGFILE
echo $OUTPUT
echo $GEOS_ROOT

# Ensure output directory exists. If not, create it:

if [ ! -d "$OUTPUT" ]; then
   mkdir $OUTPUT
fi

# Run the complete simulation:
python3 $SOFTWARE/tcrm/master/tcevent.py -c $CONFIGFILE > $OUTPUT/$SIMULATION.stdout.$DATE 2>&1

cd $OUTPUT
cp $CONFIGFILE ./$SIMULATION.$DATE.ini

