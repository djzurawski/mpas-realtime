#!/bin/bash

cd $PROGRAM_DIR
wget -c https://github.com/wrf-model/WPS/archive/refs/tags/v4.4.tar.gz
tar -xzf v4.4.tar.gz
rm v4.4.tar.gz
cd WPS-4.4
./configure --build-grib2-libs --nowrf
./compile

echo "Ignore compilation errors. If ungrib.exe exists you are good."
