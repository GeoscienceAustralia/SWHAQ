#!/bin/bash

#PBS -P w85
#PBS -qnormal
#PBS -N rh
#PBS -m abe
#PBS -M kieran.ricardo@ga.gov.au
#PBS -l walltime=0:14:00
#PBS -l mem=100GB,ncpus=4,jobfs=4000MB
#PBS -W umask=0002
#PBS -joe
#PBS -l storage=gdata/v10+gdata/w85

module purge

module use /g/data/v10/public/modules/modulefiles
module load dea/20210527

cd $HOME/SWHAQ

python3 apply_windmu.py