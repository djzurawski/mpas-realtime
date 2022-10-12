#!/bin/bash

SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH


cd $SRC_DIR
wget -c https://downloads.unidata.ucar.edu/netcdf-fortran/4.6.0/netcdf-fortran-4.6.0.tar.gz
tar -xzvf netcdf-fortran-4.6.0.tar.gz
cd netcdf-fortran-4.6.0
export CPPFLAGS=-I$PREFIX/include
export LDFLAGS=-L$PREFIX/lib
export LIBS="-L$PREFIX/lib -lnetcdf -lpnetcdf -lm -lbz2 -lxml2 -lhdf5_hl -lhdf5 -lz -ldl"
export NETCDF=$PREFIX
export FC=mpif90
export F77=mpif77
./configure --prefix=$PREFIX --enable-parallel-tests
make -j6
make -j6 check
make -j6 install
