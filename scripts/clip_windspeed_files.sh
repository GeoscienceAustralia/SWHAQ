# Short shell script to clip the spatial extent of local scale wind hazard grids
# to a smaller extent. Initial steps of processing covered all of Queensland,
# but to ensure efficient processing of subsequent steps we clip to a smaller
# region over southeast Queensland

module load nco

cd /g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep

for FILE in windspeed_*_yr.nc; do
    OUTFILE=${FILE//.nc/_clip.nc}
    echo $OUTFILE
    ncks -O -d x,151.,154. -d y,-30.,-24. $FILE $OUTFILE
done