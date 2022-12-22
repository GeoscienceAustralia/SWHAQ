#!/bin/bash

#PBS -P w85
#PBS -q normal
#PBS -N wm_max_aep
#PBS -m abe
#PBS -M craig.arthur@ga.gov.au
#PBS -l walltime=10:00:00
#PBS -l mem=100GB,ncpus=4,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -l storage=gdata/hh5+gdata/w85

SOFTWARE=/g/data/w85/software

# Add PyKrige and TCRM code to the path:
export PYTHONPATH=$PYTHONPATH:$SOFTWARE/tcrm/master
module purge

module use /g/data/hh5/public/modules
module load conda/analysis3


#cd $HOME/SWHAQ/scripts
cd /g/data/w85/QFES_SWHA/scripts
python3 ari_interpolate.py
python3 apply_wind_multipliers.py

module load nco
module load cdo

cd /g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep_pp

for FILE in windspeed_*_yr.nc; do
    OUTFILE=${FILE//.nc/_clip.nc}
    echo $OUTFILE
    ncks -O -d longitude,151.,154. -d latitude,-30.,-24. $FILE tmp.nc
    ncatted -a GeoTransform,spatial_ref,m,c,"151.000138888696 0.0002777777779999919 0.0 -24.000138888696 0.0 -0.0002777777779999991" tmp.nc
    cdo -O -L -s -setrtomiss,-999999.,0. -setmissval,-9999. tmp.nc $OUTFILE
    rm tmp.nc
done

#python3 visualise_aep_windspeed.py
