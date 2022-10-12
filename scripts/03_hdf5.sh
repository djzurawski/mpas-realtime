#!/bin/bash

SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH

cd $SRC_DIR
wget -c https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.2/src/hdf5-1.12.2.tar.gz
tar -xzvf hdf5-1.12.2.tar.gz
cd hdf5-1.12.2
export FC=mpif90
export CC=mpicc
export CXX=mpicxx
./configure --prefix=$PREFIX --with-zlib=$PREFIX --enable-parallel
make -j6
#make -j6 check
make -j6 install
