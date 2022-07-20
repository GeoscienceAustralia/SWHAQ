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

#module use /g/data/v10/public/modules/modulefiles
#module load dea/20210527
module use /g/data/hh5/public/modules
module load conda/analysis3


#cd $HOME/SWHAQ/scripts
cd /g/data/w85/QFES_SWHA/scripts
python3 ari_interpolate.py
python3 apply_wind_multipliers.py
python3 visualise_aep_windspeed.py
