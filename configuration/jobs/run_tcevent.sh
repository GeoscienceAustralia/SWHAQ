#!/bin/bash
#PBS -Pw85
#PBS -qexpress
#PBS -N tcevent
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=02:00:00
#PBS -lmem=16GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=gdata/w85
#PBS -v EVENTID

# This job script is used to run the `tcevent.py`
# script on gadi. It has been tailored for use in the Severe
# Wind Hazard Assessment project for Queensland, which means
# some of the paths and file names are specific to that project
#
#  * To use: 
#  - Ensure there is a correctly specified configuration file
#    for `tcevent.py`. 
#  - make appropriate changes to the PBS options above
#  - submit the job with the appropriate value of EVENTID, eg:
#     `qsub -v EVENTID=001-00406 run_tcevent.sh`
# 
# Contact:
# Craig Arthur, craig.arthur@ga.gov.au
# 2020-05-23

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2
module list

# Need to ensure we get the correct paths to access the local version of gdal bindings. 
# The module versions are compiled against Python3.6
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

DATE=`date +%Y%m%d%H%M`
OUTPUT=/g/data/w85/QFES_SWHA/wind/regional/$EVENTID
CONFIGFILE=/g/data/w85/QFES_SWHA/configuration/tcrm/$EVENTID.ini
TRACKPATH=/g/data/w85/QFES_SWHA/tracks

# Substitute the paths into the template configuration file: 
sed 's|TRACKPATH|'$TRACKPATH'|' /g/data/w85/QFES_SWHA/configuration/tcrm/tcevent_template.ini > $CONFIGFILE
sed 's|OUTPUTPATH|'$OUTPUT'|' /g/data/w85/QFES_SWHA/configuration/tcrm/tcevent_template.ini > $CONFIGFILE
sed 's|EVENTID|'$EVENTID'|' /g/data/w85/QFES_SWHA/configuration/tcrm/tcevent_template.ini > $CONFIGFILE

# Add path to where TCRM is installed. Separate installations
# for py3, master, develop branch
SOFTWARE=/g/data/w85/software
BRANCH=master

# Add to the Python path. e need to ensure we set the paths in the correct order
# to access the locally installed version of the GDAL bindings
export PYTHONPATH=$PYTHONPATH:$SOFTWARE/tcrm/$BRANCH:$SOFTWARE/tcrm/$BRANCH/Utilities

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

if [ ! -f "$CONFIGFILE" ]; then
    echo "Configuration file does not exist:"
    echo $CONFIGFILE
    exit 1
fi

# Run the complete simulation:
python3 $SOFTWARE/tcrm/$BRANCH/tcevent.py -c $CONFIGFILE > $OUTPUT/$EVENTID.stdout.$DATE 2>&1

python3 /g/data/w85/software/track2shp.py -id $EVENTID
#BRANCH=develop
#python3 $SOFTWARE/tcrm/$BRANCH/Utilities/tracks2shp.py -f /g/data/w85/QFES_SWHA/tracks/track.$SIMULATION.nc

cd $OUTPUT
cp $CONFIGFILE ./$EVENTID.$DATE.ini

