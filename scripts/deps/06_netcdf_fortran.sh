#!/bin/bash


cd $LIB_SRC_DIR
wget -c https://downloads.unidata.ucar.edu/netcdf-fortran/4.6.0/netcdf-fortran-4.6.0.tar.gz
tar -xzvf netcdf-fortran-4.6.0.tar.gz
cd netcdf-fortran-4.6.0
make clean
export CPPFLAGS=-I$LIB_PREFIX/include
export LDFLAGS=-L$LIB_PREFIX/lib
export LIBS="-L$LIB_PREFIX/lib -lnetcdf -lpnetcdf -lm -lbz2 -lxml2 -lhdf5_hl -lhdf5 -lz -ldl"
export NETCDF=$LIB_PREFIX
export FC=mpif90
export F77=mpif77
./configure --prefix=$LIB_PREFIX --enable-parallel-tests
make -j6
make -j6 check
make -j6 install
