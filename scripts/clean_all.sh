#!/bin/bash

#Deletes all generated file from model run

rm ${ROOT_DIR}/data/grib/gfs*
rm ${ROOT_DIR}/tools/WPS-4.4/GRIBFILE*
rm ${ROOT_DIR}/tools/WPS-4.4/FILE*
rm ${ROOT_DIR}/MPAS-Model/history*
rm ${ROOT_DIR}/MPAS-Model/lbc*
rm ${ROOT_DIR}/MPAS-Model/diag*
rm ${ROOT_DIR}/MPAS-Model/restore*
rm ${ROOT_DIR}/MPAS-Model/FILE*
rm ${ROOT_DIR}/MPAS-Model/*.init.nc
