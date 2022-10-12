#!/bin/bash

SRC_DIR="$(pwd)/src"
export PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH

cd $SRC_DIR
wget -c https://downloads.unidata.ucar.edu/netcdf-c/4.9.0/netcdf-c-4.9.0.tar.gz
tar -xzvf netcdf-c-4.9.0.tar.gz

cd netcdf-c-4.9.0
make clean
export LIBS="-lhdf5_hl -lhdf5 -lz -ldl"
export CPPFLAGS=-I$PREFIX/include
export LDFLAGS=-L$PREFIX/lib
export CC=mpicc
export FC=mpifort
#./configure --prefix=$PREFIX --disable-dap -enable-pnetcdf --enable-cdf5 --enable-parallel-test --disable-shared
./configure --prefix=$PREFIX --enable-cdf5 --enable-parallel-test --enable-cdf5
make -j6
#make -j6 check
make -j6 install
