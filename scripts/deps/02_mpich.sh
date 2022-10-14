#!/bin/bash


cd $LIB_SRC_DIR
wget -c https://www.mpich.org/static/downloads/4.0.2/mpich-4.0.2.tar.gz
tar -xzvf mpich-4.0.2.tar.gz
cd mpich-4.0.2
./configure --prefix=$LIB_PREFIX
make -j6
make -j6 install
