#!/bin/bash
#PBS -Pw85
#PBS -qhugemem
#PBS -N hazimpretro
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=2:00:00
#PBS -lmem=1024GB,ncpus=48,jobfs=4000MB
#PBS -joe
#PBS -W umask=0002
#PBS -lstorage=gdata/w85
 
# Load module, always specify version number.
module load nci-parallel/1.0.0a
 
export ncores_per_task=1
export ncores_per_node=48
 
# Must include `#PBS -l storage=scratch/ab12+gdata/yz98` if the job
# needs access to `/scratch/ab12/` and `/g/data/yz98/`. Details on:
# https://opus.nci.org.au/display/Help/PBS+Directives+Explained
 
mpirun -np $((PBS_NCPUS/ncores_per_task))  --map-by ppr:$((ncores_per_node/ncores_per_task)):NODE:PE=${ncores_per_task}:OVERSUBSCRIBE nci-parallel --input-file /g/data/w85/QFES_SWHA/scripts/cmd.txt --timeout 4000