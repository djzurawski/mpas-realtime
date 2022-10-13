#!/bin/bash

source $(pwd)/scripts/env.sh

cd $LIB_SRC_DIR

wget -c https://downloads.unidata.ucar.edu/netcdf-c/4.9.0/netcdf-c-4.9.0.tar.gz
tar -xzvf netcdf-c-4.9.0.tar.gz

cd netcdf-c-4.9.0
make clean
export LIBS="-lhdf5_hl -lhdf5 -lz -ldl"
export CPPFLAGS=-I$LIB_PREFIX/include
export LDFLAGS=-L$LIB_PREFIX/lib
export CC=mpicc
export FC=mpifort
./configure --prefix=$LIB_PREFIX --enable-cdf5 --enable-parallel-test --enable-cdf5
make -j6
make -j6 check
make -j6 install
