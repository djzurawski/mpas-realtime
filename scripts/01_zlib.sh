#!/bin/bash

SRC_DIR="$(pwd)/src"
PREFIX="$(pwd)"

export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
export PATH=$PREFIX/bin:$PATH


#zlib
cd $SRC_DIR
wget -c https://github.com/madler/zlib/archive/refs/tags/v1.2.11.tar.gz
tar -xvzf v1.2.11.tar.gz
cd zlib-1.2.11
./configure --prefix=$PREFIX
make -j4
make -j4 install
