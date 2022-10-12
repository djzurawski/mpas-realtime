#!/bin/bash

source $(pwd)/scripts/env.sh

cd $LIB_SRC_DIR
wget -c https://www.ece.uvic.ca/~frodo/jasper/software/jasper-2.0.14.tar.gz
tar -xvzf jasper-2.0.14.tar.gz
cd jasper-2.0.14
cmake -G "Unix Makefiles" -H./ -B./build -DCMAKE_INSTALL_PREFIX=$LIB_PREFIX
cd build
make -j8
make -j8 install
