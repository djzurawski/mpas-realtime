#!/bin/bash

#sudo apt update
#sudo apt install gcc gfortran make m4

SCRIPT_DIR=$(dirname $0)
SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH


#zlib
cd $SRC_DIR
wget -c https://github.com/madler/zlib/archive/refs/tags/v1.2.11.tar.gz
tar -xvzf v1.2.11.tar.gz
cd zlib-1.2.11
./configure --prefix=$PREFIX
make -j4
make -j4 install

#hdf5
cd $SRC_DIR
wget -c https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-1.12.2/src/hdf5-1.12.2.tar.gz
tar -xzvf hdf5-1.12.2.tar.gz
cd hdf5-1.12.2
./configure --prefix=$PREFIX --with-zlib=$PREFIX --enable-hl --enable-fortran
make -j4
make -j4 install


#netcdf-c
cd $SRC_DIR
wget -c https://downloads.unidata.ucar.edu/netcdf-c/4.9.0/netcdf-c-4.9.0.tar.gz
tar -xzvf netcdf-c-4.9.0.tar.gz

cd netcdf-c-4.9.0
export CPPFLAGS=-I$PREFIX/include
export LDFLAGS=-L$PREFIX/lib
export CC=mpicc
export FC=mpifort
./configure --prefix=$PREFIX
make -j4
make -j4 install

#netcdf-fortran
cd $SRC_DIR
wget -c https://downloads.unidata.ucar.edu/netcdf-fortran/4.6.0/netcdf-fortran-4.6.0.tar.gz
tar -xzvf netcdf-fortran-4.6.0.tar.gz
cd netcdf-fortran-4.6.0
export CPPFLAGS=-I$PREFIX/include
export LDFLAGS=-L$PREFIX/lib
export LIBS="-lnetcdf -lhdf5_hl -lhdf5 -lz"
./configure --prefix=$PREFIX
make -j4
make -j4 install


#mpich
cd $SRC_DIR
wget -c https://www.mpich.org/static/downloads/4.0.2/mpich-4.0.2.tar.gz
tar -xzvf mpich-4.0.2.tar.gz
cd mpich-4.0.2
./configure --prefix=$PREFIX
make -j4
make -j4 install


#parallel netcdf
cd $SRC_DIR
wget -c https://parallel-netcdf.github.io/Release/pnetcdf-1.12.3.tar.gz
tar -xzvf pnetcdf-1.12.3.tar.gz
cd pnetcdf-1.12.3
./configure --prefix=$PREFIX
make -j4
make -j4 install

# PIO
cd $SRC_DIR
wget -c https://github.com/NCAR/ParallelIO/archive/refs/tags/pio1_7_1.tar.gz
tar -xzvf pio1_7_1.tar.gz
cd ParallelIO-pio1_7_1/pio
export PATH=$PREFIX/lib:$PATH
export NETCDF_PATH=$PREFIX
export MPFC=mpif90
export PNETCDF_PATH=$PREFIX
./configure --prefix=$PREFIX --disable-netcdf --disable-mpiio
make -j4
make install -j4
