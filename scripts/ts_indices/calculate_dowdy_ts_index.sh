#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -m ae
#PBS -M kieran.ricardo@ga.gov.au
#PBS -l walltime=4:00:00
#PBS -lmem=128GB,ncpus=48,jobfs=4000MB
#PBS -joe
#PBS -l storage=scratch/w85+gdata/w85+gdata/rt52+gdata/dk92+gdata/v10

module purge
module use /g/data/v10/public/modules/modulefiles
module load dea/20210527

cd $HOME/SWHAQ/scripts/ts_indices
pip install metpy
mpiexec -n 44 python extract_dowdy_ts_index.py
