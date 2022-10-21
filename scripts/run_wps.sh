#!/bin/bash

cd ${TOOLS_DIR}/WPS-4.4
./link_grib.csh ../../data/grib/
ln -s ungrib/Variable_Tables/Vtable.GFS Vtable
./ungrib.exe
