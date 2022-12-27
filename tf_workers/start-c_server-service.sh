#!/bin/bash
sleep 30s
exec  >> /home/cam_ai/cam-ai/data/logs/c_server.log 2>> /home/cam_ai/cam-ai/data/logs/c_server.err
cd /home/cam_ai/cam-ai
source env/bin/activate
python manage.py runserver 0.0.0.0:8888 --noreload
