#!/bin/bash

source $(pwd)/scripts/env.sh

LIB_PREFIX="$(pwd)/library"
PROGRAM_DIR="$(pwd)/program"

export PIO=$LIB_PREFIX
export NETCDF=$LIB_PREFIX
export PNETCDF=$LIB_PREFIX
export LD_LIBRARY_PATH=$LIB_PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$LIB_PREFIX/bin:$PATH
export MPAS_EXTERNAL_LIBS="-L$LIB_PREFIX/lib -lhdf5_hl -lhdf5 -ldl -lz"
export MPAS_EXTERNAL_INCLUDES="-I$LIB_PREFIX/include"

cd $PROGRAM_DIR
wget -c https://github.com/MPAS-Dev/MPAS-Model/archive/refs/tags/v7.3.tar.gz
tar -xzvf v7.3.tar.gz
cd MPAS-Model-7.3
make clean CORE=init_atmosphere USE_PIO2=true
make -j6 gfortran CORE=init_atmosphere USE_PIO2=true PRECISION=single
make clean CORE=atmosphere USE_PIO2=true
make -j6 gfortran CORE=atmosphere USE_PIO2=true PRECISION=single
