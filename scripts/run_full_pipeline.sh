#!/bin/bash

poetry run python run_mpas.py --domain synotpic25km
poetry run python plot_raw.py --domain synotpic25km
scp -r -i /home/dan/.ssh/co2.pem  /home/dan/Sourcecode/mpas-realtime/products/images/ ubuntu@34.206.111.92:snow-forecast-website/static/img/mpas/
