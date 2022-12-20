# Short shell script to clip the spatial extent of local scale wind hazard grids
# to a smaller extent. Initial steps of processing covered all of Queensland,
# but to ensure efficient processing of subsequent steps we clip to a smaller
# region over southeast Queensland.
#
# Note this requires two steps: clipping the data, then modifying the
# GeoTransfom attribute of the spatial_ref variable to update the coords of the
# reference grid point (upper left corner grid cell)
#
# Craig Arthur
# 2022-12-20

module load nco

cd /g/data/w85/QFES_SWHA/hazard/output/wm_combined_aep_pp

for FILE in windspeed_*_yr.nc; do
    OUTFILE=${FILE//.nc/_clip.nc}
    echo $OUTFILE
    ncks -O -d longitude,151.,154. -d latitude,-30.,-24. $FILE $OUTFILE
    ncatted -a GeoTransform,spatial_ref,m,c,"151.000138888696 0.0002777777779999919 0.0 -24.000138888696 0.0 -0.0002777777779999991" $OUTFILE
done