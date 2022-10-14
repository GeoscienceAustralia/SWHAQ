#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N hazimp
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=24:00:00
#PBS -lmem=16GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -W umask=0002
#PBS -lstorage=gdata/w85

# This job script is used to run the `hazimp.py`
# script on gadi. It has been tailored for use in the Severe
# Wind Hazard Assessment project for Queensland, which means
# some of the paths and file names are specific to that project
#
#  * To use:
#  - Ensure there is a correctly specified HazImp configuration
#    file at /g/data/w85/QFES_SWHA/configuration/hazimp/aepimpact.yaml.template
#  - make appropriate changes to the PBS options above, specifically
#    consider:
#
#    #PBS -M <email address>
#    #PBS -lwalltime
#
#  - submit the job:
#     `qsub run_hazimp_risk.sh`
#
# Contact:
# Craig Arthur, craig.arthur@ga.gov.au
# 2022-07-11

# Fix permissions for all files/folders created so the group can access them
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

TEMPLATECONFIG=/g/data/w85/QFES_SWHA/configuration/hazimp/aepimpact.yaml.template
BASEOUTPUT=/g/data/w85/QFES_SWHA/risk_pp/risk_pp_retro5_eligible


if [ ! -f "$TEMPLATECONFIG" ]; then
    echo "Configuration file does not exist: $TEMPLATECONFIG"
    exit 1
else
    echo $TEMPLATECONFIG
fi

# Ensure base output directory exists. If not, create it:
if [ ! -d "$BASEOUTPUT" ]; then
   mkdir $BASEOUTPUT
fi

FS=$IFS
IFS=","
YEARS="1,2,3,4,5,10,15,20,20,30,35,40,45,50,75,100,150,200,250,300,350,400,450,500,1000,2000,2500,5000,10000"
for YEAR in $YEARS; do
    echo "Processing impact for $YEAR-year ARI wind speed"
    OUTPUT=$BASEOUTPUT/$YEAR
    if [ ! -d "$OUTPUT" ]; then
        mkdir $OUTPUT
    fi
    CONFIGFILE="/g/data/w85/QFES_SWHA/configuration/hazimp/aepimpact.yaml"
    # Use sed to modify the template config file, replacing all occurrences of
    # "ARI" with the value of $YEAR (sed is by default case sensitive)
    sed 's|ARI|'$YEAR'|g' $TEMPLATECONFIG > $CONFIGFILE
    # Run HazImp using the modified configuration file:
    python3 $SOFTWARE/hazimp/hazimp/main.py -c $CONFIGFILE > $OUTPUT/hazimp.stout.$DATE 2>&1
    cp $CONFIGFILE $OUTPUT/aepimpact.$YEAR.yaml
done
IFS=$FS

