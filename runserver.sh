#!/bin/bash 
if [ "$1" = "raspi" ] ; then
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
fi
if [ "$1" = "pc" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
fi
if [ "$1" = "nvidia" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  python cam-ai-server.py nvidia manage.py runserver 0.0.0.0:8000 --noreload
fi
