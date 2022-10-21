#!/bin/bash

cd $TOOLS_DIR
wget -c http://glaros.dtc.umn.edu/gkhome/fetch/sw/metis/metis-5.1.0.tar.gz
tar -xzvf metis-5.1.0.tar.gz
cd metis-5.1.0
make config
make -j$CPU_CORES
