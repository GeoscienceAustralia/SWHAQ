Severe Wind Hazard Assessment for Queensland
============================================

This directory contains input, output and model configuration files used for the Severe Wind Hazard Assessment for Queensland project (2019-2020). 

Directory structure:
--------------------

Top-level structure of the data in this collection ::

  /g/data/w85/QFES_SWHA/
  |-- configuration* -- configuration files for TCRM, processMultipliers, HazImp
  |-- exposure -- exposure database files (CSV, extracted from NEXIS)
  |-- multipliers -- local wind multiplier data, subdirectories for each community
  |-- tracks -- Event tracks, top-level contains netcdf-format files
  | `-- shapefile -- Event tracks, ESRI shapefile format
  `-- wind
   |-- local -- local wind fields, subdirectories for each scenario
    `-- regional -- regional wind fields, subdirectories for each scenario


* This folder is under version control to track changes to configuration files.


configuration:
--------------

tcrm: Configuration files for running TCRM
pm: Configuration files for running the processMultipliers code
hazimp: Configuration files for running HazImp

exposure:
---------

Input exposure files, using the TCRM formats extracted from NEXIS. These contain building point information used to calculate impacts

multipliers:
------------

Local wind multipliers for each community analysed in the project.

input: input land cover (terrain) data and DEMs
output: Tiled output for each domain

tracks:
-------

NetCDF format tracks (extracted from TCHA18) of the scenarios used in the project. These are selected in consultation with QFES.

A subdirectoy contains ESRI shape file versions of the tracks.

wind:
-----

The regional and local wind fields of all scenarios created in the project.



Contacts:
---------

Craig Arthur
Geoscience Australia
craig.arthur@ga.gov.au

Last updated:
-------------

2019-02-28
