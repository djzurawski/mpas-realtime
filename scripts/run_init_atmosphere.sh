#!/bin/bash

cd ${ROOT_DIR}/MPAS-Model
ln -s ${ROOT_DIR}/tools/WPS-4.4/FILE* .
mpiexec -n 6 ./init_atmosphere_model
