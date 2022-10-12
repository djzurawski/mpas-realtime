#!/bin/bash


SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH

cd $SRC_DIR

export CPPFLAGS="-I$PREFIX/include"
export LDFLAGS="-L$PREFIX/lib"
export CC=mpicc
export FC=mpif90

#CC=mpicc FC=mpif90 cmake -DNetCDF_C_PATH=$PREFIX \
#         -DNetCDF_Fortran_PATH=$PREFIX \
#         -DPnetCDF_PATH=$PREFIX \
#	 -DCMAKE_INSTALL_PREFIX=$PREFIX \
#cmake -v --prefix=$PREFIX .

wget -c https://github.com/NCAR/ParallelIO/archive/refs/tags/pio2_5_9.tar.gz
tar -xzvf pio2_5_9.tar.gz
cd ParallelIO-pio2_5_9
export CC=mpicc
export FC=mpifort
cmake \
    -DNetCDF_C_PATH=$PREFIX \
    -DNetCDF_Fortran_PATH=$PREFIX \
    -DPnetCDF_PATH=$PREFIX \
    -DCMAKE_INSTALL_PREFIX=$PREFIX \
    -DPIO_ENABLE_TIMING=OFF $PREFIX \
    .
make -j6
make -j6 install
