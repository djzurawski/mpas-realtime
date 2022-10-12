#!/bin/bash

PREFIX="$(pwd)"
SRC_DIR="$(pwd)/src"

export PIO=$PREFIX
export NETCDF=$PREFIX
export PNETCDF=$PREFIX
export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH
export MPAS_EXTERNAL_LIBS="-L$PREFIX/lib -lhdf5_hl -lhdf5 -ldl -lz"
export MPAS_EXTERNAL_INCLUDES="-I$PREFIX/include"

cd $SRC_DIR
#wget -c https://github.com/MPAS-Dev/MPAS-Model/archive/refs/tags/v7.3.tar.gz
#tar -xzvf v7.3.tar.gz
cd $PREFIX/src/MPAS-Model-7.3
#make -j6 gfortran CORE=init_atmosphere USE_PIO2=true
make clean CORE=atmosphere USE_PIO2=true
make -j6 gfortran CORE=atmosphere USE_PIO2=true
