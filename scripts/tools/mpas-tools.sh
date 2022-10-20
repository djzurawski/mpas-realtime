#!/bin/bash

cd $TOOLS_DIR
git clone https://github.com/MPAS-Dev/MPAS-Tools.git
cd $TOOLS_DIR/MPAS-Tools/mesh_tools/grid_rotate/
make
cd $TOOLS_DIR
git clone https://github.com/MPAS-Dev/MPAS-Limited-Area.git
