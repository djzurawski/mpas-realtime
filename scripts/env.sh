#!/bin/bash

export LIB_SRC_DIR="$(pwd)/library/src"
export LIB_PREFIX="$(pwd)/library"

export LD_LIBRARY_PATH=$LIB_PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$LIB_PREFIX/bin:$PATH
export PKG_CONFIG_PATH=$LIB_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH

export NETCDF=$LIB_PREFIX
export NETCDF_PATH=$LIB_PREFIX
export PNETCDF_PATH=$LIB_PREFIX
export JASPERLIB=$LIB_PREFIX/lib
export JASPERINC=$LIB_PREFIX/include
