#!/bin/bash 
cd cam-ai 
source env/bin/activate 
python cam-ai-server.py manage.py runserver 0.0.0.0:8000 --noreload
