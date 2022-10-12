#!/bin/bash

source $(pwd)/scripts/env.sh

cd $LIB_SRC_DIR

export CPPFLAGS="-I$LIB_PREFIX/include"
export LDFLAGS="-L$LIB_PREFIX/lib"
export CC=mpicc
export FC=mpifort
wget -c https://github.com/NCAR/ParallelIO/archive/refs/tags/pio2_5_9.tar.gz
tar -xzvf pio2_5_9.tar.gz
cd ParallelIO-pio2_5_9
cmake \
    -DNetCDF_C_PATH=$LIB_PREFIX \
    -DNetCDF_Fortran_PATH=$LIB_PREFIX \
    -DPnetCDF_PATH=$LIB_PREFIX \
    -DCMAKE_INSTALL_LIB_PREFIX=$LIB_PREFIX \
    -DPIO_ENABLE_TIMING=OFF $LIB_PREFIX \
    .
make -j6
make -j6 install
