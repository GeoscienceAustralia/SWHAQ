#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -m ae
#PBS -M kieran.ricardo@ga.gov.au
#PBS -lwalltime=4:00:00
#PBS -lmem=128GB,ncpus=48,jobfs=4000MB
#PBS -joe
#PBS -lstorage=scratch/w85+gdata/w85+gdata/rt52+gdata/dk92


module purge
module load pbs
module load dot

module use /g/data/dk92/apps/Modules/modulefiles
module load NCI-data-analysis/2021.09
module load openmpi/4.1.0

module use /g/data/v10/public/modules/modulefiles
module load dea/20210527

cd $HOME/SWHAQ/scripts
mpiexec -n 44 python3 extract_ts_indices.py
