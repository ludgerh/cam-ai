#!/bin/bash 
cd cam-ai 
if [ "$1" = "raspi" ] ; then
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate tf
fi
if [ "$1" = "pc" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
fi
python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
