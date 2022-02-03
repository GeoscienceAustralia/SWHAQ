#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N monmeanpi
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=06:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4GB
#PBS -W umask=0002
#PBS -joe
#PBS -lstorage=gdata/w85

# This script processes daily potential intensity files into monthly mean and maximum values for a range of time periods
# We calculate monthly mean, minimum and maximum values for all variables in the PI files (vmax and pmin)
# All data ends up in a single folder, so you may want to move it around after processing is complete.
# Takes about 90 minutes on NCI's gadi machine - YMMV depending on processor speed and I/O.


module purge
module load pbs
module load dot

module load cdo

INPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/pi/Daily/
OUTPUTPATH=/g/data/w85/QFES_SWHA/hazard/input/pi/monmean/

process()
{
    # Run a bunch of cdo commands:
    echo "Processing $3"
    cdo -monmean -selyear,$1/$2 $3 $OUTPUTPATH/$4.$1-$2.monmean.nc
    cdo -monmin -selyear,$1/$2 $3 $OUTPUTPATH/$4.$1-$2.monmin.nc
    cdo -monmax -selyear,$1/$2 $3 $OUTPUTPATH/$4.$1-$2.monmax.nc
}

cd $INPUTPATH

# This is the RCP85 data:
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


# Now do the RCP45 data - only covers 2004-2099 so we drop the 1980-2010 period
cd $INPUTPATH
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

