#!/bin/bash 
cd cam-ai 
if [ "$1" = "raspi" ] ; then
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate tf
  pip install -r requirements.raspi_12
fi
if [ "$1" = "pc" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  pip install -r requirements.pc_12
fi
if [ "$1" = "nvidia" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  pip install -r requirements.nvidia_12
fi
python manage.py migrate
python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
