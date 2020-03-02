#!/bin/bash
FILELIST=/scratch/w85/cxa547/swhaq/data/*.1980t2099.nc

for f in $FILELIST; do
  echo $f
  mdl=`echo $f | awk -F. '{print $1}'`
  echo $mdl
  startyear=1980
  endyear=2010
  cmd="cdo -ydaymean -selyear,$startyear/$endyear $mdl.1980t2099.nc $mdl.$startyear-$endyear.ltm.nc"
  echo $cmd
  $cmd

  startyear=2020
  endyear=2039
  cdo -ydaymean -selyear,$startyear/$endyear $mdl.1980t2099.nc $mdl.$startyear-$endyear.ltm.nc

  startyear=2040
  endyear=2059
  cdo -ydaymean -selyear,$startyear/$endyear $mdl.1980t2099.nc $mdl.$startyear-$endyear.ltm.nc

  startyear=2060
  endyear=2079
  cdo -ydaymean -selyear,$startyear/$endyear $mdl.1980t2099.nc $mdl.$startyear-$endyear.ltm.nc

  startyear=2080
  endyear=2099
  cdo -ydaymean -selyear,$startyear/$endyear $mdl.1980t2099.nc $mdl.$startyear-$endyear.ltm.nc

done

