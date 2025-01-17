"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
from time import sleep
import sys
import os
from setproctitle import setproctitle
from threading import Thread
from traceback import format_exc
from logging import getLogger
from signal import signal, SIGINT, SIGTERM, SIGHUP
from django.apps import apps as django_apps
from camai.c_settings import safe_import
from tools.l_sysinfo import system_info
print(system_info)

#from threading import enumerate

do_run = True
redis = None
stophealth = None
my_cleanup = None
restart_mode = 0
streams = {}
tf_workers = {}
trainers = {}
trainer_lists = {}

def restartcheck_thread():
  from streams.c_streams import c_stream
  from streams.models import stream
  from tf_workers.c_tfworkers import tf_worker
  from trainers.c_trainers import trainer
  global restart_mode
  while do_run:
    if (command := redis.get_shutdown_command()):
      redis.set_shutdown_command(0)
      if command == 1:
        restart_mode = 1
      elif command == 2:  
        restart_mode = 2
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
  global do_run
  redis.set('CAM-AI:KBInt', 1) #Signal for onf in views/consumers
  print ('Caught KeyboardInterrupt...')
  do_run = False
  sleep(5.0)
  stophealth()
  my_cleanup.stop()
  for i in streams:
    print('Closing stream #', i)
    streams[i].stop()
  for i in tf_workers:
    print('Closing tf_worker #', i)
    tf_workers[i].stop()
  for i in trainers:
    print('Closing trainer #', i)
    trainers[i].stop()  
  #print('*** restart_mode', restart_mode)  
  if restart_mode == 0:
    redis.set_watch_status(0) 
    #for thread in enumerate(): 
    #  print(thread)
    sys.exit(0)
  elif restart_mode == 1:
    redis.set_watch_status(0) 
    #for thread in enumerate(): 
    #  print(thread)
    os.system('sudo shutdown now')
    sys.exit(0)
  elif restart_mode == 2:
    redis.set_watch_status(2) 
    #for thread in enumerate(): 
    #  print(thread)
    os._exit(0)

signal(SIGINT, newexit)
signal(SIGTERM, newexit)
signal(SIGHUP, newexit)
    
def run():
  global do_run
  global redis
  global stophealth
  global my_cleanup
  global streams
  global tf_workers
  global trainers
  while not (app_status := django_apps.ready):
    sleep(1.0)
  from tools.c_logger import log_ini
  from tools.l_tools import djconf
  from tools.c_redis import myredis
  from camai.version import version as software_version
  print('***** Software-Version: ', software_version, '*****')
  old_version = djconf.getconfig('version', '0.0.0')
  djconf.setconfig('version', software_version)
  data_path = safe_import('data_path') 
  db_database = safe_import('db_database') 
  print('***** DataPath: ', data_path, '*****')
  djconf.setconfig('datapath', data_path)
  print('***** Database: ', db_database, '*****')
  from camai.db_ini import db_ini
  from camai.passwords import (
    smtp_account,
    smtp_password,
    smtp_server,
    smtp_port,
    smtp_email,
  )
  djconf.setconfig('smtp_account', smtp_account)
  djconf.setconfig('smtp_password', smtp_password)
  djconf.setconfig('smtp_server', smtp_server)
  djconf.setconfigint('smtp_port', smtp_port)
  djconf.setconfig('smtp_email', smtp_email)
  from tf_workers.models import worker
  from tf_workers.c_tfworkers import tf_worker
  from trainers.models import trainer as trainerdb
  from trainers.c_trainers import trainer
  from tools.health import stop as stophealth
  from tools.version_upgrade import version_upgrade
  from cleanup.c_cleanup import my_cleanup
  from streams.models import stream
  from streams.c_streams import c_stream
  
  restart_mode = 0
  redis = myredis()
  cleanup = None
  redis.set_start_trainer_busy(0)
  redis.set_start_worker_busy(0)
  redis.set_start_stream_busy(0)
  redis.set_shutdown_command(0)
  redis.set('CAM-AI:KBInt', 0)

  version_upgrade(old_version, software_version)

  logname = 'startup'
  logger = getLogger(logname)
  log_ini(logger, logname)
  try:
    for dbline in trainerdb.objects.filter(active=True):
      trainers[dbline.id] = trainer(dbline)
      trainers[dbline.id].run()
    for dbline in worker.objects.filter(active=True):
      tf_workers[dbline.id] = tf_worker(dbline.id)
      tf_workers[dbline.id].run()
    for dbline in stream.objects.filter(active=True):
      streams[dbline.id] = c_stream(dbline)
      streams[dbline.id].start()
    my_cleanup.run()  
    check_thread = Thread(target = restartcheck_thread, name='RestartCheckThread').start()
  except:
    logger.error('Error in process: ' + logname)
    logger.error(format_exc())
    
def launch():
  setproctitle('CAM-AI-Startup')
  Thread(target=run, name='StartupThreadThread').start()
