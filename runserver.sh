#!/bin/bash 
# runserver.sh
# Further parameters are passed to cam-ai-server.py, e.g. nopip:
# ./runserver.sh pc nopip
cd ~/cam-ai
if [ "$1" = "raspi" ] ; then
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py "${@:2}" manage.py runserver 0.0.0.0:8888 --noreload
fi
if [ "$1" = "pc" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py "${@:2}" manage.py runserver 0.0.0.0:8888 --noreload
fi
if [ "$1" = "nvidia" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py nvidia "${@:2}" manage.py runserver 0.0.0.0:8888 --noreload
fi
