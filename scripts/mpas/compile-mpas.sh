#!/bin/bash

LIB_PREFIX="$(pwd)/library"

CPU_CORES=$(nproc)

cd $ROOT_DIR
git clone https://github.com/MPAS-Dev/MPAS-Model
cd MPAS-Model
make clean CORE=init_atmosphere USE_PIO2=true
make -j $CPU_CORES gfortran CORE=init_atmosphere USE_PIO2=true PRECISION=single
make clean CORE=atmosphere USE_PIO2=true
make -j $CPU_CORES gfortran CORE=atmosphere USE_PIO2=true PRECISION=single
./build-tables
