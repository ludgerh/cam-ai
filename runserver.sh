#!/bin/bash 
cd cam-ai 
if [ "$1" = "raspi" ] ; then
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate tf
  pip install --upgrade pip
  pip install -r requirements.raspi_13
fi
if [ "$1" = "pc" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  pip install --upgrade pip
  pip install -r requirements.pc_13
fi
if [ "$1" = "nvidia" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
  pip install --upgrade pip
  pip install -r requirements.nvidia_13
fi
python manage.py migrate
python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
