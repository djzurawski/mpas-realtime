#!/bin/bash


#zlib
cd $LIB_SRC_DIR
wget -c https://github.com/madler/zlib/archive/refs/tags/v1.2.11.tar.gz
tar -xzf v1.2.11.tar.gz
cd zlib-1.2.11
./configure --prefix=$LIB_PREFIX
make -j8
make -j8 install
