#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N dailyltmpi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=06:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4GB
#PBS -W umask=0002
#PBS -joe
#PBS -lstorage=gdata/w85

# Create daily long term mean (DLTM) climatologies of input 6-hourly
# RCM output files. This is used to create DLTM MSLP (or PI) files 
# for use in TCRM. The script will create DLTM values for all variables
# provided in the input files.
#
# RCM data was provided by Dep't of Environment and Science (QLD)
# as part of the SHWA-Q project (2018-2021)

module purge
module load pbs
module load dot

module load cdo

INPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/pi/Daily/
OUTPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/pi/dltm/

process()
{
    # Run a bunch of cdo commands:
    # Args:
    # $1 = start year
    # $2 = end year
    # $3 = input file name
    # $4 = substring for the selected model
    
    echo "Processing $3"
    cdo -ydaymean -selyear,$1/$2 $3 $OUTPUTPATH/$4.$1-$2.ltm.nc
}

cd $INPUTPATH
FILELIST=*.1980t2099.nc

for f in $FILELIST; do
  echo $f
  mdl=`echo $f | awk -F. '{print $1}'`
  echo $mdl

  process 1980 2010 $f $mdl
  process 2020 2039 $f $mdl
  process 2040 2059 $f $mdl
  process 2060 2079 $f $mdl
  process 2080 2099 $f $mdl

done


# Now do the RCP45 data - only covers 2004-2099

FILELIST=*.2004t2099.nc

for f in $FILELIST; do
    echo $f
    mdl=`echo $f | awk -F. '{print $1}'`
    echo $mdl

    process 2020 2039 $f $mdl
    process 2040 2059 $f $mdl
    process 2060 2079 $f $mdl
    process 2080 2099 $f $mdl

done
