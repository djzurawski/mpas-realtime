#!/bin/bash

source $(pwd)/scripts/env.sh

echo $LD_LIBRARY_PATH

cd program/
#wget -c https://github.com/wrf-model/WPS/archive/refs/tags/v4.4.tar.gz
#tar -xzvf v4.4.tar.gz
#rm v4.4.tar.gz
cd WPS-4.4
./configure --build-grib2-libs --nowrf
./compile
