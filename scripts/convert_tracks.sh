#!/bin/bash
#PBS -Pw85
#PBS -qnormal
#PBS -N trackconversion
#PBS -m ae
#PBS -M craig.arthur@ga.gov.au
#PBS -lwalltime=48:00:00
#PBS -lmem=16GB,ncpus=16,jobfs=12GB
#PBS -joe
#PBS -lstorage=gdata/w85+scratch/w85

module purge
module load pbs
module load dot

module load python3/3.7.4
module load netcdf/4.6.3
module load hdf5/1.10.5
module load geos/3.8.0
module load proj/6.2.1
module load gdal/3.0.2

# Need to ensure we get the correct paths to access the local version of gdal bindings. 
# The module versions are compiled against Python3.6
export PYTHONPATH=/g/data/w85/.local/lib/python3.7/site-packages:$PYTHONPATH

# Add the local Python-based scripts to the path:
export PATH=/g/data/w85/.local/bin:$PATH

# Needs to be resolved, but this suppresses an error related to HDF5 libs
export HDF5_DISABLE_VERSION_CHECK=2

export PYTHONPATH=$PYTHONPATH:$HOME/tcrm:$HOME/tcrm/Utilities

GROUPLIST="GROUP2,"
RCPLIST="RCP45,RCP85"
PERIODS="1981-2020,2021-2040,2041-2060,2061-2080,2081-2100"
IFS=","
BASEPATH=/scratch/w85/swhaq/hazard/output/QLD
TMPPATH=${PBS_JOBFS}/TMP 
if [ ! -d $TMPPATH ]; then
    mkdir $TMPPATH
    mkdir $TMPPATH/tracks
fi

BASEOUTPUT=/scratch/w85/cxa547/swhaq/tracks2csv
if [ ! -d $BASEOUTPUT ]; then
    mkdir $BASEOUTPUT
fi

for G in $GROUPLIST; do
    for R in $RCPLIST; do
        for P in $PERIODS; do
        INPUTPATH=$BASEPATH/$G\_$R\_$P/
        if [ ! -d $INPUTPATH ]; then
            echo "Appears that $INPUTPATH is missing, skipping..."
            continue
        fi
        echo $INPUTPATH
        OUTPUTPATH=$TMPPATH
        echo "Running tracks2csv.py for files in $INPUTPATH"
        # Note the Python script adds "tracks" to both the input and output paths
        python3 $HOME/tcrm/Utilities/tracks2csv.py -i $INPUTPATH -o $OUTPUTPATH

        cd $TMPPATH/tracks
        echo "Creating tar file $G\_$R\_$P.tar.gz"
        tar czf $G\_$R\_$P.tar.gz *.csv
        rm -rf *.csv
	mv $G\_$R\_$P.tar.gz $BASEOUTPUT
        done
    done
done
#rm -rf $TMPPATH
