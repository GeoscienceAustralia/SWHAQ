#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=8:00:00
#PBS -lmem=192GB,ncpus=48,jobfs=4000MB
#PBS -joe
#PBS -lstorage=scratch/w85+gdata/w85
#PBS -v GROUP,RCP

# This script cycles through RCP scenarios and future time periods
# and calculates the absolute and relative change in ARI wind speeds,
# relative to the reference period. 
# We tmploy `cdo` to do the heavy lifting. 
#
# Variable long_name attributes are changed to indicate the actual 
# variable values. 


module purge
module load pbs
module load dot

module load cdo

FS=$IFS

BASEPATH=/scratch/w85/swhaq/hazard/output/QLD
GROUPLIST="GROUP1,GROUP2"
PERIODS="2021-2040,2041-2060,2061-2080,2081-2100"
RCPLIST="RCP45,RCP85"
IFS=","

for P in $PERIODS; do
    echo $GROUP, $RCP, $P
    REFFILE=$BASEPATH/${GROUP}\_$RCP\_1981-2020/hazard/hazard.nc
    PRJFILE=$BASEPATH/${GROUP}\_$RCP\_$P/hazard/hazard.nc
    OUTFILE=$BASEPATH/${GROUP}\_$RCP\_$P/hazard/hazard_change.nc
    RELFILE=$BASEPATH/${GROUP}\_$RCP\_$P/hazard/hazard_rel.nc
    # Difference
    cdo -L -P ${PBS_NCPUS} setattribute,wspd@long_name="Difference in ARI wind speed" \
    -smooth,radius=50km \
    -sub \
    -selvar,wspd ${PRJFILE} \
    -selvar,wspd ${REFFILE} ${OUTFILE}

    # Relative change:
    cdo -L -P ${PBS_NCPUS} setattribute,wspd@long_name="Relative change in ARI wind speed",wspd@units="%" \
    -smooth,radius=50km \
    -mulc,100 \
    -subc,1 -div \
    -selvar,wspd ${PRJFILE} \
    -selvar,wspd  ${REFFILE} ${RELFILE}

    if [[ $? -ne 0 ]]; then
        echo "cdo commands failed when processing $PRJFILE"
    else
        echo "Processed $PRJFILE"
    fi
done

FS=$IFS
