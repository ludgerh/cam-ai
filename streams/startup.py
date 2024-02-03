# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import sys
import os
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from time import sleep
from threading import Thread
from tools.l_tools import djconf
from tools.c_redis import myredis
from camai.version import version as software_version
print('***** Software-Version: ', software_version, '*****')
djconf.setconfig('version', software_version)
try:
  from camai.passwords import data_path
except  ImportError: # can be removed when everybody is up to date
  data_path = 'data/' 
try:  
  from camai.passwords import db_database
except  ImportError: # can be removed when everybody is up to date
  db_database = 'CAM-AI' 
print('***** DataPath: ', data_path, '*****')
djconf.setconfig('datapath', data_path)
print('***** Database: ', db_database, '*****')
from tf_workers.models import worker
from tf_workers.c_tfworkers import tf_workers, tf_worker
from trainers.models import model_type, trainer as trainerdb
from trainers.c_trainers import trainers, trainer
from tools.models import camurl
from tools.health import stop as stophealth
from .models import stream
from .c_streams import streams, c_stream

#from threading import enumerate
    
if not model_type.objects.filter(name='efficientnetv2-b0'):
  newtype = model_type(name='efficientnetv2-b0', x_in_default=224, y_in_default=224)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-b1'):
  newtype = model_type(name='efficientnetv2-b1', x_in_default=240, y_in_default=240)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-b2'):
  newtype = model_type(name='efficientnetv2-b2', x_in_default=260, y_in_default=260)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-b3'):
  newtype = model_type(name='efficientnetv2-b3', x_in_default=300, y_in_default=300)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-s'):
  newtype = model_type(name='efficientnetv2-s', x_in_default=384, y_in_default=384)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-m'):
  newtype = model_type(name='efficientnetv2-m', x_in_default=480, y_in_default=480)
  newtype.save()
if not model_type.objects.filter(name='efficientnetv2-l'):
  newtype = model_type(name='efficientnetv2-l', x_in_default=480, y_in_default=480)
  newtype.save()
    
if not  camurl.objects.filter(type='levelone FCS-4051'):
  newcam = camurl(type='levelone FCS-4051', 
    url='rtsp://{user}:{pass}@{address}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1')
  newcam.save()
if not  camurl.objects.filter(type='levelone FCS-5201'):
  newcam = camurl(type='levelone FCS-5201', 
    url='rtsp://{user}:{pass}@{address}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1')
  newcam.save()
if not  camurl.objects.filter(type='Reolink RLC-410W'):
  newcam = camurl(type='Reolink RLC-410W', 
    url='rtmp://{address}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}')
  newcam.save()
if not  camurl.objects.filter(type='Reolink E1 Zoom'):
  newcam = camurl(type='Reolink E1 Zoom', 
    url='rtmp://{address}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}')
  newcam.save()

restart_mode = 0
do_run = True
redis = myredis()
redis.set_start_trainer_busy(0)
redis.set_start_worker_busy(0)
redis.set_start_stream_busy(0)
redis.set_shutdown_command(0)
redis.set('KBInt', 0)

def restartcheck_thread():
  global restart_mode
  while do_run:
    if (command := redis.get_shutdown_command()):
      redis.set_shutdown_command(0)
      if command == 1:
        restart_mode = 1
      elif command == 2:  
        restart_mode = 2
      print('redis-command', restart_mode)
      os.kill(os.getpid(), SIGINT)
      return()
    if (item := redis.get_start_trainer_busy()):
      if (item in trainers) and trainers[item].do_run:
        trainers[item].stop()
      trainers[item] = trainer(item)
      trainers[item].run()
      redis.set_start_trainer_busy(0)
    if (item := redis.get_start_worker_busy()):
      if (item in tf_workers) and tf_workers[item].do_run:
        tf_workers[item].stop()
      tf_workers[item] = tf_worker(item)
      tf_workers[item].run()
      redis.set_start_worker_busy(0)
    if (item := redis.get_start_stream_busy()):
      dbline = stream.objects.get(id=item)
      if item in streams:
        streams[item].stop()
      streams[item] = c_stream(dbline)
      streams[item].start()
      redis.set_start_stream_busy(0)    
    sleep(10.0)

def newexit(*args):
  global restart_mode
  global do_run
  redis.set('KBInt', 1)
  print ('Caught KeyboardInterrupt...')
  do_run = False
  sleep(5.0)
  stophealth()
  for i in streams:
    print('Closing stream #', i)
    streams[i].stop()
  for i in tf_workers:
    print('Closing tf_worker #', i)
    tf_workers[i].stop()
  for i in trainers:
    print('Closing trainer #', i)
    trainers[i].stop()  
  if restart_mode in {0, 1}:
    redis.set_watch_status(0) 
    sys.exit(0)
  elif restart_mode == 2:
    redis.set_watch_status(2) 
    #for thread in enumerate(): 
    #  print(thread)
    os._exit(0)
    
def run():
  signal(SIGINT, newexit)
  signal(SIGTERM, newexit)
  signal(SIGHUP, newexit)

  setproctitle('CAM-AI-Startup')

  for dbline in trainerdb.objects.filter(active=True):
    trainers[dbline.id] = trainer(dbline.id)
    trainers[dbline.id].run()

  for dbline in worker.objects.filter(active=True):
    tf_workers[dbline.id] = tf_worker(dbline.id)
    tf_workers[dbline.id].run()
  
  for dbline in stream.objects.filter(active=True):
    streams[dbline.id] = c_stream(dbline)
    streams[dbline.id].start()
    
  check_thread = Thread(target = restartcheck_thread, name='RestartCheckThread').start()

