#!/bin/bash

DIR="$( cd "$( dirname "$0")" && pwd )" 
export QGIS_PREFIX_PATH=/usr/
python $DIR/src/roam/
