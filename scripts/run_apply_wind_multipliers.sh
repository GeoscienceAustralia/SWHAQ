#!/bin/bash

#PBS -P w85
#PBS -q normal
#PBS -N wm_max_aep
#PBS -m abe
#PBS -M kieran.ricardo@ga.gov.au
#PBS -l walltime=10:00:00
#PBS -l mem=100GB,ncpus=4,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -l storage=gdata/v10+gdata/w85

module purge

module use /g/data/v10/public/modules/modulefiles
module load dea/20210527

SOFTWARE=/g/data/w85/software

# Add PyKrige and TCRM code to the path:
export PYTHONPATH=$SOFTWARE:$SOFTWARE/tcrm/master:$PYTHONPATH

cd $HOME/SWHAQ/scripts

python3 ari_interpolate.py
python3 apply_wind_multipliers.py
python3 visualise_aep_windspeed.py
