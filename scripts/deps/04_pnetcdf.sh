#!/bin/bash

source $(pwd)/scripts/env.sh

cd $LIB_SRC_DIR
wget -c https://parallel-netcdf.github.io/Release/pnetcdf-1.12.3.tar.gz
tar -xzvf pnetcdf-1.12.3.tar.gz
cd pnetcdf-1.12.3
export CC=gcc
export CXX=g++
export F77=gfortran
export FC=gfortran
export MPICC=mpicc
export MPICXX=mpicxx
export MPIF77=mpif77
export MPIF90=mpif90
./configure --prefix=$LIB_PREFIX --disable-dap --enable-netcdf4 --enable-pnetcdf --enable-cdf5 --enable-parallel-tests --disable-shared
make -j6
make -j6 testing
make -j6 install
