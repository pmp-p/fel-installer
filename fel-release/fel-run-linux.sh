#!/bin/bash

clear > /tmp/h3droid_fel.log

python3 -u -B h3droid_fel.py $* 2> /tmp/h3droid_fel.log  || stty sane && stty sane
