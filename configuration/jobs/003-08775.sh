#!/bin/bash
#PBS -Pw85
#PBS -qexpress
#PBS -N tc-003-08775
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=06:00:00
#PBS -lmem=8GB,ncpus=1,jobfs=4000MB
#PBS -joe
module purge
module load pbs
module load dot
module load openmpi/1.8.4
module load python/2.7.11
module load python/2.7.11-matplotlib
module load pypar/26Feb15-2.7.6-1.8.4
module load geos
module load gdal/1.11.1-python

module list
DATE=`date +%Y%m%d%H%M`
SIMULATION=003-08775
OUTPUT=/g/data/w85/QFES_SWHA/wind/regional/$SIMULATION
CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/tcrm/$SIMULATION.ini
PYTHONPATH=$PYTHONPATH:$HOME/tcrm:$HOME/tcrm/Utilities
echo $PYTHONPATH
echo $CONFIGFILE
echo $OUTPUT
echo $GEOS_ROOT

# Ensure output directory exists. If not, create it:

if [ ! -d "$OUTPUT" ]; then
   mkdir $OUTPUT
fi


# Run the complete simulation:
python $HOME/tcrm/tcevent.py -c $CONFIGFILE > $OUTPUT/$SIMULATION.stdout.$DATE 2>&1

cd $OUTPUT
cp $CONFIGFILE ./$SIMULATION.$DATE.ini
