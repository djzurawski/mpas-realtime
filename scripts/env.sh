#!/bin/bash

export LIB_SRC_DIR="$(pwd)/libray/src"
export LIB_PREFIX="$(pwd)/library"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$LIB_PREFIX/bin:$PATH

export JASPERLIB=$LIB_PREFIX/lib
export JASPERINC=$LIB_PREFIX/include