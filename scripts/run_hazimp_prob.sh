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

# This job script spawns a bunch of new shells to run multiple scripts in
# parallel. As this is the parent job, you must request sufficient resources
# (i.e. memory and job file storage) to ensure *all* processes can run
# concurrently. 

# The actual script to run (and any required command line arguments) are
# specified in the companion "cmd.txt" file - it is passed to the nci-parallel
# program using the --input-file option below
 
export ncores_per_task=1
export ncores_per_node=48
 
# Must include `#PBS -l storage=scratch/w85+gdata/hh5` if the job
# needs access to `/scratch/w85/` and `/g/data/hh5/`. Details on:
# https://opus.nci.org.au/display/Help/PBS+Directives+Explained
 
mpirun -np $((PBS_NCPUS/ncores_per_task))  --map-by ppr:$((ncores_per_node/ncores_per_task)):NODE:PE=${ncores_per_task}:OVERSUBSCRIBE nci-parallel --input-file /g/data/w85/QFES_SWHA/scripts/cmd.txt --timeout 4000