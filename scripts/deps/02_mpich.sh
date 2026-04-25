#!/bin/bash


cd $LIB_SRC_DIR
wget -c https://www.mpich.org/static/downloads/5.0.0/mpich-5.0.0.tar.gz
tar -xzf mpich-5.0.0.tar.gz
cd mpich-5.0.0
FFLAGS=-fallow-argument-mismatch FCFLAGS=-fallow-argument-mismatch ./configure --prefix=$LIB_PREFIX
make -j$(nproc)
make -j$(nproc) install
