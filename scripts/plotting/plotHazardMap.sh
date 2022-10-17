#!/bin/bash

#PBS -P w85
#PBS -q normal
#PBS -N plotHazard
#PBS -m abe
#PBS -M craig.arthur@ga.gov.au
#PBS -l walltime=2:00:00
#PBS -l mem=100GB,ncpus=4,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -l storage=gdata/hh5+gdata/w85

module use /g/data/hh5/public/modules
module load conda/analysis3

cd /g/data/w85/QFES_SWHA/scripts/plotting

python3 plotHazardMap.py