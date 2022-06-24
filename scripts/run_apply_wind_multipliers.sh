#!/bin/bash

#PBS -P w85
#PBS -q normal
#PBS -N wm_max_aep
#PBS -m abe
#PBS -M kieran.ricardo@ga.gov.au
#PBS -l walltime=0:14:00
#PBS -l mem=100GB,ncpus=16,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -l storage=gdata/v10+gdata/w85

module purge

module use /g/data/v10/public/modules/modulefiles
module load dea/20210527

python3 $HOME/SWHAQ/scripts/apply_wind_multipliers.py