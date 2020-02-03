Severe Wind Hazard Assessment for Queensland
============================================

The Severe Wind Hazard Assessment for Queensland (SWHA(Q)) project aims 
to to provide realistic and tangible data on the potential physical impacts
of severe tropical cyclones on Queensland communities to enable the emergency 
management sector and local government to more effectively engage with the 
community. The data and information will also assist with the understanding of 
the potential impacts from climate change and inform strategic risk treatment 
strategies.  

The project is a collaboration between Geoscience Australia and Queensland 
Fire and Emergency Services (QFES), with additional support from Department 
of Environment and Science Queensland (DES). 

This repository holds scripts and configuration files used in the modelling and
analysis components of the project. References are made to other code bases
maintained by Geoscience Australia - e.g. 
[TCRM](https://github.com/GeoscienceAustralia/tcrm) and 
[HazImp](https://github.com/GeoscienceAustralia/hazimp).

Contact:
Craig Arthur: craig.arthur@ga.gov.au

Shane Martin: shane.martin@ga.gov.au


This directory contains input, output and model configuration files used for
the Severe Wind Hazard Assessment for Queensland project (2019-2020). 

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


\* This folder is under version control to track changes to configuration files.


configuration:
--------------

tcrm:: Configuration files for running TCRM

pm:: Configuration files for running the processMultipliers code

hazimp:: Configuration files for running HazImp

jobs:: Job scripts to run processes on gadi.nci.org.au

exposure:
---------

Input exposure files, using the TCRM formats extracted from NEXIS. These 
contain building point information used to calculate impacts, plus other 
sources of exposure information used in this and related projects

multipliers:
------------

Local wind multipliers for all of Queensland.

input:: input land cover (terrain) data and DEMs

output:: Tiled output for each domain

tracks:
-------

NetCDF format tracks (extracted from TCHA18) of the scenarios used in the 
project. These are selected in consultation with QFES.

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

2020-02-03
