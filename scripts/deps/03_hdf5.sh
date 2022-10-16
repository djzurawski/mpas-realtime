#!/bin/bash

cd $LIB_SRC_DIR
wget -c https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.2/src/hdf5-1.12.2.tar.gz
tar -xzf hdf5-1.12.2.tar.gz
cd hdf5-1.12.2
export FC=mpif90
export CC=mpicc
export CXX=mpicxx
./configure --prefix=$LIB_PREFIX --with-zlib=$LIB_PREFIX --enable-parallel
make -j8
#make -j6 check
make -j8 install
