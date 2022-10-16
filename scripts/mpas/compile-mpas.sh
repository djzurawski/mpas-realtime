#!/bin/bash


export MPAS_EXTERNAL_LIBS="-L$LIB_PREFIX/lib -lhdf5_hl -lhdf5 -ldl -lz"
export MPAS_EXTERNAL_INCLUDES="-I$LIB_PREFIX/include"

cd $PROGRAM_DIR
#wget -c https://github.com/MPAS-Dev/MPAS-Model/archive/refs/tags/v7.3.tar.gz
#tar -xzvf v7.3.tar.gz
#cd MPAS-Model-7.3
cd MPAS-Model
make clean CORE=init_atmosphere USE_PIO2=true
make -j8 gfortran CORE=init_atmosphere USE_PIO2=true PRECISION=single
make clean CORE=atmosphere USE_PIO2=true
make -j8 gfortran CORE=atmosphere USE_PIO2=true PRECISION=single
