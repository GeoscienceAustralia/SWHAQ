#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=3:00:00
#PBS -lmem=32GB,ncpus=16,jobfs=4000MB
#PBS -joe
#PBS -lstorage=scratch/w85+gdata/w85

# This script cycles through RCP scenarios and future time periods
# and calculates the absolute and relative change in ARI wind speeds,
# relative to the reference period. 
# We employ `cdo` to do the heavy lifting. Operators are chained, so
# only one command line is executed and no temporary files are written
# to disk
#
# Variable long_name attributes are changed to indicate the actual 
# variable values. 


module purge
module load pbs
module load dot

module load cdo

FS=$IFS

#BASEPATH=/scratch/w85/swhaq/hazard/output/QLD
BASEPATH=/g/data/w85/QFES_SWHA/hazard/output
TCHAPATH=$BASEPATH/HISTORICAL_1981-2010/hazard/hazard.nc
GROUPLIST="GROUP1,GROUP2"
PERIODS="2021-2040,2041-2060,2061-2080,2081-2100"
RCPLIST="RCP45,RCP85"
IFS=","

echo $GROUPLIST
for P in $PERIODS; do
    for R in $RCPLIST; do
        for GROUP in $GROUPLIST; do
            echo $GROUP, $R, $P
            REFFILE=$BASEPATH/${GROUP}\_$R\_1981-2020/hazard/hazard.nc
            PRJFILE=$BASEPATH/${GROUP}\_$R\_$P/hazard/hazard.nc
            OUTFILE=$BASEPATH/${GROUP}\_$R\_$P/hazard/hazard_rel_hist.nc
            RELFILE=$BASEPATH/${GROUP}\_$R\_$P/hazard/hazard_rel.nc

            # Apply relative change:
            cdo -L -mul \
                -setrtomiss,0,5 \
                -sellonlatbox,135,160,-30,-5 \
                -selvar,wspd ${TCHAPATH} \
                -addc,1 -divc,100 \
                -selvar,wspd ${RELFILE} ${OUTFILE}

            if [[ $? -ne 0 ]]; then
                echo "cdo commands failed when processing $PRJFILE"
            else
                echo "Processed $PRJFILE"
            fi
        done
    done
done

FS=$IFS
