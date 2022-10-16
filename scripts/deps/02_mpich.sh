#!/bin/bash


cd $LIB_SRC_DIR
wget -c https://www.mpich.org/static/downloads/4.0.2/mpich-4.0.2.tar.gz
tar -xzf mpich-4.0.2.tar.gz
cd mpich-4.0.2
FFLAGS=-fallow-argument-mismatch FCFLAGS=-fallow-argument-mismatch ./configure --prefix=$LIB_PREFIX 
make -j8
make -j8 install
