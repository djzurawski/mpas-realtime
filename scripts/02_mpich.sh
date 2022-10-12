#!/bin/bash

SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH


cd $SRC_DIR
wget -c https://www.mpich.org/static/downloads/4.0.2/mpich-4.0.2.tar.gz
tar -xzvf mpich-4.0.2.tar.gz
cd mpich-4.0.2
./configure --prefix=$PREFIX
make -j6
make -j6 install
