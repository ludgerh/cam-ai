#!/bin/bash 
cd cam-ai 
if [ "$1" = "venv" ] ; then
  source env/bin/activate 
fi
if [ "$1" = "conda" ] ; then
  source ~/miniconda3/etc/profile.d/conda.sh
  conda activate tf
fi
python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
